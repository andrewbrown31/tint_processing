# Log

This log details the construction of results for Brown et al. (https://journals.ametsoc.org/view/journals/mwre/151/2/MWR-D-22-0096.1.xml), with figure numbers referenced below from that study. It is noted that this is a working repository, and may be updated after this publication (with the version at submission available [here](https://github.com/andrewbrown31/tint_processing/tree/4e5fa9a74004f403fe9b56f598076a3cdf72946a)).

### Case selection
A list of potential SCW cases is attained from [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4448518.svg)](https://doi.org/10.5281/zenodo.4448518), and [TINT/tobac tracking software](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/case_driver.py) is applied to each case. Note that these are slightly modified versions of [TINT](https://github.com/andrewbrown31/TINT) and [tobac](https://github.com/andrewbrown31/tobac/tree/andrewbrown31). Code to run TINT is [here](https://github.com/andrewbrown31/tint_processing/blob/main/tint_driver.py), and is postprocessed [here](https://github.com/andrewbrown31/tint_processing/blob/main/post_process_tracks.py). After this, cases are selected for analysis using [generate_case_list.ipynb](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/generate_case_list.ipynb). This also creates Fig. 2.

### High-resolution observations
An analysis of observational data (wind gust, peak-to-mean gust ratio, lightning, and precipitation) is prepared [here](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/one_min_obs_save.ipynb), and plotted [here](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/one_min_obs_2.ipynb) for Fig. 3.

### Radar images
For each case, radar images are [plotted](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/cape_shear_radar_all_30dbz.ipynb), resulting in Figs. 4-7. For analysing potential supercells, we also look at [doppler velocity signatures](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/plot_supercells.ipynb) as part of the supplementry material.

### Environmental analysis
For both ERA5 and BARRA, convective diagnostics over all of Australia have been calculated using [this code](https://github.com/andrewbrown31/SCW-analysis/blob/master/wrf_non_parallel.py), and have been extracted at point locations for ERA5 for climatological analysis in Figs 8 and 9 using [this code](https://github.com/andrewbrown31/SCW-analysis/blob/master/era5_read.py#L584), and for BARRA using [this code](https://github.com/andrewbrown31/SCW-analysis/blob/master/barra_read.py#L611). Convective diagnostics are plotted for each SCW case, over the climatological distribution [here](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/cape_shear_values.ipynb). 

### Synoptic analysis
For ERA5, diagnostics associated with synoptic-scale systems for 2005-2018 are calculate [here](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/synoptic_objective.py), and plotted for each case against the climatological distribution [here](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/synoptic_objective.ipynb) for Fig. 10, as well as maps are for supplementry material.

### Clustering analysis
Firstly, TINT-derived radar statistics (see "Case selection" section of paper) are extracted and saved for each SCW case, in [this notebook](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/scw_cases_tint_stats.ipynb). Next, k-means clustering is performed [here](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/kmeans_and_cluster_eval.ipynb), and radar statistics and environmental conditions for each cluster is plotted (Figs. 11 and 12). The clustering and radar analysis are brought together in [this notebook](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/output_stats_table.ipynb) to create Table 1. Finally composite soundings for each cluster are plotted [here](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/composite_soundings.ipynb), as well as individually for each case.

### Appendices
#### Azimuthal shear
[Shaded time-height plot of azimuthal shear](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/scw_cases_tint_stats.ipynb) for cases where azimuthal shear is greater than 0.004 s^-1
#### Storm statistics
[Distribution of maximum altitude and azimuthal shear over cases](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/scw_cases_tint_stats.ipynb)
#### Clustering evaluation
[Rand scores, silhouette score, and clustering from BARRA](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/kmeans_and_cluster_eval.ipynb)
#### Sounding variability
[Soundings for each case from ERA5](https://github.com/andrewbrown31/tint_processing/blob/main/auto_case_driver/composite_soundings.ipynb)

