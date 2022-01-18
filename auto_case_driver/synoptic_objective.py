import warnings
import xarray as xr
import datetime as dt
import glob
import numpy as np
import metpy.calc as mpcalc
import metpy.units as units
import wrf
import tqdm
import pandas as pd
warnings.simplefilter("ignore")

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

def synoptic_diagnostics(domain, time, wb_hgt=850, smoothing=4):

    lon1, lat1, lon2, lat2 = domain

    #Calculate the wet bulb potential temperature gradient
    fq=xr.open_dataset(glob.glob("/g/data/rt52/era5/pressure-levels/reanalysis/q/"+time.strftime("%Y")+"/q_era5_oper_pl_"+time.strftime("%Y%m")+"*.nc")[0],chunks={"time":10})\
                   .sel({"level":slice(wb_hgt,wb_hgt)}).sel({"longitude":slice(lon1,lon2), "latitude":slice(lat2,lat1)}).metpy.assign_crs(grid_mapping_name='latitude_longitude').q
    ft=xr.open_dataset(glob.glob("/g/data/rt52/era5/pressure-levels/reanalysis/t/"+time.strftime("%Y")+"/t_era5_oper_pl_"+time.strftime("%Y%m")+"*.nc")[0],chunks={"time":10})\
                   .sel({"level":slice(wb_hgt,wb_hgt)}).sel({"longitude":slice(lon1,lon2), "latitude":slice(lat2,lat1)}).metpy.assign_crs(grid_mapping_name='latitude_longitude').t
    fdp = mpcalc.dewpoint_from_specific_humidity(wb_hgt*units.units.hectopascal, ft, fq)

    p3d = xr.DataArray(data = np.ones(ft.shape) * (wb_hgt*100), coords=ft.coords, dims=ft.dims, attrs={"units":"Pa"})
    wb = wrf.wetbulb(p3d, ft, fq, meta=True)
    wb_pot = mpcalc.potential_temperature(p3d, wb).isel({"level":0})
    dlat, dlon = mpcalc.gradient(wb_pot.coarsen({"latitude":smoothing, "longitude":smoothing},boundary="pad").mean(), axes=["latitude","longitude"])
    wb_pot_grad = np.sqrt(np.square(dlat) + np.square(dlon)).metpy.convert_units("K/km")

    #Calculate the 500 hPa geostrophic vorticity
    fz=xr.open_dataset(glob.glob("/g/data/rt52/era5/pressure-levels/reanalysis/z/"+time.strftime("%Y")+"/z_era5_oper_pl_"+time.strftime("%Y%m")+"*.nc")[0], chunks={"time":10})\
                .sel({"level":slice(500,500)})\
                .sel({"longitude":slice(lon1,lon2), "latitude":slice(lat2,lat1)})\
                .metpy.assign_crs(grid_mapping_name='latitude_longitude').z\
                .coarsen({"latitude":smoothing, "longitude":smoothing}, boundary="pad").mean().isel({"level":0})
    lons, lats = np.meshgrid(fz.longitude, fz.latitude)
    f=mpcalc.coriolis_parameter(lats * units.units.degree)
    laplacian = mpcalc.laplacian(fz, axes=["latitude","longitude"]) / f
    
    return wb_pot_grad, laplacian

def get_point_data(f,lat,lon,r,name,var,plot=False,vmin=None,vmax=None,func="abs"):
    lats = f.coords.get("latitude").values
    lons = f.coords.get("longitude").values
    x,y = np.meshgrid(lons,lats)
    dist_km = (latlon_dist(lat, lon, y, x) )
    a,b = np.where( (dist_km <= r) )
    target_lons = xr.DataArray(lons[b],dims="points")
    target_lats = xr.DataArray(lats[a],dims="points")    
    f_slice = (f.sel(longitude=target_lons, latitude=target_lats))
    if func=="abs":
        out_df = f_slice.isel({"points":np.abs(f_slice).argmax("points")}).to_pandas()
    elif func=="max":
        out_df = f_slice.max("points").to_pandas()
    elif func=="min":
        out_df = f_slice.min("points").to_pandas()
    return pd.DataFrame({var:out_df.values, "lat":lat, "lon":lon, "loc":name}, index=out_df.index)

if __name__ == "__main__":

    import climtas.nci
    climtas.nci.GadiClient()

    lon1 = 120; lat1 = -44.5; lon2 = 160; lat2 = -15
    domain = [lon1,lat1,lon2,lat2]

    smoothing=4
    wb_hgt=700

    names = []
    times = []
    laplacians = []
    wb_grads = []
    lats = []
    lons = []
    points = [ [-37.6654, 144.8322], [-33.9465, 151.1731], [-27.6297, 152.7111], [-31.1558, 136.8054] ]
    loc_names = ["Melbourne","Sydney","Amberley","Woomera"]
    df_500 = pd.DataFrame()
    df_1000 = pd.DataFrame()
    for y in np.arange(2005,2019):
        for m in np.arange(1,13):
            date = dt.datetime(y,m,1)
            print(date)
            wb_pot_grad, laplacian = synoptic_diagnostics(domain, date, wb_hgt=wb_hgt, smoothing=smoothing)
            for p in np.arange(len(points)):
                    l_df_1000 = get_point_data(laplacian,points[p][0],points[p][1],1000,loc_names[p],"laplacian",func="min")
                    w_df_1000 = get_point_data(wb_pot_grad,points[p][0],points[p][1],1000,loc_names[p],"wb_pot_grad",func="max")
                    temp_df_1000 = pd.concat([l_df_1000,w_df_1000["wb_pot_grad"]],axis=1)
                    df_1000 = pd.concat([df_1000, temp_df_1000],axis=0)

                    l_df_500 = get_point_data(laplacian,points[p][0],points[p][1],500,loc_names[p],"laplacian",func="min")
                    w_df_500 = get_point_data(wb_pot_grad,points[p][0],points[p][1],500,loc_names[p],"wb_pot_grad",func="max")
                    temp_df_500 = pd.concat([l_df_500,w_df_500["wb_pot_grad"]],axis=1)
                    df_500 = pd.concat([df_500, temp_df_500],axis=0)
    df_500.to_csv("/g/data/eg3/ab4502/ExtremeWind/points/era5_synoptic_500km_wb"+str(wb_hgt)+"_smoothing"+str(smoothing)+"_2005_2018.csv")
    df_1000.to_csv("/g/data/eg3/ab4502/ExtremeWind/points/era5_synoptic_1000km_wb"+str(wb_hgt)+"_smoothing"+str(smoothing)+"_2005_2018.csv")
