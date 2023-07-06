import pandas as pd
import numpy as np
import xarray as xr
import glob
import datetime as dt
import pytz

def load_scws(rid,tz):
    print("loading "+rid+"...")
    df1 = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_scw_envs_df.csv")
    
    df1["cluster_new"] = df1.cluster.map({0:2,2:1,1:0})
    df1 = df1.set_index(pd.DatetimeIndex(df1.dt_utc))
    df1 = add_lt(df1,tz)    
    df1["year"] = df1.index.year
    df1["month"] = df1.index.month
    df1["hour"] = df1["lt"].dt.hour
    df1["rid"] = rid  
    df1["scw"] = 1
    
    return df1

def load_nulls(rid,tz):
    
    df2 = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_non_scw_envs_df.csv")
    
    df2["cluster_new"] = df2.cluster.map({0:2,2:1,1:0})
    df2 = df2.set_index(pd.DatetimeIndex(df2.dt_utc))
    df2 = add_lt(df2,tz)    
    df2["year"] = df2.index.year
    df2["month"] = df2.index.month
    df2["hour"] = df2["lt"].dt.hour
    df2["rid"] = rid   
    df2["scw"] = 0
    
    return df2

def add_lt(df,tz):
    df["lt"] = df.index.tz_localize(pytz.utc).tz_convert(pytz.timezone(tz))
    return df

def remove_suspect_gusts(df):
    dts = ["2010-12-14 07:03:00","2011-01-11 03:49:00","2015-12-15 23:33:00","2020-02-09 01:00:00","2020-02-09 03:18:00","2020-05-25 06:11:00",
          "2012-11-02 18:58:00","2012-12-20 21:19:00","2012-12-15 13:00:00","2012-12-29 16:15:00","2012-12-30 06:25:00","2012-12-30 18:01:00","2013-01-02 08:15:00",
          "2013-01-05 03:36:00","2013-01-12 15:22:00","2013-02-11 07:56:00"]
    return df[np.in1d(df.dt_utc,dts,invert=True)]

def assign_storm_class(data):

    data["aspect_ratio"] = data.major_axis_length / data.minor_axis_length     
    
    #Linear
    data.loc[(data.aspect_ratio>=3) & (data.major_axis_length>=100),"class2"] = "Linear"
    #Non-linear
    data.loc[(data.aspect_ratio<3) & (data.major_axis_length>=100),"class2"] = "Non-linear"
    #Cellular
    data.loc[(data.local_max == 1),"class2"] = "Cellular"
    #Cluster of cells
    data.loc[(data.local_max>=2) & (data.major_axis_length<100),"class2"] = "Cell cluster"
    #Supercell
    data.loc[(data.max_alt>=7) & (data.azi_shear60>4) & ((data.aspect_ratio<3) | (data.major_axis_length<100)),"class2"] = "Supercellular"
    #Linear hybrid
    data.loc[(data.max_alt>=7) & (data.azi_shear60>4) & ((data.major_axis_length>=100)),"class2"] = "Embedded supercell"
    
    return data
    
