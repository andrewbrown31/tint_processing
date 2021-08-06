import numpy as np
import h5py
import datetime
import math
import pandas as pd
from skimage.segmentation import expand_labels

def plot_gust_storm_ts(aws_storm):

	#For a merged pandas dataframe, with storm and gust information, plot a time series for each radius

	plt.figure(figsize=[16,8])
	ax1 = plt.subplot(3,1,1)
	ax1.plot(aws_storms.gust, lw=2, label="Gust")
	ax1.plot(aws_storms.where(aws_storms.in20km==1).gust, color="tab:orange", lw=4, label="Gust (w/ storm <= 20 km)")
	plt.legend()

	ax1 = plt.subplot(3,1,2)
	ax1.plot(aws_storms.gust, lw=2, label="Gust")
	ax1.plot(aws_storms.where(aws_storms.in10km==1).gust, color="tab:orange", lw=4, label="Gust (w/ storm <= 10 km)")
	plt.legend()

	ax1 = plt.subplot(3,1,3)
	ax1.plot(aws_storms.gust, lw=2, label="Gust")
	ax1.plot(aws_storms.where(aws_storms.in0km==1).gust, color="tab:orange", lw=4, label="Gust (w/ storm <= 0 km)")
	plt.legend()

def plot_objects_with_stations(scan, storm_df, grid, isstorm, stn_df, r, xlim, ylim):

	#For a given radar scan in TINT output, plot the storm object on-top of wind gust station locations.
	#Expand the object by a given radius (in pixels), r.
	#Stations which are determined to be inside the radius, r, are highlighted.

	ax = plt.gca()
	x = grid["lon/lon"][:]
	plot_grid = np.zeros(x.shape)

	ax.plot(stn_df["lon"], stn_df["lat"], marker="x", ls="none", color="tab:red", mew=2, ms=14)
	try:
		stn_idx = np.array([])
		for uid in storm_df.query("scan=="+str(scan)).uid.unique():
			recon, x, y = reconstruct_grid(grid, storm_df.query("scan=="+str(scan)).query("uid=="+str(uid))["group_id"].values[0])
			stn_idx = np.concatenate((stn_idx,isstorm.query("scan=="+str(scan)).query("uid=="+str(uid)).query("in"+str(r)+"km==1").stn_no.values))
			if isstorm.query("scan=="+str(scan)).query("uid=="+str(uid)).query("in"+str(r)+"km==1").shape[0] > 0:
				plot_grid = np.where(expand_labels(recon, int(r/2.5)), 1, plot_grid)
			else:
				plot_grid = np.where(expand_labels(recon, int(r/2.5)), 0.5, plot_grid)
		c=ax.pcolormesh(x,y,plot_grid,cmap=plt.get_cmap("Greens"), edgecolor="white", vmax=1)
		plt.colorbar(c)
		ax.plot(stn_df.loc[np.in1d(stn_df.stn_no, stn_idx)]["lon"], stn_df.loc[np.in1d(stn_df.stn_no, stn_idx)]["lat"],\
			marker="x", ls="none", color="tab:orange", mew=2, ms=14)
	except:
		print("No objects in this scan")
	ax.set_ylim(ylim)
	ax.set_xlim(xlim)
	ax.grid()

