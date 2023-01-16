from sklearn.cluster import KMeans as kmeans
import argparse
import joblib
from GadiClient import GadiClient
import xarray as xr
import glob
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import numpy as np
import tqdm
import netCDF4 as nc

def calc_bdsd(ds):
    ds = ds.assign(bdsd = 1 / 
                   ( 1 + np.exp( -(6.1e-02*ds["ebwd"] + 1.5e-01*ds["Umean800_600"] + 9.4e-01*ds["lr13"] + 3.9e-02*ds["rhmin13"] +
                                   1.7e-02*ds["srhe_left"] +3.8e-01*ds["q_melting"] +4.7e-04*ds["eff_lcl"] - 1.3e+01 ) ) ) )
    return ds

def last_day_of_month(any_day):
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = any_day.replace(day=28) + dt.timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return next_month - dt.timedelta(days=next_month.day)    

def latlon_dist(lat, lon, lats, lons):

        #Calculate great circle distance (Harversine) between a lat lon point (lat, lon) and a list of lat lon
        # points (lats, lons)

        R = 6373.0

        lat1 = np.deg2rad(lat)
        lon1 = np.deg2rad(lon)
        lat2 = np.deg2rad(lats)
        lon2 = np.deg2rad(lons)
                
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return (R * c)

def load_stn_info(state):

        #Load station info
	names = ["id", "stn_no", "district", "stn_name", "site_open", "site_close", "lat", "lon", "latlon_method", "state",\
			"hgt_asl", "hgt_asl_baro", "wmo_idx", "y1", "y2", "comp%", "Y%", "N%", "W%", "S%", "I%", "#"]

	if state == "vic_nsw":
		stn_info1 = pd.read_csv(glob.glob("/g/data/eg3/ab4502/ExtremeWind/obs/aws/vic_one_min_gust/HD01D_StnDet_*.txt")[0],\
			names=names, header=0)
		stn_info2 = pd.read_csv(glob.glob("/g/data/eg3/ab4502/ExtremeWind/obs/aws/nsw_one_min_gust/HD01D_StnDet_*.txt")[0],\
			names=names, header=0)
		stn_info = pd.concat([stn_info1, stn_info2], axis=0)
	elif state=="nt":
		stn_info = pd.concat(\
		    [pd.read_csv(f, names=names, header=None) for f in glob.glob("/g/data/eg3/ab4502/ExtremeWind/obs/aws/nt_one_min_gust/HD01D_StnDet_*.txt")],axis=0).\
		    sort_values("stn_name")
	elif state=="tas":
		stn_info = pd.concat(\
		    [pd.read_csv(f, names=names, header=None) for f in glob.glob("/g/data/eg3/ab4502/ExtremeWind/obs/aws/tas_one_min_gust/HD01D_StnDet_*.txt")],axis=0).\
		    sort_values("stn_name")
	else:
		stn_info = pd.read_csv(glob.glob("/g/data/eg3/ab4502/ExtremeWind/obs/aws/"+state+"_one_min_gust/HD01D_StnDet_*.txt")[0],\
			names=names, header=0)
	return stn_info

def load_era5(fid):
	era5_str = fid.split("_")[1]+"_"+fid.split("_")[2]
	era5 = xr.open_dataset("/g/data/eg3/ab4502/ExtremeWind/aus/era5/era5_"+era5_str+".nc", chunks={"time":92})
	era5_lat = era5["lat"].values
	era5_lon = era5["lon"].values
	x,y = np.meshgrid(era5_lon,era5_lat)
	return era5, x, y

def subset_era5(era5, stn_lat, stn_lon, y, x):
	dist_km = []
	rad_lats = []
	rad_lons = []
	for i in np.arange(len(stn_lat)):
		dists = latlon_dist(stn_lat[i], stn_lon[i], y, x)
		dist_km.append(dists)
		rad_lats.append(y[dists<50])
		rad_lons.append(x[dists<50])
	unique_lons = np.unique(np.concatenate(rad_lons))
	unique_lats = np.unique(np.concatenate(rad_lats))
	era5_subset = era5.sel({"lon":unique_lons, "lat":unique_lats})
	return era5_subset, rad_lats, rad_lons

def shift_wg10_time(df):
    
    temp_wg10 = df[["time","stn_id","wg10"]].rename(columns={"wg10":"wg10_2"})
    temp_wg10["time"] = temp_wg10["time"] + dt.timedelta(hours=-1)
    merged = pd.merge(df,temp_wg10[["stn_id","time","wg10_2"]],on=["stn_id","time"],how="outer").dropna(subset="ml_cape").fillna(method="pad")
    
    return merged