def driver(rid, tz):
    
    temp_events = remove_suspect_gusts(load_scws(rid,tz))
    if temp_events.shape[0] > 0:
        df_events = assign_storm_class(temp_events)
    else:
        df_events = pd.DataFrame()
    df_nulls = assign_storm_class(load_nulls(rid,tz))

    #Columns to keep for publishing

    ind_list = [\
		#ERA5 details
		"time_y","era5_lat","era5_lon",        
		#Clustering
		"cluster_new",            
		#Wind indices
		"Umean06","Umean01","U10","wg10","s06","ebwd","Umeanwindinf","srhe_left","srh06_left",\
		#Downburst indices
		"dmi","lr_subcloud","lr_freezing","lr03","lr13","wmsi_ml","bdsd","hmi","convgust_wet","convgust_dry",\
		"gustex","dmgwind","dmgwind_fixed","dcape","wmpi","windex","ddraft_temp","te_diff","tei","wndg",\
		#Storm mode
		"dcp","scp","scp_fixed",\
		#Severe storm indices
		"sherb","eff_sherb","sweat","mucape*s06","mlcape*s06","effcape*s06","t_totals","k_index",\
		#Instability indices
		"eff_cape","eff_lcl","ml_cape","ml_lcl","mu_cape","mu_lcl","qmean01","qmean06"
	       ]

    gust_list = ["stn_id","gust","wgr_4","scw"]

    radar_list = ["rid","speed","angle","class2",
		  "in10km","major_axis_length",
		  "minor_axis_length","local_max",
		  "max_alt","azi_shear60"]

    renames = {
	     'Umean06': "Umean06",
	     'Umean01': "Umean01",
	     'U10': "U10",
	     'wg10': "WindGust10",
	     's06': "S06",
	     'ebwd': "EBWD",
	     'Umeanwindinf': "Umeanwindinf",
	     'srhe_left': "SRHE",
	     'srh06_left': "SRH06",
	     'dmi': "DMI",
	     'lr_subcloud': "LR_subcloud",
	     'lr_freezing': "LR_freezing",
	     'lr03': "LR03",
	     'lr13': "LR13",
	     'wmsi_ml': "WMSI",
	     'bdsd': "BDSD",
	     'bdsd_cv': "BDSD_CV",
	     'hmi': "HMI",
	     'convgust_wet': "ConvGust_wet",
	     'convgust_dry': "ConvGust_dry",
	     'gustex': "GUSTEX",
	     'dmgwind': "DmgWind",
	     'dmgwind_fixed': "DmgWind_fixed",
	     'dcape': "DCAPE",
	     'wmpi': "WMPI",
	     'windex': "WINDEX",
	     'ddraft_temp': "DowndraftTemp",
	     'te_diff': "ThetaeDiff",
	     'tei': "TEI",
	     'wndg': "WNDG",
	     'dcp': "DCP",
	     'scp': "SCP",
	     'scp_fixed': "SCP_fixed",
	     'sherb': "SHERB",
	     'eff_sherb': "SHERBE",
	     'sweat': "SWEAT",
	     'mucape*s06': "MUCS6",
	     'mlcape*s06': "MLCS6",
	     'effcape*s06': "EffCS6",
	     't_totals': "T_Totals",
	     'k_index': "K_Index",
	     'eff_cape': "Eff_CAPE",
	     'eff_lcl': "Eff_LCL",
	     'ml_cape': "MLCAPE",
	     'ml_lcl': "ML_LCL",
	     'mu_cape': "MUCAPE",
	     'mu_lcl': "MU_LCL",
	     'qmean01': "Qmean01",
	     'qmean06': "Qmean06",
	    'angle': "Storm_angle",
	    'azi_shear60': "Azimuthal_shear",
	    'class2': "Parent_storm_class",
	    'cluster_new':"Environmental_cluster",
	    'gust':"Wind_gust_observed",
	    'in10km':"Storm_in10km",
	    'local_max':"Local_reflectivity_maxima",
	    'major_axis_length':"Major_axis_length",
	    'max_alt':"Maximum_storm_altitude",
	    'minor_axis_length':"Minor_axis_length",
	    'rid':"Radar_id",
	    'stn_id':"Station_id",
	    'scw':"SCW",
	    'speed':"Storm_speed",
	    'wgr_4':"Peak_to_mean_wind_gust_ratio",
	    'time_y':"ERA5_time",
	    'era5_lat':"ERA5_latitude",
	    'era5_lon':"ERA5_longitude"}

    #To save confusion, if there isn't a storm object within 10 km of the station, don't output any storm stats
    df_nulls.loc[df_nulls["in10km"]==0,np.array(radar_list)[~np.in1d(radar_list,["in10km","rid"])]] = np.nan		

    if temp_events.shape[0] > 0:
        pd.concat([df_events[(gust_list + radar_list + ind_list)].rename(columns=renames),
		    df_nulls[(gust_list + radar_list + ind_list)].rename(columns=renames)],
	axis=0).sort_values("dt_utc").to_csv("/scratch/eg3/ab4502/scw_data_pub/gust_observations_"+rid+".csv")
    else:
		    df_nulls[(gust_list + radar_list + ind_list)].rename(columns=renames).sort_values("dt_utc").to_csv("/scratch/eg3/ab4502/scw_data_pub/gust_observations_"+rid+".csv")        

if __name__ == "__main__":

    rids = ["2","66","69","70","71","64","8","72","75","19","73","78","49","4","40","48","68","63","76","77"]
    tzs = {"68":'Australia/Melbourne',
	   "64":'Australia/Adelaide',
	   "8":'Australia/Brisbane',
	   "72":'Australia/Queensland',
	   "75":'Australia/Queensland',
	   "19":'Australia/Queensland',
	   "73":'Australia/Queensland',
	   "78":'Australia/Queensland',
	   "77":'Australia/Darwin',
	   "49":'Australia/Victoria',
	   "4":'Australia/Sydney',
	   "40":'Australia/Canberra',
	   "48":'Australia/West',
	   "2":'Australia/Melbourne',
	   "66":'Australia/Brisbane',
	   "69":'Australia/NSW',
	   "70":'Australia/Perth',
	   "71":'Australia/Sydney',
	   "63":'Australia/Darwin',
	   "76":'Australia/Hobart',
	   "77":"Australia/Darwin"}

    [driver(rid, tzs[rid]) for rid in rids]
