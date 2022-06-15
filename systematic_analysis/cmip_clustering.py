from dask.diagnostics import ProgressBar
import xarray as xr
from GadiClient import GadiClient
import matplotlib.pyplot as plt
import numpy as np
from era5_spatial_cluster import era5_clustering, transform_era5, load_cluster

def load_cmip_output(model, experiment, y1, y2, test=False):

	s06 = xr.open_dataset("/g/data/eg3/ab4502/ExtremeWind/aus/regrid_1.5/"+model+"_r1i1p1_"+experiment+"_s06_qm_lsm_"+y1+"_"+y2+".nc",chunks={"time":100}).s06
	qmean01 = xr.open_dataset("/g/data/eg3/ab4502/ExtremeWind/aus/regrid_1.5/"+model+"_r1i1p1_"+experiment+"_qmean01_qm_lsm_"+y1+"_"+y2+".nc",chunks={"time":100}).qmean01
	lr13 = xr.open_dataset("/g/data/eg3/ab4502/ExtremeWind/aus/regrid_1.5/"+model+"_r1i1p1_"+experiment+"_lr13_qm_lsm_"+y1+"_"+y2+".nc",chunks={"time":100}).lr13
	Umean06 = xr.open_dataset("/g/data/eg3/ab4502/ExtremeWind/aus/regrid_1.5/"+model+"_r1i1p1_"+experiment+"_Umean06_qm_lsm_"+y1+"_"+y2+".nc",chunks={"time":100}).Umean06
	bdsd = xr.open_dataset("/g/data/eg3/ab4502/ExtremeWind/aus/regrid_1.5/"+model+"_r1i1p1_logit_aws_"+experiment+"_"+y1+"_"+y2+".nc",chunks={"time":100}).logit_aws

	if test:
		s06 = s06.isel({"time":s06["time.year"]==2005})
		qmean01 = qmean01.isel({"time":qmean01["time.year"]==2005})
		lr13 = lr13.isel({"time":lr13["time.year"]==2005})
		Umean06 = Umean06.isel({"time":Umean06["time.year"]==2005})
		bdsd = bdsd.isel({"time":bdsd["time.year"]==2005})

	dim = ("time","lat","lon")
	f = xr.Dataset({
	    "s06":(dim, s06), "qmean01":(dim, qmean01), "lr13":(dim, lr13), "Umean06":(dim, Umean06), "bdsd":(dim, bdsd)},
	    coords={"time":s06.time, "lat":s06.lat, "lon":s06.lon}).chunk({"time":100})

	return f

def replace_nulls(cluster, s06_transform, qmean01_transform, lr13_transform, Umean06_transform):

	nulls = (s06_transform.isnull() | qmean01_transform.isnull() | lr13_transform.isnull() | Umean06_transform.isnull())
	cluster = xr.where(nulls, np.nan, cluster)
	
	return cluster

def output_and_save(cluster, model, experiment, y1, y2):

	dim=("time","lat","lon")
	#dim=("lat","lon","time")

	#out_ds = xr.Dataset({"cluster1":(dim, (cluster.cluster==0).resample({"time":"1M"}).mean("time")),
		  #"cluster2":(dim, (cluster.cluster==1).resample({"time":"1M"}).mean("time")),
		  #"cluster3":(dim, (cluster.cluster==2).resample({"time":"1M"}).mean("time")),
		  #"cluster1_bdsd":(dim, ((cluster.cluster==0) & (cluster.bdsd>0.83)).resample({"time":"1M"}).mean("time")),
		  #"cluster2_bdsd":(dim, ((cluster.cluster==1) & (cluster.bdsd>0.83)).resample({"time":"1M"}).mean("time")),
		  #"cluster3_bdsd":(dim, ((cluster.cluster==2) & (cluster.bdsd>0.83)).resample({"time":"1M"}).mean("time"))
		  #},
		  #coords={"lat":(("lat"), cluster.lat.values), "lon":(("lon"), cluster.lon.values)})

	out_ds = xr.Dataset({"cluster1":(dim, (cluster.cluster==0).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
		"cluster2":(dim, (cluster.cluster==1).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
		"cluster3":(dim, (cluster.cluster==2).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
		"clusterall_bdsd":(dim, (cluster.bdsd>0.83).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
		"cluster1_bdsd":(dim, ((cluster.cluster==0) & (cluster.bdsd>0.83)).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
		"cluster2_bdsd":(dim, ((cluster.cluster==1) & (cluster.bdsd>0.83)).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
		"cluster3_bdsd":(dim, ((cluster.cluster==2) & (cluster.bdsd>0.83)).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time"))
		},
		coords={"lat":(("lat"), cluster.lat.values), "lon":(("lon"), cluster.lon.values), "time":(cluster.cluster==0).resample({"time":"1M"}).mean("time").time})

	out_ds = xr.where(cluster.isel({"time":0}).cluster.isnull().drop("time"), np.nan, out_ds)

	out_ds.to_netcdf("/g/data/eg3/ab4502/ExtremeWind/aus/regrid_1.5/clustering_v2_"+model+"_"+experiment+"_"+y1+"_"+y2+".nc")

if __name__ == "__main__":

	GadiClient()
	ProgressBar().register()

	#Load the trained, K-means clustering algorithm
	cluster_mod, cluster_input = load_cluster()
	
	#For each cmip model, load the diagnostic data, and apply the k-means algorithm. Save as netcdf output
	#For the historial runs...
	experiment = "historical"; y1="1979"; y2="2005"
	models = ["ACCESS1-3", "ACCESS1-0", "BNU-ESM", "CNRM-CM5", "GFDL-CM3",\
                            "GFDL-ESM2G", "GFDL-ESM2M", "IPSL-CM5A-LR", "IPSL-CM5A-MR",\
                            "MIROC5", "MRI-CGCM3", "bcc-csm1-1"]
	for model in models:
		print(model)
		f = load_cmip_output(model, experiment, y1, y2)
		s06_transform, qmean01_transform, lr13_transform, Umean06_transform = transform_era5(f, cluster_mod, cluster_input)
		cluster = era5_clustering(s06_transform.fillna(0), 
                                 qmean01_transform.fillna(0), 
                                 lr13_transform.fillna(0), 
                                 Umean06_transform.fillna(0), 
                                 f, cluster_mod)
		cluster = replace_nulls(cluster, s06_transform, qmean01_transform, lr13_transform, Umean06_transform)        
		output_and_save(cluster, model, experiment, y1, y2)	

	#For the future runs...
	experiment = "rcp85"; y1="2081"; y2="2100"
	for model in models:
		print(model)
		f = load_cmip_output(model, experiment, y1, y2)
		s06_transform, qmean01_transform, lr13_transform, Umean06_transform = transform_era5(f, cluster_mod, cluster_input)
		cluster = era5_clustering(s06_transform.fillna(0), 
                                 qmean01_transform.fillna(0), 
                                 lr13_transform.fillna(0), 
                                 Umean06_transform.fillna(0), 
                                 f, cluster_mod)
		cluster = replace_nulls(cluster, s06_transform, qmean01_transform, lr13_transform, Umean06_transform)        
		output_and_save(cluster, model, experiment, y1, y2)	
