import multiprocessing
from sklearn.metrics import roc_auc_score
from sklearn.utils import resample
import pandas as pd
import numpy as np
import glob
import datetime as dt
import tqdm

def remove_suspect_gusts(df):
    dts = ["2010-12-14 07:03:00","2011-01-11 03:49:00","2015-12-15 23:33:00","2020-02-09 01:00:00","2020-02-09 03:18:00","2020-05-25 06:11:00",
          "2012-11-02 18:58:00","2012-12-20 21:19:00","2012-12-15 13:00:00","2012-12-29 16:15:00","2012-12-30 06:25:00","2012-12-30 18:01:00","2013-01-02 08:15:00",
          "2013-01-05 03:36:00","2013-01-12 15:22:00","2013-02-11 07:56:00"]
    return df[np.in1d(df.dt_utc,dts,invert=True)]

def load_scws(rid):

    df1 = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_scw_envs_df.csv")
    df1["rid"] = rid  
    df1["scw"] = 1
    
    return df1

def load_nulls(rid):
    
    df2 = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_non_scw_envs_df.csv")
    df2["rid"] = rid   
    df2["scw"] = 0
    
    return df2

#def load_scws(rid):
#    print("loading "+rid+"...")
#    df1 = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_scw_envs_df.csv")
#    df2 = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_non_scw_envs_df.csv")
#    df1["rid"]=rid
#    df2["rid"]=rid
#    df1["scw"]=1
#    df2["scw"]=0
#    return df1, df2

def skill(events, nulls, t, v, scores="TSS"):
    
    hits = (events[v]>t).sum()
    misses = (events[v]<=t).sum()    
    fa = (nulls[v]>t).sum()
    cn = (nulls[v]<=t).sum()
        
    if scores=="TSS":
        return (( (hits) / (hits+misses) )  - ( (fa) / (fa+cn) ))
    elif scores=="CSI":
        return ((hits)  / (hits+misses+fa))
    elif scores=="HSS":
        if hits / (hits + misses) > 0.66:
            return (( 2*(hits*cn - misses*fa) ) / ( misses*misses + fa*fa + 2*hits*cn + (misses + fa) * (hits + cn) ))
        else:
            return (0)

def skill_test(scw,null,v,scores="TSS",auc_greater=True):
    if scores != "AUC":
        x = np.linspace(0,scw[v].quantile(1),100)
        score = [skill(scw,null,i,v,scores=scores) for i in x]
    elif scores == "AUC":
        temp = pd.concat([scw[[v,"scw"]], null[[v,"scw"]]], axis=0).dropna()
        if auc_greater:
            score = [roc_auc_score(temp["scw"],temp[v])]
        else:
            score = [roc_auc_score(temp["scw"]*-1,temp[v])]
        x = [np.nan]
    else:
        raise ValueError()

    return np.max(score), x[np.argmax(score)]

def resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, metric, N, var_list, n_samples):

    output_skill = pd.DataFrame(columns=var_list)
    output_thresh = pd.DataFrame(columns=var_list)    
    output_skill1 = pd.DataFrame(columns=var_list)
    output_thresh1 = pd.DataFrame(columns=var_list)
    output_skill2 = pd.DataFrame(columns=var_list)
    output_thresh2 = pd.DataFrame(columns=var_list)
    output_skill3 = pd.DataFrame(columns=var_list)
    output_thresh3 = pd.DataFrame(columns=var_list)

    for v in tqdm.tqdm(var_list):
        temp_tss = []
        temp_t = []        
        temp_tss1 = []
        temp_t1 = []
        temp_tss2 = []
        temp_t2 = []
        temp_tss3 = []
        temp_t3 = []    
        for n in (np.arange(N)):
            resampled_null = resample(df_null[[v,"scw"]],replace=True,n_samples=int(df_null.shape[0] * n_samples),random_state=n)
            resampled_scw = resample(df_scw[[v,"scw"]],replace=True,n_samples=df_scw.shape[0],random_state=n)
            auc_greater = (resampled_scw[v].mean() >= resampled_null[v].mean())
            tss, t = skill_test(resampled_scw,resampled_null,v,scores=metric,auc_greater=auc_greater)
            temp_tss.append(tss)
            temp_t.append(t)            
            
            resampled_null = resample(df_null1[[v,"scw"]],replace=True,n_samples=int(df_null1.shape[0] * n_samples),random_state=n)
            resampled_scw = resample(df_scw1[[v,"scw"]],replace=True,n_samples=df_scw1.shape[0],random_state=n)
            auc_greater = (resampled_scw[v].mean() >= resampled_null[v].mean())
            tss, t = skill_test(resampled_scw,resampled_null,v,scores=metric,auc_greater=auc_greater)
            temp_tss1.append(tss)
            temp_t1.append(t)     

            resampled_null = resample(df_null2[[v,"scw"]],replace=True,n_samples=int(df_null2.shape[0] * n_samples),random_state=n)
            resampled_scw = resample(df_scw2[[v,"scw"]],replace=True,n_samples=df_scw2.shape[0],random_state=n)
            auc_greater = (resampled_scw[v].mean() >= resampled_null[v].mean())
            tss, t = skill_test(resampled_scw,resampled_null,v,scores=metric,auc_greater=auc_greater)
            temp_tss2.append(tss)
            temp_t2.append(t)     

            resampled_null = resample(df_null3[[v,"scw"]],replace=True,n_samples=int(df_null3.shape[0] * n_samples),random_state=n)
            resampled_scw = resample(df_scw3[[v,"scw"]],replace=True,n_samples=df_scw3.shape[0],random_state=n)
            auc_greater = (resampled_scw[v].mean() >= resampled_null[v].mean())
            tss, t = skill_test(resampled_scw,resampled_null,v,scores=metric,auc_greater=auc_greater)
            temp_tss3.append(tss)
            temp_t3.append(t)             

        output_skill[v] = temp_tss
        output_thresh[v] = temp_t            
        output_skill1[v] = temp_tss1
        output_thresh1[v] = temp_t1
        output_skill2[v] = temp_tss2
        output_thresh2[v] = temp_t2
        output_skill3[v] = temp_tss3
        output_thresh3[v] = temp_t3  
        
    return output_skill, output_thresh, output_skill1, output_thresh1, output_skill2, output_thresh2, output_skill3, output_thresh3 