def assign_stations(stn_df, storm_df, grid):

	#Loop over each "uid" (storm object identifier) and "scan" integer (starting at 0) from the loaded TINT object
	#Reconstruct the original radar grid, and decide which stations are inside the storm object, and inside two radii (10, 20 km). Store this info in
	#   three different dataframes
	stns0 = pd.DataFrame(columns = stn_df.stn_no, index=storm_df.index, data=0)
	stns10 = pd.DataFrame(columns = stn_df.stn_no, index=storm_df.index, data=0)
	stns20 = pd.DataFrame(columns = stn_df.stn_no, index=storm_df.index, data=0)
	dist = pd.DataFrame(columns = stn_df.stn_no, index=storm_df.index, data=0)
	stns0["uid"] = storm_df["uid"]; stns0["time"] = storm_df["time"]; stns0["scan"] = storm_df["scan"]
	stns10["uid"] = storm_df["uid"]; stns10["time"] = storm_df["time"]; stns10["scan"] = storm_df["scan"]
	stns20["uid"] = storm_df["uid"]; stns20["time"] = storm_df["time"]; stns20["scan"] = storm_df["scan"]
	dist["uid"] = storm_df["uid"]; dist["time"] = storm_df["time"]; dist["scan"] = storm_df["scan"]
	for s in np.arange(storm_df.scan.max()+1):
		for u in np.unique(storm_df.query("scan=="+str(s)).uid):
			if u >= 0:
				recon, x, y = reconstruct_grid(grid, storm_df.query("scan=="+str(s)).query("uid=="+str(u))["group_id"].values[0])
				#Take h5 file, append stations which intersect storm object to dataframe
				stns0, stns10, stns20, dist = add_stn_ids(recon, x, y, storm_df, stn_df, u, s, stns0, stns10, stns20, dist)

	#From the dataframes generated here (of same size as storm_df), create a new dataframe for each station, indexed by time,
	#   with a binary column for a storm object as well as an identifier for the storm, dropping the storm that's further away 
	#   if there is more than one.
	isstorm = pd.DataFrame()
	for stn in stn_df.stn_no:
		temp_df0 = pd.concat([stns0[[stn, "uid", "time", "scan"]], dist.rename(columns={stn:"dist"})["dist"]], axis=1).\
				sort_values(by=[stn, "dist"], ascending=[False, True]).drop_duplicates("time", keep="first").\
				rename(columns={stn:"in0km"})
		temp_df10 = pd.concat([stns10[[stn, "uid", "time", "scan"]], dist.rename(columns={stn:"dist"})["dist"]], axis=1).\
				sort_values(by=[stn, "dist"], ascending=[False, True]).drop_duplicates("time", keep="first").\
				rename(columns={stn:"in10km"})
		temp_df20 = pd.concat([stns20[[stn, "uid", "time", "scan"]], dist.rename(columns={stn:"dist"})["dist"]], axis=1).\
				sort_values(by=[stn, "dist"], ascending=[False, True]).drop_duplicates("time", keep="first").\
				rename(columns={stn:"in20km"})
		temp_df0["stn_no"] = stn
		isstorm = pd.concat([isstorm,\
		    pd.merge(pd.merge(temp_df0, temp_df10[["time","in10km"]], on="time"), temp_df20[["time","in20km"]], on="time")\
			[["time","stn_no","scan","uid","dist","in0km","in10km","in20km"]]], axis=0)

	return isstorm

def reconstruct_grid(f, group_id):

	#From h5 grid objects (f), reconstruct the radar grid

	bbox = f[group_id].attrs["bbox"]
	x = f["lon/lon"][:]
	y = f["lat/lat"][:]
	recon = np.zeros(x.shape)
	recon[bbox[0]:bbox[2],bbox[1]:bbox[3]] = f[group_id+"/cell_mask"][:]

	return recon, x, y

def stns2grid(stn_df, x, y):

	#From a dataframe of station info, grid the data
	gridded = np.zeros(x.shape)
	for y0, x0, stn_no in zip(stn_df["lat"].values, stn_df["lon"].values, stn_df["stn_no"].values):
		if (x0 >= x.min()) & (x0 <= x.max()) & (y0 >= y.min()) & (y0 <= y.max()):
			dist = latlon_dist(y0, x0, y, x)
			idx = np.argmin(dist)
			grid_x, grid_y = np.unravel_index(idx, x.shape)
			gridded[grid_x, grid_y] = gridded[grid_x, grid_y] + 1
			stn_df.loc[stn_df["stn_no"]==stn_no,"grid_x"] = int(grid_x)
			stn_df.loc[stn_df["stn_no"]==stn_no,"grid_y"] = int(grid_y)

	return gridded, stn_df

def add_stn_ids(recon_grid, x, y, storm_df, stn_info, uid, scan, stns0, stns10, stns20, dist):

	#From a h5 grid, check which AWS stations (stn_info) are within the storm object, as well as within n grid points
	#Append station ids to storm_df
	storm_x, storm_y = (np.where(recon_grid==1, x, np.nan).flatten(), np.where(recon_grid==1, y, np.nan).flatten())
	storm_x = storm_x[~np.isnan(storm_x)]
	storm_y = storm_y[~np.isnan(storm_y)]
	dist.iloc[(stns0["uid"]==uid) & (stns0["scan"]==scan), 0:-3] =\
		[round(np.min(latlon_dist(storm_y, storm_x, yp, xp)),3) for xp,yp in zip(stn_info["lon"].values, stn_info["lat"].values)]
	for r in [0, 4, 8]:
		storm_x, storm_y = np.where(expand_labels(recon_grid, r)==1)
		storm_stns = stn_info.loc[[np.any((storm_x == xp) & (storm_y == yp)) for xp,yp in zip(stn_info["grid_x"].values, stn_info["grid_y"].values)]].stn_no.values
		if r == 0:
			stns0.loc[(stns0["uid"]==uid) & (stns0["scan"]==scan), np.in1d(stns0.columns, storm_stns)] = 1
		elif r == 4:
			stns10.loc[(stns10["uid"]==uid) & (stns10["scan"]==scan), np.in1d(stns10.columns, storm_stns)] = 1
		elif r == 8:
			stns20.loc[(stns20["uid"]==uid) & (stns20["scan"]==scan), np.in1d(stns20.columns, storm_stns)] = 1
	return (stns0, stns10, stns20, dist)

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

