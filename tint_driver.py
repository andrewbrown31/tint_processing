import xarray as xr
from netCDF4 import num2date
import argparse
import numpy as np
import os
import glob
import datetime as dt
import zipfile

import pyart
from tint import Cell_tracks

"""
Tracking Parameter Guide
------------------------

FIELD_THRESH : units of 'field' attribute
    The threshold used for object detection. Detected objects are connnected
    pixels above this threshold.
ISO_THRESH : units of 'field' attribute
    Used in isolated cell classification. Isolated cells must not be connected
    to any other cell by contiguous pixels above this threshold.
ISO_SMOOTH : pixels
    Gaussian smoothing parameter in peak detection preprocessing. See
    single_max in tint.objects.
MIN_SIZE : square kilometers
    The minimum size threshold in pixels for an object to be detected.
SEARCH_MARGIN : meters
    The radius of the search box around the predicted object center.
FLOW_MARGIN : meters
    The margin size around the object extent on which to perform phase
    correlation.
MAX_DISPARITY : float
    Maximum allowable disparity value. Larger disparity values are sent to
    LARGE_NUM.
MAX_FLOW_MAG : meters per second
    Maximum allowable global shift magnitude. See get_global_shift in
    tint.phase_correlation.
MAX_SHIFT_DISP : meters per second
    Maximum magnitude of difference in meters per second for two shifts to be
    considered in agreement. See correct_shift in tint.matching.
GS_ALT : meters
    Altitude in meters at which to perform phase correlation for global shift
    calculation. See correct_shift in tint.matching.
"""

def decode_radar_times(f):
    return f.assign_coords({"time":num2date(f.time.values, f.time.units, calendar=f.time.calendar)})

def unpack_level1b(rid, times):
	#Unzip level1b data between times[0] and times[1], and save to scratch
	assert times[0].year == times[1].year, "Times range must be within calendar year"
	files = np.array(glob.glob("/g/data/rq0/admin/level_1b_v2/"+rid+"/grid/"+str(times[0].year)+"/*.zip"))
	if len(files) == 0:
		print("NO FILES FOUND FOR RID: "+rid+" AND TIMES "+times[0]+" "+times[-1])
	file_dates = np.array([dt.datetime.strptime(f.split("/")[9].split("_")[1], "%Y%m%d") for f in files])
	target_files = files[(file_dates >= times[0].replace(hour=0, minute=0)) & (file_dates <= times[1].replace(hour=0, minute=0))]
	extract_to = "/scratch/eg3/ab4502/tint/"
	for f in target_files:
		with zipfile.ZipFile(f, "r") as zip_ref:
			zip_ref.extractall(extract_to)

def grid_gen(target_files):
	for fn in target_files:
		yield pyart.io.read_grid(fn)

def track(rid, times, azi_shear, steiner, refl_name="corrected_reflectivity"):
    
    #Generate ouput file name based on initial and last time
    outname = rid+"_"+times[0].strftime("%Y%m%d")+"_"+times[-1].strftime("%Y%m%d")
        
    #Unpack gridded radar files. Create empty files based on missing files reported in Level 2
    unpack_level1b(rid, times)
    grid_files = np.sort(glob.glob("/scratch/eg3/ab4502/tint/"+rid+"*_grid.nc"))
    file_dates = np.array([dt.datetime.strptime(f.split("/")[5].split("_")[1] + f.split("/")[5].split("_")[2],\
                    "%Y%m%d%H%M%S") for f in grid_files])
    target_files = grid_files[(file_dates >= times[0]) & (file_dates <= times[1])]

    #Load in a format ready to send to TINT
    grids = grid_gen(target_files)

    #If steiner is True, load the level 2 steiner data with xarray
    if steiner:
        grid_files = []; i=0
        path = "/g/data/rq0/admin/level_2_v2/"+str(rid)+"/STEINER/"
        while times[0] + dt.timedelta(days=1*i) <= times[1]:
            t = (times[0] + dt.timedelta(days=1*i)).strftime("%Y%m%d")
            grid_path = path + str(rid)+"_"+t+"_steiner.nc"
            if os.path.isfile(grid_path):
                grid_files.append(grid_path)
            i=i+1
        steiner_grid = xr.open_mfdataset([f for f in grid_files], decode_times=False, preprocess=decode_radar_times).steiner.load()
    else:
        steiner_grid = False

    #Initialise TINT tracks and set tracking parameters
    tracks_obj = Cell_tracks(refl_name)
    tracks_obj.params["FIELD_THRESH"]=30
    tracks_obj.params["MIN_SIZE"]=15
    tracks_obj.params["MIN_VOL"]=30
    tracks_obj.params["MIN_HGT"]=2
    tracks_obj.params["MAX_DISPARITY"]=60
    tracks_obj.params["SEARCH_MARGIN"]=10000
    tracks_obj.params["SKIMAGE_PROPS"]=["eccentricity","major_axis_length","minor_axis_length","bbox"]
    tracks_obj.params["FIELD_DEPTH"]=5
    tracks_obj.params["LOCAL_MAX_DIST"]=4
    tracks_obj.params["AZI_SHEAR"]=azi_shear
    tracks_obj.params["STEINER"]=steiner
    tracks_obj.params["AZH1"]=2
    tracks_obj.params["AZH2"]=6
    
    #Perform TINT tracking
    tracks_obj.get_tracks(grids, "/g/data/eg3/ab4502/TINTobjects/"+outname+".h5", steiner_grid)
    tracks_obj.tracks.to_csv("/g/data/eg3/ab4502/TINTobjects/"+outname+".csv")    

    #Write options to file
    with open("/g/data/eg3/ab4502/TINTobjects/"+outname+".txt", "w") as f:
        print(tracks_obj.params,"\n",tracks_obj.grid_size, file=f)

    #Clean up
    _ = [os.remove(f) for f in target_files]

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('-rid', type=str, help='radar id')
	parser.add_argument('-t1', type=str, help='start date in YYYYMMDDHHMM format')
	parser.add_argument('-t2', type=str, help='end date in YYYYMMDDHHMM format')
	parser.add_argument('--azi_shear', type=str, help='Extract azimuthal shear?', default="True")
	parser.add_argument('--steiner', type=str, help='Calculate convective percent using level2 STEINER class. data?', default="True")
	args = parser.parse_args()

	if not ( (args.azi_shear=="True") | (args.azi_shear=="False") ):
		raise ValueError("--azi_shear must be True or False")
	if not ( (args.steiner=="True") | (args.steiner=="False") ):
		raise ValueError("--azi_shear must be True or False")

	track(args.rid, [dt.datetime.strptime(args.t1, "%Y%m%d%H%M"), dt.datetime.strptime(args.t2, "%Y%m%d%H%M")],\
		args.azi_shear=="True", args.steiner=="True")

