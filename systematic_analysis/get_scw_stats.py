import argparse
import pandas as pd
import numpy as np
import glob
import datetime as dt
import tqdm
import os

def last_day_of_month(any_day):
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = any_day.replace(day=28) + dt.timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return next_month - dt.timedelta(days=next_month.day)    

def load_scws(rid,year,month):
    
    #Load the merged AWS, ERA5, TINT dataset. Define SCW events and keep these only. Currently: One minute max 3-sec gusts over 25 m/s, with a radar object within 
    #   10 km, and a WGR(4-hr) greater than 1.5. Get unique UIDs associated with all one-minute
    #   SCW instances. Compare to all other UIDs. Aggregate UIDs over storm duration (mean).
    
    #Load the joint AWS-ERA5-TINT dataframe, and create a rolling 4 hour mean gust column (for calculating WGR)
    d1 = dt.datetime(year,month,1)
    d2 = last_day_of_month(d1)
    temp_df = pd.read_pickle("/g/data/eg3/ab4502/ExtremeWind/points/era5_aws_tint_"+rid+"_"+d1.strftime("%Y%m%d")+"_"+d2.strftime("%Y%m%d")+"_max.pkl")
    temp_df["dt_utc"] = pd.DatetimeIndex(temp_df.dt_utc)
    temp_df = temp_df.sort_values("dt_utc")
    #rolling = temp_df[["gust","stn_id","dt_utc"]].groupby("stn_id").rolling("4H",center=True,on="dt_utc",closed="both").mean()
    rolling4 = temp_df[["gust","stn_id","dt_utc"]].set_index("dt_utc").groupby("stn_id").rolling("4H",center=True,closed="both",min_periods=60).mean()
    rolling2b = temp_df[["gust","stn_id","dt_utc"]].set_index("dt_utc").groupby("stn_id").rolling("2H",center=False,closed="both",min_periods=30).mean()
    rolling2a = temp_df[["gust","stn_id","dt_utc"]].set_index("dt_utc").shift(freq="-2H").groupby("stn_id").rolling("2H",center=False,closed="both",min_periods=30).mean()
    rolling = pd.concat([rolling4.rename(columns={"gust":"rolling4"}),rolling2a.rename(columns={"gust":"rolling2a"}),rolling2b.rename(columns={"gust":"rolling2b"})],axis=1)
    temp_df = pd.merge(temp_df,rolling,on=["stn_id","dt_utc"])
    temp_df["wgr_4"] = temp_df["gust"] / temp_df["rolling4"]
    temp_df["wgr_2a"] = temp_df["gust"] / temp_df["rolling2a"]
    temp_df["wgr_2b"] = temp_df["gust"] / temp_df["rolling2b"]
    temp_df = temp_df.dropna(subset=["gust"])
    
    #Get all SCW events as a separate dataframe. Options for how to define "separate" events:
    #   domain = for each gust, look in the next hour over the whole radar domain. if there is a stronger gust at any station,
    #              then discard the current gust. Else, discard the other gusts. Move on to the next gust.
    #	era5_grid = events which occur more than one hour apart or on different neighbouring ERA5 grid points
    #	stns = events which occur more than one hour apart or at different stations
    #Also record the number of stations that measured a SCW event for each 1) hourly inverval and 2) storm ID
    #temp_df["hour_group"] = 0
    scws_envs = temp_df.query("(gust>=25) & (in10km ==1) & (wgr_4 >= 2)").copy().reset_index()
    #keep_inds = []
    drop="domain"
    i=0
    shape = scws_envs.shape[0]
    while i < shape:
         #if scws_envs.iloc[i].hour_group == 0:
            #diffs = abs(scws_envs.iloc[i].dt_utc - scws_envs.dt_utc)
            #if drop=="stns":
             #   scws_envs.loc[(diffs < dt.timedelta(hours=1)) & \
            #	    (np.in1d(scws_envs["stn_id"],scws_envs.iloc[i].stn_id)) & \
            #	    (scws_envs.hour_group==0), "hour_group"] = i+1
            #elif drop=="era5_grid":
             #   scws_envs.loc[(diffs < dt.timedelta(hours=1)) & \
            #	    ( (np.in1d(scws_envs["era5_lat"],scws_envs.iloc[i].era5_lat)) &\
            #	    (np.in1d(scws_envs["era5_lon"],scws_envs.iloc[i].era5_lon))) &\
           # 	    (scws_envs.hour_group==0), "hour_group"] = i+1
            #elif drop=="domain":    
                #scws_envs.loc[(diffs < dt.timedelta(hours=1)) & (scws_envs.hour_group==0), "hour_group"] = i+1

            try:
                diffs = scws_envs.dt_utc - scws_envs.loc[i].dt_utc
                if drop=="domain":
                    hour_group = scws_envs.loc[(diffs < dt.timedelta(hours=1)) & (diffs >= dt.timedelta(hours=0))].sort_values(["gust","dt_utc"],ascending=[False,True])
                    scws_envs = scws_envs.drop(hour_group.iloc[1:].index.values)
            except:
                pass
            i=i+1

    #meas_per_hour = scws_envs.groupby("hour_group").nunique().stn_id
    #meas_per_uid = scws_envs.groupby("uid10").nunique().stn_id
    #scws_envs=pd.merge(scws_envs,meas_per_hour.rename("meas_per_hour"),on="hour_group")
    #scws_envs=pd.merge(scws_envs,meas_per_uid.rename("meas_per_uid"),on="uid10")
    #scws_envs = scws_envs.sort_values("dt_utc").sort_values("gust",ascending=False).drop_duplicates("hour_group").sort_values("dt_utc").drop(columns=["hour_group"])
    scws_envs = scws_envs.sort_values("dt_utc")

    #Create a dataframe for non-events for the purposes of environmental analysis. Defined as hourly occurrences at all unique ERA5 grid points with a neighbouring AWS, which
    # do not record a SCW event in the following hour. Note that if a radar object is observed at the station neighbouring the ERA5 grid point in the following hour,
    # then "in10km" is equal to 1.
    temp_df["scw"] = np.where((temp_df.gust>=25) & (temp_df.wgr_4>=2) & (temp_df.in10km==1),1,0)
    non_scw_envs = temp_df.sort_values(["scw","in10km","gust"],ascending=False).\
	drop_duplicates(subset=["hour_floor","era5_lat","era5_lon"]).query("scw==0").sort_values("dt_utc")
    
    #Get the UIDs for all SCW occurrences (SCW storms). Get all other UIDs (non SCW storms) which go within 10 km of an AWS.
    scws_uid = scws_envs.uid10.unique()
    non_scw_uid = temp_df.query("(in10km==1)").uid10.unique()
    non_scw_uid = non_scw_uid[np.in1d(non_scw_uid, temp_df.query("scw==1").uid10.unique(), invert=True)]
    
    #Load the TINT dataset. Aggregate statistics over time for SCWs and non-SCW storms (mean)
    tint_df = pd.read_csv("/g/data/eg3/ab4502/TINTobjects/"+rid+"_"+d1.strftime("%Y%m%d")+"_"+d2.strftime("%Y%m%d")+".csv")
    tint_df["time"] = pd.DatetimeIndex(tint_df.time)
    keys = tint_df.columns.values
    keys = keys[np.in1d(keys,"bbox",invert=True)]
    agg_dict = dict.fromkeys(keys,"mean")
    agg_dict["time"] = "min" 
    scw_storms = tint_df[np.in1d(tint_df.uid, scws_uid)].groupby("uid").agg(agg_dict)
    non_scw_storms = tint_df[np.in1d(tint_df.uid, non_scw_uid)].groupby("uid").agg(agg_dict)    
    
    return scws_envs, non_scw_envs, scw_storms, non_scw_storms

