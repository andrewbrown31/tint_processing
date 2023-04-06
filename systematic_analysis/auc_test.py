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

def skill_test(it):

    scw,null,v = it
    temp = pd.concat([scw, null], axis=0).dropna()
    score = [roc_auc_score(temp["scw"],temp[v]), roc_auc_score(temp["scw"]*-1,temp[v])]

    return np.max(score)

def resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, metric, N, var_list, n_samples):

    output_skill = pd.DataFrame(columns=var_list)
    output_skill1 = pd.DataFrame(columns=var_list)
    output_skill2 = pd.DataFrame(columns=var_list)
    output_skill3 = pd.DataFrame(columns=var_list)

    pool = multiprocessing.Pool(16)

    for v in tqdm.tqdm(var_list):
        scw_resamp = [df_scw[[v,"scw"]].iloc[np.random.randint(0,df_scw.shape[0],df_scw.shape[0])] for X in np.arange(N)]
        null_resamp = [df_null[[v,"scw"]].iloc[np.random.randint(0,df_null.shape[0],df_null.shape[0])] for X in np.arange(N)]
        res = pool.map(skill_test,zip(scw_resamp,null_resamp,[v]*N))
        temp_tss = [res[i] for i in np.arange(len(res))]

        scw_resamp = [df_scw1[[v,"scw"]].iloc[np.random.randint(0,df_scw1.shape[0],df_scw1.shape[0])] for X in np.arange(N)]
        null_resamp = [df_null1[[v,"scw"]].iloc[np.random.randint(0,df_null1.shape[0],df_null1.shape[0])] for X in np.arange(N)]
        res = pool.map(skill_test,zip(scw_resamp,null_resamp,[v]*N))
        temp_tss1 = [res[i] for i in np.arange(len(res))]

        scw_resamp = [df_scw2[[v,"scw"]].iloc[np.random.randint(0,df_scw2.shape[0],df_scw2.shape[0])] for X in np.arange(N)]
        null_resamp = [df_null2[[v,"scw"]].iloc[np.random.randint(0,df_null2.shape[0],df_null2.shape[0])] for X in np.arange(N)]
        res = pool.map(skill_test,zip(scw_resamp,null_resamp,[v]*N))
        temp_tss2 = [res[i] for i in np.arange(len(res))]

        scw_resamp = [df_scw3[[v,"scw"]].iloc[np.random.randint(0,df_scw3.shape[0],df_scw3.shape[0])] for X in np.arange(N)]
        null_resamp = [df_null3[[v,"scw"]].iloc[np.random.randint(0,df_null3.shape[0],df_null3.shape[0])] for X in np.arange(N)]
        res = pool.map(skill_test,zip(scw_resamp,null_resamp,[v]*N))
        temp_tss3 = [res[i] for i in np.arange(len(res))]

        output_skill[v] = temp_tss
        output_skill1[v] = temp_tss1
        output_skill2[v] = temp_tss2
        output_skill3[v] = temp_tss3
        
    return output_skill, output_skill1, output_skill2, output_skill3

if __name__ == "__main__":

	#Load SCW/null information (hourly)
	rids = ["2","66","69","70","71","64","8","72","75","19","73","78","49","4","40","48","68","63","76","77"]
	#rids = ["2"]
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
	test_vars = ["wg10","bdsd"]
	
	#For now drop "t500". Not important anyway, but is not in the files for 2019-2020, so causes script to fail.
	test_vars = list(np.array(test_vars)[np.in1d(test_vars,"t500",invert=True)])
    
	n_samples = None #(This is how many null samples to use each bootstrap)
	auc, auc1, auc2, auc3 = resample_test(df_scw, df_scw1, df_scw2, df_scw3, df_null, df_null1, df_null2, df_null3, "AUC", N, test_vars, n_samples)
	auc_full = pd.DataFrame([skill_test([df_scw[[v,"scw"]],df_null[[v,"scw"]],v]) for v in test_vars],index=test_vars,columns=["auc"])
	auc_full1 = pd.DataFrame([skill_test([df_scw1[[v,"scw"]],df_null1[[v,"scw"]],v]) for v in test_vars],index=test_vars,columns=["auc"])
	auc_full2 = pd.DataFrame([skill_test([df_scw2[[v,"scw"]],df_null2[[v,"scw"]],v]) for v in test_vars],index=test_vars,columns=["auc"])
	auc_full3 = pd.DataFrame([skill_test([df_scw3[[v,"scw"]],df_null3[[v,"scw"]],v]) for v in test_vars],index=test_vars,columns=["auc"])

	#Calculate the same TSS and CSI for 2019-20. This is done for cross-validation of the BDSD
	auc_cv,_,_,_ = resample_test(df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019], 
		 df_scw1, 
		 df_scw2, 
		 df_scw3, 
		 df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019], 
		 df_null1, 
		 df_null2, 
		 df_null3, "AUC", N, ["bdsd"], n_samples)
	auc_full_cv = pd.DataFrame([skill_test(\
					[df_scw[pd.DatetimeIndex(df_scw.dt_utc).year>=2019][[v,"scw"]],\
					df_null[pd.DatetimeIndex(df_null.dt_utc).year>=2019][[v,"scw"]],v]) for v in ["bdsd"]],index=["bdsd"],columns=["auc"])

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