def extract_era5_df(era5_subset, rad_lats, rad_lons,stn_list, summary):
	temp_df = pd.DataFrame()
	for i in tqdm.tqdm(np.arange(len(stn_list))):
		target_lon = xr.DataArray(rad_lons[i], dims="points")
		target_lat = xr.DataArray(rad_lats[i], dims="points")
		era5_points = era5_subset.sel({"lon":target_lon, "lat":target_lat})
		if summary=="max":
			points = era5_points.max("points").to_dataframe()
		elif summary=="mean":
			points = era5_points.mean("points").to_dataframe()
		elif summary=="min":
			points = era5_points.min("points").to_dataframe()
		else:
			raise ValueError("SUMMARY ARGUMENT NEEDS TO BE: max, min, or mean")
		points["points"]=i
		temp_df = pd.concat([temp_df, points], axis=0)

	temp_df = temp_df.reset_index()
	for p in np.arange(len(stn_list)):
		temp_df.loc[temp_df.points==p,"stn_id"] = stn_list[p]
	temp_df = temp_df.drop("points",axis=1)

	return temp_df

def load_lightning(fid):
	yyyymmdd1 = fid.split("_")[1]
	yyyymmdd2 = fid.split("_")[2]
	start_t = dt.datetime(int(yyyymmdd1[0:4]), int(yyyymmdd1[4:6]), int(yyyymmdd1[6:8]))
	end_t = dt.datetime(int(yyyymmdd2[0:4]), int(yyyymmdd2[4:6]), int(yyyymmdd2[6:8])) + dt.timedelta(days=1)

	f = xr.open_dataset("/g/data/eg3/ab4502/ExtremeWind/ad_data/lightning_1hr/lightning_AUS_0.25deg_1hr_"+yyyymmdd1[0:4]+".nc",\
	    decode_times=False)
	f = f.assign_coords(time=[dt.datetime(int(yyyymmdd1[0:4]),1,1,0) + dt.timedelta(hours=int(i)) for i in np.arange(len(f.time.values))]).\
                sel({"time":slice(start_t,end_t)})
	return f

def extract_lightning_points(lightning, stn_lat, stn_lon, stn_list):

	lon = lightning.lon.values
	lat = lightning.lat.values
	x, y = np.meshgrid(lon,lat)
	df_out = pd.DataFrame()
	for i in np.arange(len(stn_lat)):
		dist_km = latlon_dist(stn_lat[i], stn_lon[i], y, x)
		sliced = xr.where(dist_km<=50, lightning, np.nan)
		temp = sliced.sum(("lat","lon")).Lightning_observed.to_dataframe()
		temp["points"] = i
		df_out = pd.concat([df_out,temp], axis=0)

	for p in np.arange(len(stn_list)):
		df_out.loc[df_out.points==p,"stn_id"] = stn_list[p]
	df_out = df_out.drop("points",axis=1)

	return df_out

def filter_azshear(df):

	df["time"] = (pd.DatetimeIndex(df.time))
	azshear60 = df.set_index(pd.DatetimeIndex(df.time)).groupby("uid").azi_shear.rolling("60min",center=True,min_periods=2,closed="both").median()
	df = pd.merge(df, azshear60.rename("azi_shear60"),left_on=["uid","time"],right_index=True)    
	return df

def latlon_dist(lat, lon, lats, lons):

        #Calculate great circle distance (Harversine) between a lat lon point (lat, lon) and a list of lat lon
        # points (lats, lons)
                        
        R = 6373.0
                        
        lat1 = np.deg2rad(lat)
        lon1 = np.deg2rad(lon)
        lat2 = np.deg2rad(lats)
        lon2 = np.deg2rad(lons)
                
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return (R * c)

def get_mask(lon,lat,thresh=0.5):
    #Return lsm for a given domain (with lats=lat and lons=lon)
    lsm,nat_lon,nat_lat = get_lsm()
    lon_ind = np.where((nat_lon >= lon[0]) & (nat_lon <= lon[-1]))[0]
    lat_ind = np.where((nat_lat >= lat[-1]) & (nat_lat <= lat[0]))[0]
    lsm_domain = lsm[(lat_ind[0]):(lat_ind[-1]+1),(lon_ind[0]):(lon_ind[-1]+1)]
    lsm_domain = np.where(lsm_domain > thresh, 1, 0)

    return lsm_domain