if __name__ == "__main__":

	################
	# STATION INFO #
	################
	#Load station info
	names = ["id", "stn_no", "district", "stn_name", "1", "2", "lat", "lon", "3", "4", "5", "6", "7", "8", \
                        "9", "10", "11", "12", "13", "14", "15", "16"]
	stn_df = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/obs/aws/vic_one_min_gust/HD01D_StnDet_999999999990821.txt",\
                names=names, header=0)

	################
	# STORM TRACKS #
	################
	#Define out_id from TINT, which is radar id + %Y%m%d
	#out_id = "02_20200131"
	out_id = "02_20150228"
	#Load .csv TINT track output
	storm_df = pd.read_csv("/g/data/eg3/ab4502/figs/tint/"+out_id+".csv")
	#Load h5 file from TINT output
	grid = h5py.File("/g/data/eg3/ab4502/TINTobjects/"+out_id, "r")
	#Add a "group_id" to the .csv file, which will be used to index the h5 file
	storm_df["group_id"] = pd.DatetimeIndex(storm_df["time"]).strftime("%Y%m%d%H%M%S") + "/" + storm_df["uid"].astype(str)

	#################
	# GRID STATIONS #
	#################
	#Grid station info (w.r.t. the TINT h5 grid), and append grid coordinates to "station info" dataframe
	x, y = (grid["lon/lon"][:], grid["lat/lat"][:])
	gridded_stn, stn_df = stns2grid(stn_df, x, y)

	#############################
	# ASSIGN STATIONS TO STORMS #
	#############################
	isstorm = assign_stations(stn_df, storm_df, grid)
	isstorm = isstorm.set_index(pd.DatetimeIndex(isstorm["time"]).round("1min")).sort_index()
    
        ###################
	# FILL IN TRACKS  #
        ###################
	#TODO: Should storm tracks be interpolated in time and space? Or should we just use the available instantaneous scans and throw
	#   out gusts when there's no scan within X minutes?

        ##########################
	# ASSIGN GUSTS TO STORMS #
        ##########################
	#Merge the one-minute AWS data with storm data, up-sampled to one-minute frequency by forward filling over MIN intervals.
	#Done separately for each station

	#aws = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/obs/aws/vic_one_min_gust/2020.csv")
	aws = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/obs/aws/vic_one_min_gust/2015.csv")
	aws = aws.set_index(pd.DatetimeIndex(aws.dt_utc))
	#stn = 90035    #Cressy
	#stn = 87168	#Sheoaks
	#stn = 86371	#Frankston beach
	#stn = 86077	#Moorabin airport
	#stn = 89002     #Ballarat
	#stn = 86282    #Melbourne airport
	stn = 81123    #Bendigo
	#MIN = 6
	MIN = 12
	aws_storms = pd.merge(isstorm.query("stn_no=="+str(stn)).resample("1min").asfreq().ffill(limit=MIN),\
		aws.query("stn_id=="+str(stn))[["gust","q"]], how="inner", left_index=True, right_index=True)

	###########################
	# MISC PLOTTING FOR TESTS #
	###########################
	import matplotlib.pyplot as plt

	#Plot gridded storm objects for a single scan, matched spatially with gust stations
	scan = 43
	xlim = [x.min(), x.max()]; ylim=[y.min(), y.max()]
	plt.figure(figsize=[18,6])
	ax=plt.subplot(1,3,1)
	plot_objects_with_stations(scan, storm_df, grid, isstorm, stn_df, 0, xlim, ylim)
	plt.title("0 km radius")
	ax=plt.subplot(1,3,2)
	plot_objects_with_stations(scan, storm_df, grid, isstorm, stn_df, 10, xlim, ylim)
	plt.title("10 km radius")
	ax=plt.subplot(1,3,3)
	plot_objects_with_stations(scan, storm_df, grid, isstorm, stn_df, 20, xlim, ylim)
	plt.title("20 km radius")
	plt.suptitle(isstorm.query("scan=="+str(scan)).time[0])

	#Plot one-minute time series of AWS gust with storm flags
	plot_gust_storm_ts(aws_storms)
