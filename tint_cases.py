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
	files = np.array(glob.glob("/g/data/rq0/admin/level_1b_v2/"+rid+"/grid/"+str(times[0].year)+"/*.zip"))
	if len(files) == 0:
		print("NO FILES FOUND FOR RID: "+rid+" AND TIMES "+times[0].strftime("%Y%m%d %H:%M")+" "+times[-1].strftime("%Y%m%d %H:%M"))
	file_dates = np.array([dt.datetime.strptime(f.split("/")[9].split("_")[1], "%Y%m%d") for f in files])
	target_files = files[(file_dates >= times[0].replace(hour=0, minute=0)) & (file_dates <= times[1].replace(hour=0, minute=0))]
	extract_to = "/scratch/eg3/ab4502/tint/"
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
    
    #Load radar data from rq0, save to disk
    #[load_radar(rid, date) for date in np.unique([dt.datetime(d.year, d.month, d.day) for d in date_seq(times,"hours",1)])]
    
    #Generate daily ouput file names
    #files=np.sort(glob.glob("/g/data/eg3/ab4502/radar/"+rid+"_*"))
    #datetimes = np.array([dt.datetime.strptime(files[i].split("/")[-1][3:18],"%Y%m%d_%H%M%S") for i in np.arange(len(files))])
    #files = files[(datetimes >= times[0]) & (datetimes<=times[1])]
    #datetimes = datetimes[(datetimes >= times[0]) & (datetimes<=times[1])]
    outname = rid+"_"+times[0].strftime("%Y%m%d")
        
    #For each radar file (now on disk), grid the data and save in scratch.
    #Also do azimuthal shear calculations if flagged
    #Also smooth the gridded reflectivity if flagged
    #get_ipython().system('rm /scratch/eg3/ab4502/tint/*.nc')
    #cnt = 0
    #for f in tqdm.tqdm(files[0:-1:step]):
    #    radar = pyart.aux_io.read_odim_h5(f)
    #    if azi_shear:
    #            dealiase(radar, "velocity")
    #            az_shear_meta = llsd.main(radar,'reflectivity','velocity')
    #            radar.add_field('azi_shear', az_shear_meta, replace_existing=True)
    #    grid = pyart.map.grid_from_radars(radar,(41,121,121),((0,20e3),(-150e3,150e3),(-150e3,150e3)), weighting_function="Barnes2", min_radius=2500.)
        #grid = pyart.map.grid_from_radars(radar,(41,201,201),((0,20e3),(-250e3,250e3),(-250e3,250e3)), weighting_function="Barnes2", min_radius=2500.)        
    #    if smooth:
    #            grid.fields["reflectivity"]["data"] = np.stack([gaussian_filter(grid.fields["reflectivity"]["data"][i], 2) for i in np.arange(41)])
    #    grid.time["data"] = float(grid.time["data"])
    #    pyart.io.write_grid("/scratch/eg3/ab4502/tint/"+str(cnt).zfill(3)+"_grid.nc", grid)
    #    pyart.io.write_cfradial("/scratch/eg3/ab4502/tint/"+str(cnt).zfill(3)+"_radar.nc", radar)
    #    cnt=cnt+1

    #Re-load gridded radar files, as well as raw radar files, in a format ready to send to TINT
    unpack_level1b(rid, times)
    grid_files = np.sort(glob.glob("/scratch/eg3/ab4502/tint/"+rid+"*_grid.nc"))
    file_dates = np.array([dt.datetime.strptime(f.split("/")[5].split("_")[1] + f.split("/")[5].split("_")[2],\
                    "%Y%m%d%H%M%S") for f in grid_files])
    target_files = grid_files[(file_dates >= times[0]) & (file_dates <= times[1])]
    grids = (pyart.io.read_grid(fn) for fn in target_files)
    #radar_files = np.sort(glob.glob("/scratch/eg3/ab4502/tint/*radar.nc"))
    #radars = (pyart.io.read_cfradial(fn) for fn in radar_files)

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
    tracks_obj.params["AZH1"]=2
    tracks_obj.params["AZH2"]=6
    
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
       elif rid == "50":
          tracks_obj.radar_info = {'radar_lon':152.539, 'radar_lat':-27.608}
       elif rid == "71":
          tracks_obj.radar_info = {'radar_lon':151.2094, 'radar_lat':-33.7008}
       elif rid == "66":
          tracks_obj.radar_info = {'radar_lon':153.24, 'radar_lat':-27.7178}
       elif rid == "2":
          tracks_obj.radar_info = {'radar_lon':144.7555, 'radar_lat':-37.8553}
       animate(tracks_obj, grids, "/g/data/eg3/ab4502/figs/tint/"+outname, tracers=True, extra_points=extra_points)

    #Clean up
    _ = [os.remove(f) for f in glob.glob("/scratch/eg3/ab4502/tint/"+rid+"*_grid.nc")]

