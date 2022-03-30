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

	f = xr.open_dataset("/g/data/eg3/ab4502/ExtremeWind/ad_data/lightning/lightning_Australasia0.250000degree_6.00000hr_"+yyyymmdd1[0:4]+".nc",\
	    decode_times=False)
	f = f.assign_coords(time=[dt.datetime(int(yyyymmdd1[0:4]),1,1,0) + dt.timedelta(hours=int(i*6)) for i in f.time.values]).\
		sel({"time":slice(start_t,end_t)})
	f = f.assign_coords(lat=np.arange(f.lat.min(), f.lat.max() + 0.25, 0.25))
	f = f.assign_coords(lon=np.arange(f.lon.min(), f.lon.max() + 0.25, 0.25))
	f = f.resample({"time":"1H"}).nearest()
	return f

def extract_lightning_points(lightning, stn_lat, stn_lon, stn_list):

	lon = lightning.lon.values
	lat = lightning.lat.values
	x, y = np.meshgrid(lon,lat)
	df_out = pd.DataFrame()
	for i in np.arange(len(stn_lat)):
		dist_km = latlon_dist(stn_lat[i], stn_lon[i], y, x)
		sliced = xr.where(dist_km<=50, lightning, np.nan)
		temp = sliced.max(("lat","lon")).Lightning_observed.to_dataframe()
		temp["points"] = i
		df_out = pd.concat([df_out,temp], axis=0)

	for p in np.arange(len(stn_list)):
		df_out.loc[df_out.points==p,"stn_id"] = stn_list[p]
	df_out = df_out.drop("points",axis=1)

	return df_out

def load_tint_aws_era5_lightning(fid, state, summary="max"):

	#Load the AWS one-minute gust data with TINT storm object ID within 10 and 20 km
	tint_df = pd.read_csv("/g/data/eg3/ab4502/TINTobjects/"+fid+"_aws.csv")
	tint_df["hour_floor"] = pd.DatetimeIndex(tint_df.dt_utc).floor("1H")
	tint_df["day"] = pd.DatetimeIndex(tint_df.dt_utc).floor("D")
	stn_list = np.sort(tint_df.stn_id.unique())

	#Load the storm statistics dataset, and merge with the AWS dataset
	storm_df = pd.read_csv("/g/data/eg3/ab4502/TINTobjects/"+fid+".csv")
	tint_df = tint_df.merge(storm_df, left_on=["uid10","scan"], right_on=["uid","scan"]).drop(columns=["uid0","uid20","in0km","in20km",\
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

	print("extracting data...")
	#Extract point data within 50 km of each station (mean, min and max)
	era5_df = extract_era5_df(era5_subset, rad_lats, rad_lons,stn_list,summary)

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
	if year >= 2005:
		lightning = load_lightning(fid)
		lightning_df = extract_lightning_points(lightning, stn_lat, stn_lon, stn_list).reset_index()
		era5_df = era5_df.merge(lightning_df, on=["time","stn_id"])
	else:
		era5_df["Lightning_observed"] = np.nan
	aws_era5_tint = tint_df.merge(era5_df,left_on=["hour_floor","stn_id"], right_on=["time","stn_id"])

	#Load clustering classification model saved by ~/working/observations/tint_processing/auto_case_driver/kmeans_and_cluster_eval.ipynb
	cluster_mod = joblib.load('/g/data/eg3/ab4502/figs/ExtremeWind/case_studies/cluster_model_era5.pkl')
	cluster_input = pd.read_csv("/g/data/eg3/ab4502/figs/ExtremeWind/case_studies/cluster_input_era5.csv").drop(columns=["Unnamed: 0"])
	input_df = (aws_era5_tint[["s06","qmean01","lr13","Umean06"]]\
		   - cluster_input.min(axis=0))\
	    / (cluster_input.max(axis=0) - \
	       cluster_input.min(axis=0))
	aws_era5_tint["cluster"] = cluster_mod.predict(input_df)

	#NOTE Add BDSD
	aws_era5_tint = calc_bdsd(aws_era5_tint)

	#Save as pickle for fast i/o (compared with csv)
	aws_era5_tint.to_pickle("/g/data/eg3/ab4502/ExtremeWind/points/era5_aws_tint_"+fid+"_"+summary+".pkl")

if __name__ == "__main__":

	GadiClient()

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
