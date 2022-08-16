import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML, Image, display
import tempfile
import os
import shutil
import glob
import tqdm
from scipy.ndimage import gaussian_filter
from load_radar import load_radar
import datetime as dt
import zipfile

import pyart
from pymeso import llsd
from tint import Cell_tracks, animate
from tint.visualization import embed_mp4_as_gif

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

def unpack_level1b(rid, times):
	#Unzip level1b data between times[0] and times[1], and save to scratch
	assert times[0].year == times[1].year, "Times range must be within calendar year"
	files = np.array(glob.glob("/g/data/rq0/level_1b/"+rid+"/grid/"+str(times[0].year)+"/*.zip"))
	if len(files) == 0:
		print("NO FILES FOUND FOR RID: "+rid+" AND TIMES "+times[0].strftime("%Y%m%d %H:%M")+" "+times[-1].strftime("%Y%m%d %H:%M"))
	file_dates = np.array([dt.datetime.strptime(f.split("/")[8].split("_")[1], "%Y%m%d") for f in files])
	target_files = files[(file_dates >= times[0].replace(hour=0, minute=0)) & (file_dates <= times[1].replace(hour=0, minute=0))]
	extract_to = "/scratch/w40/ab4502/tint/"
	for f in target_files:
		with zipfile.ZipFile(f, "r") as zip_ref:
			zip_ref.extractall(extract_to)

def dealiase(radar, vel_name):
    #check to see if radar object has nyquist velocity. use Pyart to dealiase velocity
    try: 
        gatefilter = pyart.correct.GateFilter(radar)
        corr_vel   = pyart.correct.dealias_region_based(
            radar, vel_field=vel_name, keep_original=False, gatefilter = gatefilter)
        radar.add_field(vel_name, corr_vel, True)
    except:
        print("Unable to dealias velocity due to no Nyquist velocity found in radar object")

def date_seq(times,delta_type,delta):
    
    #Create a linear sequence of datetime objects, from times[0] to times[1], and 'delta' spacing of type 'delta_type' (e.g. 'hours')

    start_time = times[0]
    end_time = times[1]
    current_time = times[0]
    date_list = [current_time]
    while (current_time < end_time):
        if delta_type == "hours":
            current_time = current_time + dt.timedelta(hours = delta)
        date_list.append(current_time)
    return date_list

def track_case(rid, times, smooth=True, step=1, azi_shear=True, extra_points=False, animation=False, refl_name="corrected_reflectivity"):
    
    outname = rid+"_"+times[0].strftime("%Y%m%d")

    #Load gridded radar files in a format ready to send to TINT
    unpack_level1b(rid, times)
    grid_files = np.sort(glob.glob("/scratch/w40/ab4502/tint/"+rid+"*_grid.nc"))
    file_dates = np.array([dt.datetime.strptime(f.split("/")[5].split("_")[1] + f.split("/")[5].split("_")[2],\
                    "%Y%m%d%H%M%S") for f in grid_files])
    target_files = grid_files[(file_dates >= times[0]) & (file_dates <= times[1])]
    grids = (pyart.io.read_grid(fn) for fn in target_files)

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
    tracks_obj.params["STEINER"]=False
    tracks_obj.params["AZH1"]=2
    tracks_obj.params["AZH2"]=6
    tracks_obj.params["SEGMENTATION_METHOD"]="watershed"
    tracks_obj.params["WATERSHED_THRESH"]=[30]
    tracks_obj.params["WATERSHED_SMOOTHING"]=3
    tracks_obj.params["WATERSHED_EROSION"]=0
    tracks_obj.params["MIN_FIELD"]=30
    
    #Perform TINT tracking
    tracks_obj.get_tracks(grids, "/g/data/eg3/ab4502/TINTobjects/"+outname+".h5", None)
    tracks_obj.tracks.to_csv("/g/data/eg3/ab4502/TINTobjects/"+outname+".csv")    

    #Make animation from radar grids and TINT track output
    if animation:
       try:
          os.remove('/g/data/eg3/ab4502/figs/tint/'+outname+'.mp4')
       except:
          pass
       grids = (pyart.io.read_grid(fn) for fn in target_files)
       if rid == "40":
          tracks_obj.radar_info = {'radar_lon':149.5122, 'radar_lat':-35.6614}
       elif rid == "55":
          tracks_obj.radar_info = {'radar_lon':147.467, 'radar_lat':-35.167}
       elif rid == "50":
          tracks_obj.radar_info = {'radar_lon':152.539, 'radar_lat':-27.608}
       elif rid == "71":
          tracks_obj.radar_info = {'radar_lon':151.2094, 'radar_lat':-33.7008}
       elif rid == "66":
          tracks_obj.radar_info = {'radar_lon':153.24, 'radar_lat':-27.7178}
       elif rid == "8":
          tracks_obj.radar_info = {'radar_lon':152.5768, 'radar_lat':-25.9574}
       elif rid == "27":
          tracks_obj.radar_info = {'radar_lon':144.7555, 'radar_lat':-37.8553}
       elif rid == "2":
          tracks_obj.radar_info = {'radar_lon':144.7555, 'radar_lat':-37.8553}
       elif rid == "68":
          tracks_obj.radar_info = {'radar_lon':147.5755, 'radar_lat':-37.8876}
       elif rid == "38":
          tracks_obj.radar_info = {'radar_lon':146.2558, 'radar_lat':-26.4139}
       elif rid == "28":
          tracks_obj.radar_info = {'radar_lon':152.951, 'radar_lat':-29.622}
       elif rid == "4":
          tracks_obj.radar_info = {'radar_lon':152.0254, 'radar_lat':-32.7298}
       animate(tracks_obj, grids, "/g/data/eg3/ab4502/figs/tint/"+outname, tracers=True, extra_points=extra_points, alt=2500)

    #Clean up
    _ = [os.remove(f) for f in glob.glob("/scratch/eg3/ab4502/tint/"+rid+"*_grid.nc")]

if __name__ == "__main__":

    track_case("66", [dt.datetime(2011,1,10,17,0), dt.datetime(2011,1,11,10,0)], smooth=True, step=1, extra_points=[(-27.6297, 152.7111)], azi_shear=True, animation=True) 

    #Auto cases
    #df=pd.read_csv("/g/data/eg3/ab4502/figs/ExtremeWind/case_studies/case_study_list.csv")
    #for index, row in df[df.stn_name=="Melbourne"].iterrows():
        #track_case("2",
		#[pd.to_datetime(row.gust_time_utc)+dt.timedelta(hours=-0.5), pd.to_datetime(row.gust_time_utc)+dt.timedelta(hours=0.5)],
		#smooth=False, step=1, azi_shear=True, animation=False)

    #df=pd.read_csv("/g/data/eg3/ab4502/figs/ExtremeWind/case_studies/case_study_list.csv")
    #for index, row in df[df.stn_name=="Sydney"].iloc[0:1].iterrows():
    #    track_case("71",
#		[pd.to_datetime(row.gust_time_utc)+dt.timedelta(hours=-0.5), pd.to_datetime(row.gust_time_utc)+dt.timedelta(hours=0.5)],
#		smooth=False, step=1, azi_shear=True, animation=False)