if __name__ == "__main__":
    
    #Vic
    #Waurn ponds
    #track_case("02", [dt.datetime(2020,5,19,12), dt.datetime(2020,5,19,18)], smooth=True, step=2, extra_points=[(-37.5127, 143.7911)])
    #Cressy
    #track_case("2", [dt.datetime(2020,1,31,0), dt.datetime(2020,1,31,22,0)], smooth=False, step=1, extra_points=[(-37.5976, 149.7289), (-37.6654, 144.8322), (-37.9483, 144.9269), (-37.9075, 144.1303), (-37.5127, 143.7911), (-37.7067, 142.9378), (-38.2332, 143.7924)], azi_shear=True, animation=False)
    #Melb airport max gust (2015)
    #track_case("02", [dt.datetime(2015,2,28,6), dt.datetime(2015,2,28,12)], smooth=True, step=2, extra_points=[(-38.1480, 145.1152), (-37.8565, 144.7565), (-37.6654, 144.8322)])
    #From Stacey's paper
    #track_case("02", [dt.datetime(2011,2,4,9,0), dt.datetime(2011,2,4,9,30)], smooth=True, step=2)
    #Melb white christmas supercell
    #track_case("02", [dt.datetime(2011,12,25,6), dt.datetime(2011,12,25,12)], smooth=True, step=2, extra_points=[(-37.2091, 145.8423), (-37.6654, 144.8322)], azi_shear=True, animation=False)
    #Melb 2016 Jan squall line
    #track_case("02", [dt.datetime(2016,1,13,3), dt.datetime(2016,1,13,9)], smooth=True, step=2, extra_points=[(-37.0222, 141.2657), (-37.1017, 147.6008), (-37.8640, 144.9639), (-38.0288, 144.4783)]) 
    #Melb Aug 2020 squall line
    #track_case("02", [dt.datetime(2020,8,27,6), dt.datetime(2020,8,27,9)], smooth=True, step=2, extra_points=[(-38.5647, 146.7479), (-38.8051, 146.1936), (-38.1016, 147.1398), (-38.0288, 144.4783), (-38.2332, 143.7924)])     
    #Yarrawonga bow echo
    #track_case("02", [dt.datetime(2011,9,28,6), dt.datetime(2011,9,28,12)], smooth=True, step=2, extra_points=[(-36.0690, 146.9509)])     
    #track_case("49", [dt.datetime(2011,9,28,6), dt.datetime(2011,9,28,12)], smooth=True, step=2, extra_points=[(-36.0690, 146.9509)])  
    #Gippsland/Dandeonong cut-off low
    #track_case("02", [dt.datetime(2021,6,9,11,30), dt.datetime(2021,6,9,12,30)], smooth=False, step=1, azi_shear=False, extra_points=[(-36.9381, 145.0539)])     

    #NSW
    #Kurnell
    #track_case("71", [dt.datetime(2015,12,15,22,0), dt.datetime(2015,12,16,1)], smooth=True, step=2)
    #track_case("71", [dt.datetime(2015,12,15,23,0), dt.datetime(2015,12,15,23,20)], smooth=True, step=2)
    track_case("71", [dt.datetime(2016,1,14,4,0), dt.datetime(2016,1,14,5,0)], smooth=True, step=1, animation=True, extra_points=[(-33.9465, 151.1731)], azi_shear=True)
    #Boorowa outage NSW
    #track_case("71", [dt.datetime(2020,12,1,3), dt.datetime(2020,12,1,9)], smooth=True, step=2, extra_points=[(-33.8382, 148.6540), (-34.2493, 148.2475)])
    #track_case("40", [dt.datetime(2020,12,1,4), dt.datetime(2020,12,1,5)], smooth=True, step=1, extra_points=[(-34.356940, 148.738652)],animation=True)           
    #33.4 m/s SCW gust Sydney
    #track_case("71", [dt.datetime(2016,1,14,3), dt.datetime(2016,1,14,9)], smooth=True, step=2, extra_points=[(-33.9465, 151.1731)])           

    #QLD
    #Double point island gust (16 December 2006) from Gympie radar
    #track_case("08", [dt.datetime(2006,12,16,6), dt.datetime(2006,12,16,9)], smooth=True, step=1, azi_shear=False, extra_points=[(-25.9319, 153.1906)])
    #Double point island gust from Brisbane radar
    #track_case("43", [dt.datetime(2006,12,16,6), dt.datetime(2006,12,16,9)], smooth=True, step=1)    
    #38.6 m/s SCW gust for Oakey (strongest gust in 202 events from Brown and Dowdy 2021)
    #track_case("66", [dt.datetime(2011,10,7,15), dt.datetime(2011,10,7,23)], smooth=True, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=True, animation=True)        
    #The gap
    #track_case("66", [dt.datetime(2008,11,16,3), dt.datetime(2008,11,16,9)], smooth=True, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=True, animation=True)        

    #Test cases (null)
    #track_case("50", [dt.datetime(2006,1,1,0), dt.datetime(2006,1,1,3,0)], smooth=False, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=False, animation=False)        
    #track_case("2", [dt.datetime(2020,1,4,11,30), dt.datetime(2020,1,4,12,30)], smooth=False, step=1, extra_points=[(-37.5976, 149.7289), (-37.6654, 144.8322), (-37.9483, 144.9269), (-37.9075, 144.1303), (-37.5127, 143.7911), (-37.7067, 142.9378), (-38.2332, 143.7924)], azi_shear=True, animation=True)