def load_scws_driver(rid,start_year,end_year):
    scw_envs_df = pd.DataFrame()
    non_scw_envs_df = pd.DataFrame()
    scw_storms_df = pd.DataFrame()
    non_scw_storms_df = pd.DataFrame()
    for y in tqdm.tqdm(np.arange(start_year,end_year+1)):
        for m in np.arange(1,13):
            d1 = dt.datetime(y,m,1)
            d2 = last_day_of_month(d1)
            if os.path.exists("/g/data/eg3/ab4502/ExtremeWind/points/era5_aws_tint_"+rid+"_"+d1.strftime("%Y%m%d")+"_"+d2.strftime("%Y%m%d")+"_max.pkl"):
                scw_envs, non_scw_envs, scw_storms, non_scw_storms = load_scws(rid,y,m)
                scw_envs_df = pd.concat([scw_envs_df, scw_envs])
                non_scw_envs_df = pd.concat([non_scw_envs_df, non_scw_envs])
                scw_storms_df = pd.concat([scw_storms_df, scw_storms])
                non_scw_storms_df = pd.concat([non_scw_storms_df, non_scw_storms])
            else:
                print("NO DATA YEAR "+str(y)+" MONTH "+str(m))
    scw_envs_df.to_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_scw_envs_df.csv")
    non_scw_envs_df.to_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_non_scw_envs_df.csv")
    scw_storms_df.to_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_scw_storms_df.csv")
    non_scw_storms_df.to_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_non_scw_storms_df.csv")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-rid', type=str)
    parser.add_argument('-y1', type=int)
    parser.add_argument('-y2', type=int)
    args = parser.parse_args()
    rid = args.rid
    y1 = args.y1	
    y2 = args.y2

    load_scws_driver(rid,y1,y2)
