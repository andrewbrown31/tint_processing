import pandas as pd
import numpy as np
import datetime as dt
import os
from tint_driver import track
from post_process_tracks import post_process_tracks

def load_scw_events():
    
	#Load the Brown and Dowdy (2021, JSHESS) measured SCW events at Melbourne, Sydney, Brisbane (Oakey+Amberley) and Woomera

	df_auto = pd.DataFrame()
	cols = ["gust_time_utc","lat","lon","stn_name","wind_gust"]
	events = pd.read_pickle("/g/data/eg3/ab4502/ExtremeWind/obs/aws/convective_wind_gust_aus_2005_2018.pkl")
	for loc in ["Melbourne","Sydney","Amberley","Oakey","Woomera"]:
	    cond = (events["wind_gust"] >= 25) & (events["stn_name"]==loc) & (events["lightning"]>=2)
	    loc_events = events[cond].sort_values("wind_gust",ascending=False)[cols]
	    df_auto = pd.concat([df_auto,loc_events.set_index("gust_time_utc")], axis=0)

	df_auto.loc[df_auto["stn_name"]=="Melbourne","rid"] = "2"    
	df_auto.loc[df_auto["stn_name"]=="Sydney","rid"] = "71"
	df_auto.loc[df_auto["stn_name"]=="Amberley","rid"] = "66"
	df_auto.loc[df_auto["stn_name"]=="Oakey","rid"] = "50"
	df_auto.loc[df_auto["stn_name"]=="Woomera","rid"] = "27"

	df_auto.loc[df_auto["stn_name"]=="Melbourne","stn_id"] = "086282"    
	df_auto.loc[df_auto["stn_name"]=="Sydney","stn_id"] = "066037"    
	df_auto.loc[df_auto["stn_name"]=="Amberley","stn_id"] = "040004"    
	df_auto.loc[df_auto["stn_name"]=="Oakey","stn_id"] = "041359"    
	df_auto.loc[df_auto["stn_name"]=="Woomera","stn_id"] = "016001"    

	df_auto.loc[df_auto["stn_name"]=="Melbourne","state"] = "vic"    
	df_auto.loc[df_auto["stn_name"]=="Sydney","state"] = "nsw"    
	df_auto.loc[df_auto["stn_name"]=="Amberley","state"] = "qld"    
	df_auto.loc[df_auto["stn_name"]=="Oakey","state"] = "qld"    
	df_auto.loc[df_auto["stn_name"]=="Woomera","state"] = "sa"    

	return df_auto

def check_steiner(rid, times):

	t1_exist = os.path.isfile("/g/data/rq0/level_2/"+rid+"/STEINER/"+rid+"_"+times[0].strftime("%Y%m%d")+"_steiner.nc")
	t2_exist = os.path.isfile("/g/data/rq0/level_2/"+rid+"/STEINER/"+rid+"_"+times[1].strftime("%Y%m%d")+"_steiner.nc")
	if t1_exist & t2_exist:
		return True
	else:
		return False

def check_level1b(rid, times):
	t1_exist = os.path.isfile("/g/data/rq0/level_1b/"+rid+"/grid/"+times[0].strftime("%Y")+"/"+rid+"_"+times[0].strftime("%Y%m%d")+"_grid.zip")
	t2_exist = os.path.isfile("/g/data/rq0/level_1b/"+rid+"/grid/"+times[1].strftime("%Y")+"/"+rid+"_"+times[1].strftime("%Y%m%d")+"_grid.zip")
	if t1_exist & t2_exist:
		return True
	else:
		return False

def get_storm_id(fid,time):

	if os.path.isfile("/g/data/eg3/ab4502/TINTobjects/"+fid+"_aws.csv"):
		storm_df = pd.read_csv("/g/data/eg3/ab4502/TINTobjects/"+fid+"_aws.csv")
		storm_df = storm_df.set_index(pd.DatetimeIndex(storm_df["dt_utc"]))
		#Sneakily reach for the previous one-min observation, if the daily max gust isn't within the one-min data. This is...
		# the case for Oakey, where one observation seems to be missing every 20 minutes.
		storm_df = storm_df.resample("1min").asfreq().fillna(method="ffill",limit=1)
		if time in storm_df.index:
			return storm_df.loc[time][["scan","in10km","uid10"]].values
		else:
		#This is only true if a daily radar file exists, but theres missing sub-daily scans
			return [np.nan, np.nan, np.nan]
	else:
		return [np.nan, np.nan, np.nan]

if __name__ == "__main__":

	df = load_scw_events()
	uid_list = []
	scan_list = []
	in10km_list = []
	
	for index, row in df.iterrows():
	    times = [index+dt.timedelta(hours=-12),pd.to_datetime(index)+dt.timedelta(hours=12)]
	    fid = row.rid + "_" + times[0].strftime("%Y%m%d") + "_" + times[1].strftime("%Y%m%d")

	    if check_level1b(row.rid, times):
		    track(row.rid, times, True, check_steiner(row.rid, times))
		    post_process_tracks(fid, row.state, [int(row.stn_id)], "True", 10, False, None, None, 100)
	    else:
		    print("NO LEVEL1B DATA FOR "+times[0].strftime("%Y%m%d")+" RID: "+row.rid)

	    scan, in10km, uid10 = get_storm_id(fid, index)
	    scan_list.append(scan)
	    in10km_list.append(in10km)
	    uid_list.append(uid10)

	df["uid"] = uid_list
	df["scan"] = scan_list
	df["in10km"] = in10km_list
	df.to_csv("/g/data/eg3/ab4502/figs/ExtremeWind/case_studies/potential_cases.csv")
