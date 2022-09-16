from skill_test import *

if __name__ == "__main__":

	#Load SCW/null information (hourly)
	#melb_scw, melb_null = load_scws("2")
	#bris_scw, bris_null = load_scws("66")
	#namoi_scw, namoi_null = load_scws("69")
	#perth_scw, perth_null = load_scws("70")
	#syd_scw, syd_null = load_scws("71")
	#df_scw = pd.concat([melb_scw, bris_scw, namoi_scw, perth_scw, syd_scw], axis=0)
	#df_null = pd.concat([melb_null, bris_null, namoi_null, perth_null, syd_null], axis=0).query("(in10km==1)")
	rids = ["68","64","8","72","75","19","73","78","49","4","40","48","2","66","69","70","71"]
	df_scw = pd.DataFrame()
	df_null = pd.DataFrame()
	for rid in rids:
	    df_scw = pd.concat([df_scw,remove_suspect_gusts(load_scws(rid)).query("in10km==1")],axis=0)
	    df_null = pd.concat([df_null,load_nulls(rid).query("in10km==1")],axis=0)    

	#Separate the combined dataframe out into environmental clusters
	#Also create two "null" datasets. One for all non-SCW occurrences, one for all non-SCW occurences with a radar object within 10 km
	df_scw1 = df_scw.query("cluster==1")
	df_scw2 = df_scw.query("cluster==2")
	df_scw3 = df_scw.query("cluster==0")
	df_null1 = df_null.query("(cluster==1)")
	df_null2 = df_null.query("(cluster==2)")
	df_null3 = df_null.query("(cluster==0)")

	#Calculate a range of TSS, and CSI values based on N bootstrapping. Note that the bootstrap resampling here is balanced based on under-sampling the null dataset.
	N=1000
	#test_vars = ["wg10","bdsd","gustex","eff_sherb","scp","t_totals"]
	#test_vars = ["wg10","bdsd"]
	test_vars = list(df_scw.columns[43:-8])
	
	#For now drop "t500". Not important anyway, but is not in the files for 2019-2020, so causes script to fail.
	test_vars = list(np.array(test_vars)[np.in1d(test_vars,"t500",invert=True)])

	tss, tss_thresh, tss1, tss_thresh1, tss2, tss_thresh2, tss3, tss_thresh3 = resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, "TSS", N, test_vars)
	csi, csi_thresh, csi1, csi_thresh1, csi2, csi_thresh2, csi3, csi_thresh3 = resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, "CSI", N, test_vars)
	auc, _, auc1, _, auc2, _, auc3, _ = resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, "AUC", N, test_vars)

	#Calculate the same TSS and CSI for 2019-20. This is done for cross-validation of the BDSD
	tss_cv, tss_thresh_cv,_,_,_,_,_,_ = resample_test(df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019],
		 df_scw1,
		 df_scw2, 
		 df_scw3, 
		 df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019], 
		 df_null1, 
		 df_null2, 
		 df_null3, "TSS", N, test_vars)
	csi_cv, csi_thresh_cv,_,_,_,_,_,_ = resample_test(df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019], 
		 df_scw1, 
		 df_scw2, 
		 df_scw3, 
		 df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019], 
		 df_null1, 
		 df_null2, 
		 df_null3, "CSI", N, test_vars)
	auc_cv, auc_thresh_cv,_,_,_,_,_,_ = resample_test(df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019], 
		 df_scw1, 
		 df_scw2, 
		 df_scw3, 
		 df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019], 
		 df_null1, 
		 df_null2, 
		 df_null3, "AUC", N, test_vars)

	#Save the TSS, CSI dataframes.
	tss.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_clusterall_in10km.csv",index=False)
	tss1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_cluster1_in10km.csv",index=False)
	tss2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_cluster2_in10km.csv",index=False)
	tss3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_cluster3_in10km.csv",index=False)
	tss_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_clusterall_cv_in10km.csv",index=False)
	csi.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_clusterall_in10km.csv",index=False)
	csi1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_cluster1_in10km.csv",index=False)
	csi2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_cluster2_in10km.csv",index=False)
	csi3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_cluster3_in10km.csv",index=False)
	csi_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_clusterall_cv_in10km.csv",index=False)
	auc.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_clusterall_in10km.csv",index=False)
	auc1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_cluster1_in10km.csv",index=False)
	auc2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_cluster2_in10km.csv",index=False)
	auc3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_cluster3_in10km.csv",index=False)
	auc_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_clusterall_cv_in10km.csv",index=False)

	#Save the optimal threshold dataframes for TSS and CSI
	tss_thresh.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_clusterall_in10km.csv",index=False)
	tss_thresh1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_cluster1_in10km.csv",index=False)
	tss_thresh2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_cluster2_in10km.csv",index=False)
	tss_thresh3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_cluster3_in10km.csv",index=False)
	tss_thresh_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_clusterall_cv_in10km.csv",index=False)
	csi_thresh.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_clusterall_in10km.csv",index=False)
	csi_thresh1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_cluster1_in10km.csv",index=False)
	csi_thresh2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_cluster2_in10km.csv",index=False)
	csi_thresh3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_cluster3_in10km.csv",index=False)
	csi_thresh_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_clusterall_cv_in10km.csv",index=False)
