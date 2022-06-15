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
    tracks_obj.params["MIN_HGT"]=0
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
    tracks_obj.params["WATERSHED_THRESH"]=[30,40]
    tracks_obj.params["WATERSHED_SMOOTHING"]=3
    tracks_obj.params["WATERSHED_EROSION"]=0
    
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

    #TOBAC TESTING
    #track_case("66", [dt.datetime(2013,11,23,9,0), dt.datetime(2013,11,23,10,0)], smooth=True, step=1, extra_points=[(-27.6297, 152.7111)], azi_shear=True, animation=False) 
    #track_case("2", [dt.datetime(2010,3,6,2,30), dt.datetime(2010,3,6,3,30)], smooth=True, step=2, extra_points=[(-37.2091, 145.8423), (-37.6654, 144.8322)], azi_shear=True, animation=False)
    #track_case("2", [dt.datetime(2020,1,31,3), dt.datetime(2020,1,31,12,0)], smooth=False, step=1, extra_points=[(-37.5976, 149.7289), (-37.6654, 144.8322), (-37.9483, 144.9269), (-37.9075, 144.1303), (-37.5127, 143.7911), (-37.7067, 142.9378), (-38.2332, 143.7924)], azi_shear=True, animation=True)
    #track_case("2", [dt.datetime(2012,2,26,8,30), dt.datetime(2012,2,26,9,30)], smooth=True, step=2, extra_points=[(-37.2091, 145.8423), (-37.6654, 144.8322)], azi_shear=True, animation=False)
    #track_case("2", [dt.datetime(2015,2,28,9), dt.datetime(2015,2,28,10)], smooth=True, step=2, extra_points=[(-38.1480, 145.1152), (-37.8565, 144.7565), (-37.6654, 144.8322)], animation=False, azi_shear=True)
    #track_case("27", [dt.datetime(2007,10,27,8,30), dt.datetime(2007,10,27,9,30)], smooth=True, step=1, azi_shear=False, extra_points=[(-31.1558, 136.8054)], animation=False)
    
    #Vic
    #Waurn ponds
    #track_case("02", [dt.datetime(2020,5,19,12), dt.datetime(2020,5,19,18)], smooth=True, step=2, extra_points=[(-37.5127, 143.7911)])
    #Cressy
    #Melb airport max gust (2015)
    #From Stacey's paper
    #track_case("02", [dt.datetime(2011,2,4,9,0), dt.datetime(2011,2,4,9,30)], smooth=True, step=2)
    #Melb white christmas supercell
    #track_case("2", [dt.datetime(2011,12,25,6,35), dt.datetime(2011,12,25,6,50)], smooth=True, step=2, extra_points=[(-37.2091, 145.8423), (-37.6654, 144.8322)], azi_shear=True, animation=False)
    #Melb 2016 Jan squall line
    #track_case("02", [dt.datetime(2016,1,13,3), dt.datetime(2016,1,13,9)], smooth=True, step=2, extra_points=[(-37.0222, 141.2657), (-37.1017, 147.6008), (-37.8640, 144.9639), (-38.0288, 144.4783)]) 
    #Melb Aug 2020 squall line
    #track_case("2", [dt.datetime(2020,8,27,6), dt.datetime(2020,8,27,8,20)], smooth=True, step=2, extra_points=[(-38.5647, 146.7479), (-38.8051, 146.1936), (-38.1016, 147.1398), (-38.0288, 144.4783), (-38.2332, 143.7924)],animation=True)         
    #Yarrawonga bow echo
    #track_case("02", [dt.datetime(2011,9,28,6), dt.datetime(2011,9,28,12)], smooth=True, step=2, extra_points=[(-36.0690, 146.9509)])     
    #track_case("49", [dt.datetime(2011,9,28,6), dt.datetime(2011,9,28,12)], smooth=True, step=2, extra_points=[(-36.0690, 146.9509)])  
    #Gippsland/Dandeonong cut-off low
    #track_case("02", [dt.datetime(2021,6,9,11,30), dt.datetime(2021,6,9,12,30)], smooth=False, step=1, azi_shear=False, extra_points=[(-36.9381, 145.0539)])     
    #2010 SCW event
    #AUS400
    #track_case("68", [dt.datetime(2017,3,27,0), dt.datetime(2017,3,27,6)], smooth=False, step=1, extra_points=[(-38.8051, 146.1936),(-38.5647, 146.7479),(-38.2094, 146.4746)],\
	    #azi_shear=False, animation=True)
    #MELB 2021
    #track_case("2", [dt.datetime(2012,2,26,8,30), dt.datetime(2012,2,26,9,30)], smooth=True, step=2, extra_points=[(-37.6654, 144.8322)], azi_shear=True, animation=True)
    track_case("2", [dt.datetime(2009,4,26,0,0), dt.datetime(2009,4,26,3,0)], smooth=True, step=1, extra_points=[(-37.6654, 144.8322)], azi_shear=True, animation=True)
    

    #NSW
    #Kurnell
    #track_case("71", [dt.datetime(2015,12,16,1,30), dt.datetime(2015,12,16,2,30)], smooth=False, step=1, extra_points=[(-33.9465, 151.1731)],animation=True,azi_shear=True)
    #Boorowa outage NSW
    #track_case("71", [dt.datetime(2020,12,1,3), dt.datetime(2020,12,1,9)], smooth=True, step=2, extra_points=[(-33.8382, 148.6540), (-34.2493, 148.2475)])
    #track_case("40", [dt.datetime(2020,12,1,4), dt.datetime(2020,12,1,5)], smooth=True, step=1, extra_points=[(-34.356940, 148.738652)],animation=True)           
    #Sydneys
    #track_case("71", [dt.datetime(2016,1,14,3), dt.datetime(2016,1,14,9)], smooth=True, step=2, extra_points=[(-33.9465, 151.1731)])           
    #track_case("71", [dt.datetime(2014,10,14,11), dt.datetime(2014,10,14,12)], smooth=True, step=2, extra_points=[(-33.9465, 151.1731)], animation=True)           
    #track_case("71", [dt.datetime(2016,6,4,3), dt.datetime(2016,6,4,4)], smooth=True, step=2, extra_points=[(-33.9465, 151.1731)], animation=True)           
    #track_case("71", [dt.datetime(2014,6,28,6), dt.datetime(2014,6,28,7)], smooth=True, step=2, extra_points=[(-33.9465, 151.1731)], animation=True)           
    #Wagga
    #track_case("55", [dt.datetime(2009,1,20,4), dt.datetime(2009,1,20,7)], smooth=True, step=2, extra_points=[(-35.1583, 147.4575)],animation=True,azi_shear=False)           
    #track_case("55", [dt.datetime(2017,3,27,6,30), dt.datetime(2017,3,27,7,30)], smooth=True, step=2, extra_points=[(-35.1583, 147.4575)],animation=True,azi_shear=True)
    #Coffs
    #track_case("28", [dt.datetime(2011,3,1,8,0), dt.datetime(2011,3,1,10,0)], smooth=True, step=2, extra_points=[(-30.3107, 153.1187)],animation=True,azi_shear=False)
    #track_case("28", [dt.datetime(2012,2,12,9,30), dt.datetime(2012,2,12,10,30)], smooth=True, step=2, extra_points=[(-30.3107, 153.1187)],animation=True,azi_shear=False)
    #Newcastle (Williamtown)
    #track_case("4", [dt.datetime(2015,4,20,23), dt.datetime(2015,4,21,0,59)], smooth=True, step=2, extra_points=[(-32.7939, 151.8364)],animation=False,azi_shear=True)           

    #QLD
    #Double point island gust (16 December 2006) from Gympie radar
    #track_case("8", [dt.datetime(2006,12,16,0), dt.datetime(2006,12,16,9)], smooth=True, step=1, azi_shear=False, extra_points=[(-25.9319, 153.1906)], animation=True)
    #Double point island gust from Brisbane radar
    #track_case("43", [dt.datetime(2006,12,16,6), dt.datetime(2006,12,16,9)], smooth=True, step=1)    
    #38.6 m/s SCW gust for Oakey (strongest gust in 202 events from Brown and Dowdy 2021)
    #track_case("50", [dt.datetime(2011,10,7,19), dt.datetime(2011,10,7,20)], smooth=True, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=False, animation=True)        
    #OAKEYs
    #track_case("50", [dt.datetime(2013,10,18,4), dt.datetime(2013,10,18,5)], smooth=True, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=False, animation=True)        
    #track_case("50", [dt.datetime(2018,2,13,6,30), dt.datetime(2018,2,13,7,30)], smooth=True, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=False, animation=True)        
    #track_case("50", [dt.datetime(2014,9,25,4), dt.datetime(2014,9,25,5)], smooth=True, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=False, animation=True)        
    #The gap
    #track_case("66", [dt.datetime(2008,11,16,3), dt.datetime(2008,11,16,9)], smooth=True, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=True, animation=True)        
    #Archerfield
    #track_case("66", [dt.datetime(2014,11,27,6), dt.datetime(2014,11,27,7)], smooth=True, step=1, extra_points=[(-27.5716, 153.0071)], azi_shear=True, animation=True)        
    #Amberly
    #track_case("66", [dt.datetime(2016,12,18,4), dt.datetime(2016,12,18,5)], smooth=True, step=1, extra_points=[(-27.6297, 152.7111)], azi_shear=True, animation=True)        
    #track_case("66", [dt.datetime(2011,1,18,4,30), dt.datetime(2011,1,18,5,30)], smooth=True, step=1, extra_points=[(-27.6297, 152.7111)], azi_shear=True, animation=True) 
    #Charleville
    #track_case("38", [dt.datetime(2005,1,22,5), dt.datetime(2005,1,22,6)], smooth=True, step=1, extra_points=[(-26.4139, 146.2558)], azi_shear=False, animation=True) 

    #SA
    #Woomera
    #track_case("27", [dt.datetime(2010,12,7,8), dt.datetime(2010,12,7,11)], smooth=True, step=1, azi_shear=False, extra_points=[(-31.1558, 136.8054)], animation=True)

    #Null cases
    #track_case("2", [dt.datetime(2020,1,3,0), dt.datetime(2020,1,4,0,0)], smooth=False, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=False, animation=True)        
    #track_case("66", [dt.datetime(2013,5,10,22), dt.datetime(2013,5,11,0,0)], smooth=False, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=False, animation=True)        
    #track_case("50", [dt.datetime(2006,1,1,0), dt.datetime(2006,1,1,12,0)], smooth=False, step=1, extra_points=[(-27.4034, 151.7413)], azi_shear=False, animation=True)        
    #track_case("2", [dt.datetime(2020,1,4,11,30), dt.datetime(2020,1,4,12,30)], smooth=False, step=1, extra_points=[(-37.5976, 149.7289), (-37.6654, 144.8322), (-37.9483, 144.9269), (-37.9075, 144.1303), (-37.5127, 143.7911), (-37.7067, 142.9378), (-38.2332, 143.7924)], azi_shear=True, animation=True)

    #Auto cases
    #events = pd.read_pickle("/g/data/eg3/ab4502/ExtremeWind/obs/aws/convective_wind_gust_aus_2005_2018.pkl")
    #for t in events[(events["wind_gust"] >= 25) & (events["stn_name"]=="Melbourne") & (events["tc_affected"]==0) & (events["lightning"]>=2)].sort_values("wind_gust",ascending=False).iloc[0:9].gust_time_utc.values:
        #print("\nMELBOURNE; "+str(t))
        #t = pd.to_datetime(t)
        #try:
        #   track_case("2", [t-dt.timedelta(hours=0.5), t+dt.timedelta(hours=0.5)], smooth=False, step=1, extra_points=[np.unique(events[events.stn_name=="Melbourne"][["lat","lon"]]).squeeze()], azi_shear=True, animation=True) 
        #except:
        #   track_case("2", [t-dt.timedelta(hours=0.5), t+dt.timedelta(hours=0.5)], smooth=False, step=1, extra_points=[np.unique(events[events.stn_name=="Melbourne"][["lat","lon"]]).squeeze()], azi_shear=False, animation=True) 
         #  print("\nINFO: NO AZI SHEAR")
    #for t in events[(events["wind_gust"] >= 25) & (events["stn_name"]=="Sydney") & (events["tc_affected"]==0) & (events["lightning"]>=2) & (events["gust_time_utc"]>=dt.datetime(2009,5,17)) & (events["gust_time_utc"] != dt.datetime(2013,10,29,3,8,0)) & (events["gust_time_utc"] != dt.datetime(2014,6,28,6,8,0))].sort_values("wind_gust",ascending=False).iloc[0:9].gust_time_utc.values:
    #    print("\nSYDNEY; "+str(t))
    #    t = pd.to_datetime(t)
    #    try:
    #       track_case("71", [t-dt.timedelta(hours=0.5), t+dt.timedelta(hours=0.5)], smooth=False, step=1, extra_points=[np.unique(events[events.stn_name=="Sydney"][["lat","lon"]]).squeeze()], azi_shear=True, animation=True) 
    #    except:
    #       track_case("71", [t-dt.timedelta(hours=0.5), t+dt.timedelta(hours=0.5)], smooth=False, step=1, extra_points=[np.unique(events[events.stn_name=="Sydney"][["lat","lon"]]).squeeze()], azi_shear=False, animation=True) 
    #       print("\nINFO: NO AZI SHEAR")
    #for t in events[(events["wind_gust"] >= 25) & (events["stn_name"]=="Amberley") & (events["tc_affected"]==0) & (events["lightning"]>=2)].sort_values("wind_gust",ascending=False).iloc[0:4].gust_time_utc.values:
    #    print("\nAMBERLEY; "+str(t))
    #    t = pd.to_datetime(t)
    #    try:
    #       track_case("66", [t-dt.timedelta(hours=0.5), t+dt.timedelta(hours=0.5)], smooth=False, step=1, extra_points=[np.unique(events[events.stn_name=="Amberley"][["lat","lon"]]).squeeze()], azi_shear=True, animation=True) 
    #    except:
    #       track_case("66", [t-dt.timedelta(hours=0.5), t+dt.timedelta(hours=0.5)], smooth=False, step=1, extra_points=[np.unique(events[events.stn_name=="Amberley"][["lat","lon"]]).squeeze()], azi_shear=True, animation=True) 
    #       print("\nINFO: NO AZI SHEAR")
    #for t in events[(events["wind_gust"] >= 25) & (events["stn_name"]=="Oakey") & (events["tc_affected"]==0) & (events["lightning"]>=2)].sort_values("wind_gust",ascending=False).iloc[0:5].gust_time_utc.values:
    #    print("\nOAKEY; "+str(t))
    #    t = pd.to_datetime(t)
    #    track_case("50", [t-dt.timedelta(hours=0.5), t+dt.timedelta(hours=0.5)], smooth=False, step=1, extra_points=[np.unique(events[events.stn_name=="Oakey"][["lat","lon"]]).squeeze()], azi_shear=False, animation=True) 
	    
    #for t in events[(events["wind_gust"] >= 25) & (events["stn_name"]=="Woomera") & (events["tc_affected"]==0) & (events["lightning"]>=2)].sort_values("wind_gust",ascending=False).iloc[0:9].gust_time_utc.values:
        #print("\nWOOMERA; "+str(t))
        #t = pd.to_datetime(t)
        #track_case("27", [t-dt.timedelta(hours=0.5), t+dt.timedelta(hours=0.5)], smooth=False, step=1, extra_points=[np.unique(events[events.stn_name=="Woomera"][["lat","lon"]]).squeeze()], animation=True, azi_shear=False) 