def get_lsm():
    #Load the ERA5 land-sea fraction
    lsm_file = nc.Dataset("/g/data/rt52/era5/single-levels/reanalysis/lsm/1979/lsm_era5_oper_sfc_19790101-19790131.nc")
    lsm = np.squeeze(lsm_file.variables["lsm"][0])
    lsm_lon = np.squeeze(lsm_file.variables["longitude"][:])
    lsm_lat = np.squeeze(lsm_file.variables["latitude"][:])
    lsm_file.close()
    return [lsm,lsm_lon,lsm_lat]


def get_point_data(time,lat,lon,r,var,plot=False,vmin=None,vmax=None):
    
    f = xr.open_dataset(glob.glob("/g/data/eg3/ab4502/ExtremeWind/aus/era5/era5_"\
                            +time.strftime("%Y%m")+"*.nc")[0])[var].sel({"time":time.replace(minute=0)})
    
    lats = f.coords.get("lat").values
    lons = f.coords.get("lon").values
    x,y = np.meshgrid(lons,lats)
    dist_km = (latlon_dist(lat, lon, y, x) )
    mask = get_mask(lons,lats)
    a,b = np.where( (dist_km <= r) & (mask == 1) )
    target_lons = xr.DataArray(lons[b],dims="points")
    target_lats = xr.DataArray(lats[a],dims="points")    
    f_slice = (f.sel(lon=target_lons, lat=target_lats))
    
    if plot:
        plt.figure()
        ax=plt.axes(projection=ccrs.PlateCarree())
        temp = np.where((dist_km <= r) & (mask == 1), f.values, np.nan)
        c=ax.pcolormesh(x,y,temp,vmin=vmin,vmax=vmax)
        plt.colorbar(c)
        ax.coastlines()
    
    #Return the value of the point with the highest absolute value
    return pd.DataFrame([f_slice[v].values[np.abs(f_slice[v]).argmax()] for v in var], index=var)

def get_env_clusters():
	#This is just the code from auto_case_driver/kmeans_and_cluster_eval.ipynb - instead of loading in the clustering from disk
	details_list = pd.read_csv("/g/data/eg3/ab4502/figs/ExtremeWind/case_studies/case_study_list.csv")
	details_list["gust_time_utc"] = pd.DatetimeIndex(details_list.gust_time_utc)
	details_list["rid"] = details_list.rid.astype(str)
	details_list["stn_id"] = details_list.stn_id.astype(str).str.pad(width=6,side="left",fillchar="0")
	var=["s06","qmean01","lr13","Umean06"]
	df = pd.DataFrame()
	for index, row in details_list.iterrows():
		df = pd.concat([df, 
			get_point_data(row["gust_time_utc"], row["lat"], row["lon"], 50, var, plot=False).T],
				axis=0)

	df_norm = (df - df.min(axis=0)) / (df.max(axis=0) - df.min(axis=0))
	mod=kmeans(n_clusters=3, verbose=0, random_state=0)
	mod_fit=mod.fit(df_norm[var])
	cluster_index = mod_fit.predict(df_norm[var])

	return mod_fit, df

def add_missing_cols(df):

	#For "tint_df" dataframes that are created when there are no storm objects, ellipse-fit statistics, such as
	#eccentricity, are not calculated. This function just adds these columns and fills with NaNs

	cols = ["eccentricity","major_axis_length","minor_axis_length","bbox","speed_rnge","num_of_scans","duration_mins"]
	for c in cols:
		if c not in list(df.columns):
			if c == "num_of_scans":
				df[c] = 0
			else:
				df[c] = np.nan	

	return df

