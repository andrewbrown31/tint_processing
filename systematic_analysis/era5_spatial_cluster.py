import tqdm
import pandas as pd
from GadiClient import GadiClient
import xarray as xr
import numpy as np
import joblib

def calc_bdsd(ds):
    #Calculate the Brown Dowdy Statistical Diagnostic 
    ds = ds.assign(bdsd = 1 / 
                   ( 1 + np.exp( -(6.1e-02*ds["ebwd"] + 1.5e-01*ds["Umean800_600"] + 9.4e-01*ds["lr13"] + 3.9e-02*ds["rhmin13"] +
                                   1.7e-02*ds["srhe_left"] +3.8e-01*ds["q_melting"] +4.7e-04*ds["eff_lcl"] - 1.3e+01 ) ) ) )
    return ds

def load_era5(y,test=False):

    #Load ERA5 diagnostics

    v = ["qmean01","lr13","Umean06","s06","bdsd"]
    if test:
        f=calc_bdsd(xr.open_mfdataset(["/g/data/eg3/ab4502/ExtremeWind/aus/era5/era5_20200201_20200229.nc",\
			    "/g/data/eg3/ab4502/ExtremeWind/aus/era5/era5_20200101_20200131.nc"],
		combine='by_coords'))[v]
    else:
        f=calc_bdsd(xr.open_mfdataset("/g/data/eg3/ab4502/ExtremeWind/aus/era5/era5_"+y+"*.nc",combine='by_coords'))[v]
    f = f.isel({"time":np.in1d(f["time"].dt.hour, [0,6,12,18])})

    return f

def load_cluster():

    #Load the k-means clustering model 

    cluster_mod = joblib.load('/g/data/eg3/ab4502/figs/ExtremeWind/case_studies/cluster_model_era5.pkl')
    cluster_input = pd.read_csv("/g/data/eg3/ab4502/figs/ExtremeWind/case_studies/cluster_input_era5.csv").drop(columns=["Unnamed: 0"])

    return cluster_mod, cluster_input

def transform_era5(f, cluster_mod, cluster_input):

    #Transform the ERA5 diagnostics for input into the k-means model

    s06 = (f["s06"] - cluster_input["s06"].min()) / (cluster_input["s06"].max()-cluster_input["s06"].min())
    qmean01 = (f["qmean01"] - cluster_input["qmean01"].min()) / (cluster_input["qmean01"].max()-cluster_input["qmean01"].min())
    lr13 = (f["lr13"] - cluster_input["lr13"].min()) / (cluster_input["lr13"].max()-cluster_input["lr13"].min())
    Umean06 = (f["Umean06"] - cluster_input["Umean06"].min()) / (cluster_input["Umean06"].max()-cluster_input["Umean06"].min())

    return s06, qmean01, lr13, Umean06

def era5_clustering(s06, qmean01, lr13, Umean06, f, cluster_mod):

    #Use the k-means clustering model on all the spatial ERA5 data. This will assign a cluster to every grid point.

    dim=("time","lat","lon")

    s06_1d = s06.stack(dim=dim)
    qmean01_1d = qmean01.stack(dim=dim)
    lr13_1d = lr13.stack(dim=dim)
    Umean06_1d = Umean06.stack(dim=dim)
    X = pd.DataFrame({"s06":s06_1d, "qmean01":qmean01_1d, "lr13":lr13_1d, "Umean06":Umean06_1d})
    preds = cluster_mod.predict(X).reshape(s06.shape)
    preds_new = np.copy(preds)
    preds_new[preds==0]=2
    preds_new[preds==1]=0
    preds_new[preds==2]=1

    era5_cluster = xr.Dataset({"cluster":(dim, preds_new), "bdsd":(dim, f.bdsd.values)},\
			coords={"lat":(("lat"), f.lat.values), "lon":(("lon"), f.lon.values), "time":(("time"), f.time.values)}).chunk(f.chunks)

    return era5_cluster

def summarise_and_save(era5_cluster,y):

    #From the 3-d clustering grid, save monthly output for:
    #	-> The fraction of times belonging to each cluster at each grid point
    #	-> The fraction of times belonging to each cluster that has a BDSD value in excess of 0.83 (considered favourable for SCW events)

   dim=("time","lat","lon")

   #out_ds = xr.Dataset({"cluster1":(dim, (era5_cluster.cluster==0).resample({"time":"1M"}).mean("time")),
              #"cluster2":(dim, (era5_cluster.cluster==1).resample({"time":"1M"}).mean("time")),
              #"cluster3":(dim, (era5_cluster.cluster==2).resample({"time":"1M"}).mean("time")),
              #"cluster1_bdsd":(dim, ((era5_cluster.cluster==0) & (era5_cluster.bdsd>0.83)).resample({"time":"1M"}).mean("time")),
              #"cluster2_bdsd":(dim, ((era5_cluster.cluster==1) & (era5_cluster.bdsd>0.83)).resample({"time":"1M"}).mean("time")),
              #"cluster3_bdsd":(dim, ((era5_cluster.cluster==2) & (era5_cluster.bdsd>0.83)).resample({"time":"1M"}).mean("time"))
              #},
              #coords={"lat":(("lat"), era5_cluster.lat.values), "lon":(("lon"), era5_cluster.lon.values)})

   out_ds = xr.Dataset({"cluster1":(dim, (era5_cluster.cluster==0).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
	    "cluster2":(dim, (era5_cluster.cluster==1).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
	    "cluster3":(dim, (era5_cluster.cluster==2).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
	    "clusterall_bdsd":(dim, (era5_cluster.bdsd>0.83).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
	    "cluster1_bdsd":(dim, ((era5_cluster.cluster==0) & (era5_cluster.bdsd>0.83)).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
	    "cluster2_bdsd":(dim, ((era5_cluster.cluster==1) & (era5_cluster.bdsd>0.83)).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time")),
	    "cluster3_bdsd":(dim, ((era5_cluster.cluster==2) & (era5_cluster.bdsd>0.83)).resample({"time":"1D"}).max(("time")).resample({"time":"1M"}).sum("time"))
	    },
	    coords={"lat":(("lat"), era5_cluster.lat.values), "lon":(("lon"), era5_cluster.lon.values), "time":(era5_cluster.cluster==0).resample({"time":"1M"}).mean("time").time})

   out_ds.to_netcdf("/g/data/eg3/ab4502/ExtremeWind/aus/era5/clusters_"+y+".nc")

if __name__ == "__main__":

    GadiClient()

    for y in tqdm.tqdm(np.arange(1979,2021)):
        f = load_era5(str(y))

        cluster_mod, cluster_input = load_cluster()
        
        s06, qmean01, lr13, Umean06 = transform_era5(f, cluster_mod, cluster_input)

        era5_cluster = era5_clustering(s06, qmean01, lr13, Umean06, f, cluster_mod)

        summarise_and_save(era5_cluster, str(y))

    
