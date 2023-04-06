from skill_test import *

def resample_test(df_scw, df_null,metric, N, var_list, n_samples):

    output_skill = pd.DataFrame(columns=var_list)
    output_thresh = pd.DataFrame(columns=var_list)    

    for v in tqdm.tqdm(var_list):
        temp_tss = []
        temp_t = []        
        for n in (np.arange(N)):
            resampled_null = resample(df_null[[v,"scw"]],replace=True,n_samples=int(df_null.shape[0] * n_samples),random_state=n)
            resampled_scw = resample(df_scw[[v,"scw"]],replace=True,n_samples=df_scw.shape[0],random_state=n)
            auc_greater = (resampled_scw[v].mean() >= resampled_null[v].mean())
            tss, t = skill_test(resampled_scw,resampled_null,v,scores=metric,auc_greater=auc_greater)
            temp_tss.append(tss)
            temp_t.append(t)            
            
        output_skill[v] = temp_tss
        output_thresh[v] = temp_t            
        
    return output_skill, output_thresh

def assign_storm_class(data):

    data["aspect_ratio"] = data.major_axis_length / data.minor_axis_length     
    #Linear
    data.loc[(data.aspect_ratio>=3) & (data.major_axis_length>=100),"class2"] = "Linear"
    #Non-linear
    data.loc[(data.aspect_ratio<3) & (data.major_axis_length>=100),"class2"] = "Non-linear"
    #Cellular
    data.loc[(data.local_max == 1),"class2"] = "Cellular"
    #Cluster of cells
    data.loc[(data.local_max>=2) & (data.major_axis_length<100),"class2"] = "Cell cluster"
    #Supercell
    data.loc[(data.max_alt>=7) & (data.azi_shear60>4) & ((data.aspect_ratio<3) | (data.major_axis_length<100)),"class2"] = "Supercellular"
    #Linear hybrid
    data.loc[(data.max_alt>=7) & (data.azi_shear60>4) & ((data.major_axis_length>=100)),"class2"] = "Embedded supercell"
    
    return data

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
	    print(rid)
	    df_scw = pd.concat([df_scw,remove_suspect_gusts(load_scws(rid)).query("in10km==1")],axis=0)
	    df_null = pd.concat([df_null,load_nulls(rid).query("in10km==1")],axis=0)    

	#Separate the combined dataframe out into storm classes
	#Also create two "null" datasets. One for all non-SCW occurrences, one for all non-SCW occurences with a radar object within 10 km
	df_scw = assign_storm_class(df_scw)
	df_null = assign_storm_class(df_null)
	df_scw_linear = df_scw[df_scw["class2"]=="Linear"]
	df_scw_nonlinear = df_scw[df_scw["class2"]=="Non-linear"]
	df_scw_cell = df_scw[df_scw["class2"]=="Cellular"]
	df_scw_cellcluster = df_scw[df_scw["class2"]=="Cell cluster"]
	df_scw_supercell = df_scw[df_scw["class2"]=="Supercellular"]
	df_scw_embeddedsup = df_scw[df_scw["class2"]=="Embedded supercell"]

	df_null_linear = df_null[df_null["class2"]=="Linear"]
	df_null_nonlinear = df_null[df_null["class2"]=="Non-linear"]
	df_null_cell = df_null[df_null["class2"]=="Cellular"]
	df_null_cellcluster = df_null[df_null["class2"]=="Cell cluster"]
	df_null_supercell = df_null[df_null["class2"]=="Supercellular"]
	df_null_embeddedsup = df_null[df_null["class2"]=="Embedded supercell"]

	#Calculate a range of TSS, and CSI values based on N bootstrapping. Note that the bootstrap resampling here is balanced based on under-sampling the null dataset.
	N=1000
	#test_vars = ["rhmin01","bdsd"]
	test_vars = list(df_scw.columns[43:-12])
	
	#For now drop "t500". Not important anyway, but is not in the files for 2019-2020, so causes script to fail.
	test_vars = list(np.array(test_vars)[np.in1d(test_vars,"t500",invert=True)])


	n_samples=0.1
	for score in ["auc"]:
		for temp_df_null, temp_df_scw, temp_class in zip((df_null_linear,df_null_nonlinear,df_null_cell,df_null_cellcluster,df_null_supercell,df_null_embeddedsup),\
						    (df_scw_linear,df_scw_nonlinear,df_scw_cell,df_scw_cellcluster,df_scw_supercell,df_scw_embeddedsup),\
						    ("linear","nonlinear","cell","cellcluster","supercell","embeddedsup")):

			temp_score, temp_score_thresh = resample_test(temp_df_scw, temp_df_null, score.upper(), N, test_vars, n_samples)
			temp_score_cv, temp_score_thresh_cv = resample_test(temp_df_scw[pd.DatetimeIndex(temp_df_scw.dt_utc).year>=2019], temp_df_null[pd.DatetimeIndex(temp_df_null.dt_utc).year>=2019], score.upper(), N, ["bdsd"], n_samples)

			temp_score.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/"+score+"_era5_"+temp_class+".csv",index=False)
			temp_score_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/"+score+"_era5_"+temp_class+"_cv.csv",index=False)

			if score == "auc":
				auc_full = pd.DataFrame([skill_test(temp_df_scw,temp_df_null,v,"AUC",auc_greater=(temp_df_scw[v].mean() >= temp_df_null[v].mean()))[0] for v in test_vars],index=test_vars,columns=["auc"]) 
				auc_full_cv = pd.DataFrame([skill_test(temp_df_scw[pd.DatetimeIndex(temp_df_scw.dt_utc).year>=2019],temp_df_null[pd.DatetimeIndex(temp_df_null.dt_utc).year>=2019],v,"AUC",auc_greater=(temp_df_scw[v].mean() >= temp_df_null[v].mean()))[0] for v in test_vars],index=test_vars,columns=["auc"])
				auc_full.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/"+score+"_full_era5_"+temp_class+".csv",index=True)
				auc_full_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/"+score+"_full_era5_"+temp_class+"_cv.csv",index=True)

			#if score != "auc":
			#	temp_score_thresh.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/"+score+"_thresh_era5_"+temp_class+".csv",index=False)
			#	temp_score_thresh_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/"+score+"_thresh_era5_"+temp_class+"_cv.csv",index=False)