if __name__ == "__main__":

	#Load SCW/null information (hourly)
	rids = ["2","66","69","70","71","64","8","72","75","19","73","78","49","4","40","48","68","63","76","77"]
	#rids = ["2","66","69","70","71"]
	df_scw = pd.DataFrame()
	df_null = pd.DataFrame()
	for rid in rids:
	    print(rid)
	    df_scw = pd.concat([df_scw,remove_suspect_gusts(load_scws(rid))],axis=0)
	    df_null = pd.concat([df_null,load_nulls(rid)],axis=0)    

	#Separate the combined dataframe out into environmental clusters
	df_scw1 = df_scw.query("cluster==1")
	df_scw2 = df_scw.query("cluster==2")
	df_scw3 = df_scw.query("cluster==0")
	df_null1 = df_null.query("cluster==1")
	df_null2 = df_null.query("cluster==2")
	df_null3 = df_null.query("cluster==0")

	#Calculate a range of TSS, and CSI values based on N bootstrapping. Note that the bootstrap resampling here is balanced based on under-sampling the null dataset.
	N=1000
	#test_vars = ["wg10","bdsd"]
	test_vars = list(df_scw.columns[43:-12])
	
	#For now drop "t500". Not important anyway, but is not in the files for 2019-2020, so causes script to fail.
	test_vars = list(np.array(test_vars)[np.in1d(test_vars,"t500",invert=True)])
    
	n_samples = 0.1 #(This is how many null samples to use each bootstrap, in fractions)
	#tss, tss_thresh, tss1, tss_thresh1, tss2, tss_thresh2, tss3, tss_thresh3 = resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, "TSS", N, test_vars, n_samples)
	#csi, csi_thresh, csi1, csi_thresh1, csi2, csi_thresh2, csi3, csi_thresh3 = resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, "CSI", N, test_vars, n_samples)
	auc, _, auc1, _, auc2, _, auc3, _ = resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, "AUC", N, test_vars, n_samples)
	auc_full = pd.DataFrame([skill_test(df_scw,df_null,v,"AUC",auc_greater=(df_scw[v].mean() >= df_null[v].mean()))[0] for v in test_vars],\
				index=test_vars,columns=["auc"])
	auc_full1 = pd.DataFrame([skill_test(df_scw1,df_null1,v,"AUC",auc_greater=(df_scw[v].mean() >= df_null[v].mean()))[0] for v in test_vars],\
				index=test_vars,columns=["auc"])
	auc_full2 = pd.DataFrame([skill_test(df_scw2,df_null2,v,"AUC",auc_greater=(df_scw[v].mean() >= df_null[v].mean()))[0] for v in test_vars],\
				index=test_vars,columns=["auc"])
	auc_full3 = pd.DataFrame([skill_test(df_scw3,df_null3,v,"AUC",auc_greater=(df_scw[v].mean() >= df_null[v].mean()))[0] for v in test_vars],\
				index=test_vars,columns=["auc"])

	#Calculate the same TSS and CSI for 2019-20. This is done for cross-validation of the BDSD
	#tss_cv, tss_thresh_cv,_,_,_,_,_,_ = resample_test(df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019],
	#	 df_scw1,
	#	 df_scw2, 
	#	 df_scw3, 
	#	 df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019], 
	#	 df_null1, 
	#	 df_null2, 
	#	 df_null3, "TSS", N, test_vars)
	#csi_cv, csi_thresh_cv,_,_,_,_,_,_ = resample_test(df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019], 
	#	 df_scw1, 
	#	 df_scw2, 
	#	 df_scw3, 
	#	 df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019], 
	#	 df_null1, 
	#	 df_null2, 
	#	 df_null3, "CSI", N, test_vars)
	auc_cv, auc_thresh_cv,_,_,_,_,_,_ = resample_test(df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019], 
		 df_scw1, 
		 df_scw2, 
		 df_scw3, 
		 df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019], 
		 df_null1, 
		 df_null2, 
		 df_null3, "AUC", N, ["bdsd"], n_samples)
	auc_full_cv = pd.DataFrame(\
				    [skill_test(\
					    df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019],\
					    df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019],\
					    v,"AUC",\
					    auc_greater=(df_scw[v].mean() >= df_null[v].mean()))[0] for v in ["bdsd"]],\
				    index=["bdsd"],columns=["auc"])

	#Save the AUC dataframes.
	auc.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_clusterall.csv",index=False)
	auc1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_cluster1.csv",index=False)
	auc2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_cluster2.csv",index=False)
	auc3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_cluster3.csv",index=False)
	auc_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_era5_clusterall_cv.csv",index=False)

	auc_full.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_full_era5_clusterall.csv",index=True)
	auc_full1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_full_era5_cluster1.csv",index=True)
	auc_full2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_full_era5_cluster2.csv",index=True)
	auc_full3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_full_era5_cluster3.csv",index=True)
	auc_full_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/auc_full_era5_clusterall_cv.csv",index=True)

	#Save the optimal threshold dataframes for TSS and CSI
#	tss_thresh.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_clusterall.csv",index=False)
#	tss_thresh1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_cluster1.csv",index=False)
#	tss_thresh2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_cluster2.csv",index=False)
#	tss_thresh3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_cluster3.csv",index=False)
#	tss_thresh_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_thresh_era5_clusterall_cv.csv",index=False)
#	csi_thresh.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_clusterall.csv",index=False)
#	csi_thresh1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_cluster1.csv",index=False)
#	csi_thresh2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_cluster2.csv",index=False)
#	csi_thresh3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_cluster3.csv",index=False)
#	csi_thresh_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_thresh_era5_clusterall_cv.csv",index=False)
#
#	tss.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_clusterall.csv",index=False)
#	tss1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_cluster1.csv",index=False)
#	tss2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_cluster2.csv",index=False)
#	tss3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_cluster3.csv",index=False)
#	tss_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/tss_era5_clusterall_cv.csv",index=False)
#	csi.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_clusterall.csv",index=False)
#	csi1.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_cluster1.csv",index=False)
#	csi2.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_cluster2.csv",index=False)
#	csi3.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_cluster3.csv",index=False)
#	csi_cv.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/csi_era5_clusterall_cv.csv",index=False)
