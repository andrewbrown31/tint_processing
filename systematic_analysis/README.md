# Log for Long-Term Observational Characteristics of Different Severe Convective Wind Types around Australia

This log details the construction of results for Brown et al. (https://doi.org/10.1175/WAF-D-23-0069.1), with figure numbers referenced below from that study. It is noted that this is a working repository, and may be updated after this publication (with the version at submission available [here](https://github.com/andrewbrown31/tint_processing/tree/278062c482aaf6b2bfe7c9bc6008d8179678aedd).

## Generating and merging data

1) **Process the level1b [AURA radar](https://www.openradar.io/) data using [`../tint_driver.py`](../tint_driver.py).** This also requires some pre-processing of [automatic weather station (AWS) data](http://www.bom.gov.au/climate/data/stations/) using the [`../aws_restruct/`](../aws_restruct) directory. For submitting [`../tint_driver.py`](../tint_driver.py) jobs to the PBS queue, the `../jobs_*/` directories are used. For example, [`../jobs_2/tint_driver.sh`](../jobs_2/tint_driver.sh) processes the radar data for the Melbourne radar. Note that these a slightly modified version of [TINT](https://github.com/andrewbrown31/TINT) and [tobac](https://github.com/andrewbrown31/tobac/tree/andrewbrown31) is used.
2) **Process ERA5 pressure level data on rt52 into convective diagnostics** using the [`era5_wrfpython/`](https://github.com/andrewbrown31/SCW-analysis/tree/master/jobs/era5_wrfpython) directory in the [SCW-analysis](https://github.com/andrewbrown31/SCW-analysis/tree/master) repository
3) **Perform [clustering](../auto_case_driver/kmeans_and_cluster_eval.ipynb) on a smaller set of 36 cases**, based on environmental factors. See `../auto_case_driver/`.
4) **Merge storm (from TINT), AWS, lightning data with ERA5 convective diagnostics**. This is done using the [`merge_data.py`](merge_data.py) script, that is submitted to the PBS queue using the `merge_data_jobs/*/` directories for each radar.
5) **Summarise the files created by the above step for fast analysis** using [`get_scw_stats.py`](get_scw_stats.py). This is submitted to the PBS queue using shell scripts in the `get_scw_stats_jobs/` directory.

## Figures and analysis
### Figure 1 and Table 1
[station_stats.ipynb](station_stats.ipynb)

### Figure 2, 3
[event_analysis.ipynb](event_analysis.ipynb)

### Figure 4, 5, 6, 7 and 8 Table 3 and 4
[non_event_analysis.ipynb](non_event_analysis.ipynb)

### Figure 9 and 10
Plotting done in [auc_scores.ipynb](auc_scores.ipynb). Skill scores calculated using [skill_test.py](skill_test.py), [skill_test_in10km_nulls.py](skill_test_in10km_nulls.py), and [skill_test_storm_class.py](skill_test_storm_class.py) (depending on what are used for events/non-events)

# Log for Severe Convective Winds in Australia and Their Sensitivity to Global Warming. Section 6: Australian climatology of severe convective wind environments for different event types, and future projections based on global climate model data (in preparation)

This log details code used in the production of thesis results (in preparation)

## Generating data

1) **Process ERA5 pressure level data on rt52 into convective diagnostics** using the [`era5_wrfpython/`](https://github.com/andrewbrown31/SCW-analysis/tree/master/jobs/era5_wrfpython) directory in the [SCW-analysis](https://github.com/andrewbrown31/SCW-analysis/tree/master) repository.
2) **Perform severe convective wind environment (SCW) clustering on gridded ERA5 data** using the diagnostics calculated in step 1, and the [clustering model of Brown et al. (2023)](../auto_case_driver/kmeans_and_cluster_eval.ipynb). This step uses the [`era5_spatial_cluster.py`](https://github.com/andrewbrown31/tint_processing/blob/main/systematic_analysis/era5_spatial_cluster.py) script, that is submitted to the Gadi job scheduler using [`era5_spatial_cluster.sh`](https://github.com/andrewbrown31/tint_processing/blob/main/systematic_analysis/era5_spatial_cluster.sh). The script also uses the statistical diagnostic of Brown and Dowdy (2021) to classify if the environment is favourable for a SCW event. The output of this step is monthly netcdf files, with the fraction of 6-hourly time steps belonging to each type of SCW environment, and the fraction of time steps that are favourable for an SCW event.
3) **Process CMIP5 sub-daily pressure level data into convective diagnostic for SCW analysis**, including a bias correction process following Brown and Dowdy (2021). This code is in a [separate repository](https://github.com/andrewbrown31/SCW-analysis/tree/master) with a log [here](https://github.com/andrewbrown31/SCW-analysis/blob/master/cmip/log.md).
4) **Repeat Step 2 but for the processed CMIP5 diagnostics calculated in Step 3**. This uses [`cmip_clustering.py`](https://github.com/andrewbrown31/tint_processing/blob/main/systematic_analysis/cmip_clustering.py), submitted to the Gadi job queue using [`cmip_clustering.sh`](https://github.com/andrewbrown31/tint_processing/blob/main/systematic_analysis/cmip_clustering.sh).

## Figures

Figures for ERA5 climatology and trends are created [here](https://github.com/andrewbrown31/tint_processing/blob/main/systematic_analysis/era5_cluster_predict.ipynb).

Figures for CMIP5 ensemble climatology and trends are created [here](https://github.com/andrewbrown31/tint_processing/blob/main/systematic_analysis/cmip_clustering.ipynb).

### References 

Brown, A., & Dowdy, A. (2021). Severe Convective Wind Environments and Future Projected Changes in Australia. Journal of Geophysical Research: Atmospheres, 126(16), 1–17. https://doi.org/10.1029/2021JD034633

Brown, A., Dowdy, A., Lane, T. P., & Hitchcock, S. (2023). Types of Severe Convective Wind Events in Eastern Australia. Monthly Weather Review, 151(2), 419–448. https://doi.org/10.1175/MWR-D-22-0096.1
