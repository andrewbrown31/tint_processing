# Log

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