def load_tint_aws_era5_lightning(fid, state, summary="max"):

	#Load the AWS one-minute gust data with TINT storm object ID within 10 and 20 km
	tint_df = pd.read_csv("/g/data/eg3/ab4502/TINTobjects/"+fid+"_aws.csv")
	tint_df["hour_floor"] = pd.DatetimeIndex(tint_df.dt_utc).floor("1H")
	tint_df["day"] = pd.DatetimeIndex(tint_df.dt_utc).floor("D")
	stn_list = np.sort(tint_df.stn_id.unique())

	#Load the storm statistics dataset, and merge with the AWS dataset
	storm_df = pd.read_csv("/g/data/eg3/ab4502/TINTobjects/"+fid+".csv")
	storm_df = filter_azshear(storm_df)
	tint_df = tint_df.merge(add_missing_cols(storm_df), left_on=["uid10","scan"], right_on=["uid","scan"]).drop(columns=["uid0","uid20","in0km","in20km",\
		"uid","grid_x","grid_y","bbox"])
	
	#Load AWS info to retrieve lat lon information
	stn_info = load_stn_info(state)
	stn_latlon = stn_info.set_index("stn_no").loc[stn_list][["lat","lon"]].values
	stn_lat = stn_latlon[:,0]; stn_lon = stn_latlon[:,1]
	
	#Load ERA5 convective diagnostics and coordinates
	era5, x, y = load_era5(fid)

	print("subsetting era5...")
	#For each AWS, get the unique lat/lons within 50 km, subset the ERA5 diagnostics to that region. Return the radius lat and lons for each station
	era5_subset, rad_lats, rad_lons = subset_era5(era5,stn_lat,stn_lon,y,x)

	#Load the ERA5 land sea mask, and mask the convective diagnostics
	era5_mask = (xr.open_dataset("/g/data/rt52/era5/single-levels/reanalysis/lsm/1979/lsm_era5_oper_sfc_19790101-19790131.nc").\
			isel({"time":0}).sel({"longitude":era5_subset.lon, "latitude":era5_subset.lat}).lsm >= 0.5).values
	era5_subset = xr.where(era5_mask>=0.5, era5_subset, np.nan).persist()

	#Add the BDSD to the ERA5 subset
	era5_subset = calc_bdsd(era5_subset)

	print("extracting data...")
	#Extract point data within 50 km of each station (mean, min or max)
	era5_df = extract_era5_df(era5_subset, rad_lats, rad_lons,stn_list,summary)

	#Shift the WG10 column backwards by one hour, seeing as this variable is defined as "maximum in previous hour"
	#Call this shifted wg10 "wg10_2".
	#Because we don't have the first hour of the next month here, we simply pad these values using the last observation
	era5_df = shift_wg10_time(era5_df)

	#Add lat lon info
	era5_lat = []; era5_lon = []
	for i in np.arange(len(stn_list)):
		era5_lon.append(era5_subset.lon.values[np.argmin(abs(era5_subset.lon.values-stn_lon[i]))])
		era5_lat.append(era5_subset.lat.values[np.argmin(abs(era5_subset.lat.values-stn_lat[i]))])
	era5_df["era5_lat"] = era5_df.stn_id.map(dict(zip(stn_list,era5_lat)))
	era5_df["era5_lon"] = era5_df.stn_id.map(dict(zip(stn_list,era5_lon)))

	#Lightning data
	#Merge ERA5 and Lightning hourly data, then merge the hourly data with one minute AWS/TINT data
	year = int(fid.split("_")[1][0:4])
	if (year >= 2005) & (year <= 2020):
		lightning = load_lightning(fid)
		lightning_df = extract_lightning_points(lightning, stn_lat, stn_lon, stn_list).reset_index()
		era5_df = era5_df.merge(lightning_df, on=["time","stn_id"])
	else:
		print("NOTE THAT LIGHTNING DATA IS NOT AVAILABLE FOR THIS YEAR")
		era5_df["Lightning_observed"] = np.nan
	aws_era5_tint = tint_df.merge(era5_df,left_on=["hour_floor","stn_id"], right_on=["time","stn_id"])

	#Load clustering classification model saved by ~/working/observations/tint_processing/auto_case_driver/kmeans_and_cluster_eval.ipynb
	cluster_mod, cluster_input = get_env_clusters()
	input_df = (aws_era5_tint[["s06","qmean01","lr13","Umean06"]]\
		   - cluster_input.min(axis=0))\
	    / (cluster_input.max(axis=0) - \
	       cluster_input.min(axis=0))
	aws_era5_tint["cluster"] = cluster_mod.predict(input_df)

	#Save as pickle for fast i/o (compared with csv)
	aws_era5_tint.to_pickle("/g/data/eg3/ab4502/ExtremeWind/points/era5_aws_tint_"+fid+"_"+summary+".pkl")

if __name__ == "__main__":

	client=GadiClient()

	parser = argparse.ArgumentParser()
	parser.add_argument('-year', type=str)
	parser.add_argument('-month', type=str)
	parser.add_argument('-rid', type=str)
	parser.add_argument('-state', type=str)
	parser.add_argument('-summary', type=str)
	args = parser.parse_args()
	year = args.year
	month = args.month
	rid = args.rid
	state = args.state
	summary = args.summary

	date = dt.datetime(int(year), int(month), 1)
	date2 = last_day_of_month(date)
	fid1 = date.strftime("%Y%m%d")
	fid2 = date2.strftime("%Y%m%d")
	print(date)
	load_tint_aws_era5_lightning(rid+"_"+fid1+"_"+fid2, state, summary=summary)

	client.close()
