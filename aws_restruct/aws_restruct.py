import argparse
import pandas as pd
import numpy as np
import glob
from tqdm import tqdm

def read_aws(stn_id, times, state):
	if state in ["tas","nt"]: 
		dtypes = {"hd":str, "stn_id":str, "yyyy_lt":str,"mm_lt":str,"dd_lt":str,"hh_lt":str,"MM_lt":str,\
				"utc_yyyy":str,"utc_mm":str,"utc_dd":str,"utc_hh":str,"utc_MM":str,"gust":str, "q":str, "#":str}
		df=pd.read_csv(glob.glob("/g/data/eg3/ab4502/ExtremeWind/obs/aws/"+state+"_one_min_gust/HD01D_Data_*"+stn_id+"*.txt")[0],\
			names=list(dtypes.keys()),header=0,dtype=dtypes)
		df["dt_utc"] = pd.to_datetime(df["utc_yyyy"] + df["utc_mm"] + df["utc_dd"] + df["utc_hh"] + df["utc_MM"], format="%Y%m%d%H%M")
		df["dt_lt"] = (df["yyyy_lt"] + df["mm_lt"] + df["dd_lt"] + df["hh_lt"] + df["MM_lt"])
		df = df.set_index("dt_utc")
		df["gust"] = pd.to_numeric(df["gust"], errors="coerce") / 3.6
		df = df[["hd","stn_id","dt_lt","gust","q","#"]]
	else:
		dtypes = {"hd":str, "stn_id":str, "dt_lt":str, "dt_utc":str, "gust":str, "q":str, "#":str}
		df=pd.read_csv(glob.glob("/g/data/eg3/ab4502/ExtremeWind/obs/aws/"+state+"_one_min_gust/HD01D_Data_*"+stn_id+"*.txt")[0],\
			names=["hd","stn_id","dt_lt","dt_utc","gust","q","#"],header=0,dtype=dtypes)
		df["dt_utc"] = pd.to_datetime(df["dt_utc"], format="%Y%m%d%H%M")
		df = df.set_index("dt_utc")
		df["gust"] = pd.to_numeric(df["gust"], errors="coerce")    
	return df.loc[slice(times[0], times[1])]

def read_and_combine(y, info, state):
	df = pd.DataFrame()
	print("INFO: Processing "+str(info.shape[0]) +" stations for "+state+" during "+y)
	for stn_id in tqdm(info.site.astype(str)):
		df = pd.concat([df, read_aws(stn_id, [y+"-01-01 00:00", y+"-12-31 23:59"], state)], axis=0)
	df[["stn_id","dt_lt","gust","q"]].to_csv("/g/data/eg3/ab4502/ExtremeWind/obs/aws/"+state+"_one_min_gust/"+y+".csv")
	del df

if __name__ == "__main__":

	#For the one-minute AWS data downloaded from TCZ, take the station-based .csv files and restructure them into yearly files for all station.
	#Do this on a state by state basis

	parser = argparse.ArgumentParser(description='convert station-based .csv files to yearly files for a given year')
	parser.add_argument("-y",help="Year",required=True)
	args = parser.parse_args()
	y = args.y
	
	info_cols = ["site","name","lat","lon","start1","start2","end1","end2","years","%","obs","AWS"]
	info_cols2 = ["site","name","_","lat","lon","start1","start2","end1","end2","years","%","obs","AWS"]
	vic_info = pd.read_fwf("/home/548/ab4502/working/observations/data/vic_onemin_gust_sites.txt", header=None, names=info_cols)
	nsw_info = pd.read_fwf("/home/548/ab4502/working/observations/data/nsw_onemin_gust_sites.txt", header=None, names=info_cols)
	qld_info = pd.read_fwf("/home/548/ab4502/working/observations/data/qld_onemin_gust_sites.txt", header=None, names=info_cols2)
	sa_info = pd.read_fwf("/home/548/ab4502/working/observations/data/sa_onemin_gust_sites.txt", header=None, names=info_cols)
	wa_info = pd.read_fwf("/home/548/ab4502/working/observations/data/wa_onemin_gust_sites.txt", header=None, names=info_cols)
	nt_info = pd.read_fwf("/home/548/ab4502/working/observations/data/nt_onemin_gust_sites.txt", header=None, names=info_cols)
	tas_info = pd.read_fwf("/home/548/ab4502/working/observations/data/tas_onemin_gust_sites.txt", header=None, names=info_cols)

	#read_and_combine(y, vic_info, "vic")
	#read_and_combine(y, nsw_info, "nsw")
	#read_and_combine(y, qld_info, "qld")
	#read_and_combine(y, sa_info, "sa")
	#read_and_combine(y, wa_info, "wa")
	read_and_combine(y, tas_info, "tas")
	read_and_combine(y, nt_info, "nt")
