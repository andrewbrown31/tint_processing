import argparse
import pandas as pd
import numpy as np
import glob
import datetime as dt
import tqdm
from statsmodels.tools.tools import add_constant
from statsmodels.discrete.discrete_model import Logit
import warnings
from sklearn.linear_model import LogisticRegression
import multiprocessing
from statsmodels.tools.tools import add_constant
from statsmodels.discrete.discrete_model import Logit
import warnings
import itertools
from event_analysis import optimise_pss, pss
from merge_data import get_env_clusters

def load_scws(rid):
    print("loading "+rid+"...")
    df1 = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_scw_envs_df.csv")
    
    df1["cluster_new"] = df1.cluster.map({0:2,2:1,1:0})
    df1["rid"] = rid  
    df1["scw"] = 1
    
    return df1

def load_nulls(rid):
    
    df2 = pd.read_csv("/g/data/eg3/ab4502/ExtremeWind/points/"+rid+"_non_scw_envs_df.csv")
    
    df2["cluster_new"] = df2.cluster.map({0:2,2:1,1:0})
    df2["rid"] = rid   
    df2["scw"] = 0
    
    return df2

def remove_suspect_gusts(df):
    dts = ["2010-12-14 07:03:00","2011-01-11 03:49:00","2015-12-15 23:33:00","2020-02-09 01:00:00","2020-02-09 03:18:00","2020-05-25 06:11:00",
          "2012-11-02 18:58:00","2012-12-20 21:19:00","2012-12-15 13:00:00","2012-12-29 16:15:00","2012-12-30 06:25:00","2012-12-30 18:01:00","2013-01-02 08:15:00",
          "2013-01-05 03:36:00","2013-01-12 15:22:00","2013-02-11 07:56:00"]
    return df[np.in1d(df.dt_utc,dts,invert=True)]

def assign_storm_class(data):

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

def resample_events(df, event, N, M, conserve_prop=True, fixed_ratio=None): 
                
    ratio = round(df.shape[0] / df[event].sum())
    event_inds = df[df[event]==1].index.values
    non_inds = df[df[event]==0].index.values 
    rand_event_inds = []; rand_non_event_inds = []
    for i in np.arange(N):
        rand_event_inds.append(event_inds[np.random.randint(0, high=len(event_inds), size=M)])
        if conserve_prop:
            rand_non_event_inds.append(non_inds[np.random.randint(0, high=len(non_inds), size=int(M*ratio))])
        else:
            rand_non_event_inds.append(non_inds[np.random.randint(0, high=len(non_inds), size=int(round((df[event]==0).sum()*fixed_ratio)))])
    return [rand_event_inds, rand_non_event_inds]

def fwd_selection(cluster, N):

	#Note that N is the number of times the HSS is calculated using bootstrapping

        model = "era5"
        pval_choice = False
        event = "is_conv_aws"
        seed = 0; np.random.seed(seed=seed)

        print("INFO: Forward selection of variables for cluster "+str(cluster))

        #Test predictors are all "variables" available
        preds = np.array(['ml_cape', 'mu_cape', 'sb_cape',\
             'ml_cin', 'sb_cin', 'mu_cin', 'ml_lcl', 'mu_lcl', 'sb_lcl', 'eff_cape',\
             'eff_cin', 'eff_lcl', 'lr01', 'lr03', 'lr13', 'lr36', 'lr24', 'lr_freezing',\
             'lr_subcloud', 'qmean01', 'qmean03', 'qmean06', 'qmeansubcloud', 'q_melting',\
             'q1', 'q3', 'q6', 'rhmin01', 'rhmin03', 'rhmin13', 'rhminsubcloud', 'tei', 'wbz',\
             'mhgt', 'mu_el', 'ml_el', 'sb_el', 'eff_el', 'pwat', \
             'te_diff', 'dpd850', 'dpd700', 'dcape', 'ddraft_temp', 'sfc_thetae',\
             'srhe_left', 'srh01_left', 'srh03_left', 'srh06_left', 'ebwd', 's010', 's06',\
             's03', 's01', 's13', 's36', 'scld', 'U500', 'U10', 'U1', 'U3', 'U6', 'Ust_left',\
             'Usr01_left', 'Usr03_left', 'Usr06_left', 'Uwindinf', 'Umeanwindinf',\
             'Umean800_600', 'Umean06', 'Umean01', 'Umean03'])

	#Load diagnostics/events
        if model == "era5":
                pss_df, df_aws, df_sta = optimise_pss("/g/data/eg3/ab4502/ExtremeWind/points/"+\
                        "era5_allvars_v3_2005_2018.pkl", T=1000, compute=False, l_thresh=2,\
                        is_pss="hss", model_name="era5_v5")
        elif model == "barra":
                pss_df, df_aws, df_sta = optimise_pss("/g/data/eg3/ab4502/ExtremeWind/points/"+\
                        "barra_allvars_v3_2005_2018.pkl", T=1000, compute=False, l_thresh=2,\
                        is_pss="hss", model_name="barra_fc_v5")
        else:
                raise ValueError("Invalid model name")

        #Set the correct dataframe based on event type 
        if event=="is_sta":
                df = df_sta.reset_index().drop(columns="index")
        elif event=="is_conv_aws":
                df = df_aws.reset_index().drop(columns="index")

	#Load clustering classification model saved by ~/working/observations/tint_processing/auto_case_driver/kmeans_and_cluster_eval.ipynb
        cluster_mod, cluster_input = get_env_clusters()
        input_df = (df[["s06","qmean01","lr13","Umean06"]]\
		   - cluster_input.min(axis=0))\
	    / (cluster_input.max(axis=0) - \
	       cluster_input.min(axis=0))
        df["cluster"] = cluster_mod.predict(input_df)

	#Subset based on cluster option
        if cluster == "all":
            pass
        else:
            df = df[df["cluster"]==int(cluster)]

        #Initialise things
        warnings.simplefilter("ignore")
        logit = LogisticRegression(class_weight="balanced", solver="liblinear",max_iter=1000)
        pool = multiprocessing.Pool()

        #Train model with statsmodel
        mod = Logit(df[event],add_constant(df[preds])["const"]).fit()

        #Train model with sklearn and get HSS
        logit_mod = logit.fit(add_constant(df[preds])[["const"]], df[event])
        df["predict"] = logit_mod.predict_proba(add_constant(df[preds])[["const"]])[:,1]
        iterable = itertools.product(np.linspace(0,1,100), [df[["predict", event]]], ["predict"], [event], ["hss"], [0.66])
        res2 = pool.map(pss, iterable)
        current_hss = np.max([res2[i][0] for i in np.arange(len(res2))])

        statsmod_preds = []
        statsmod_hss = []
        alph = 0.05
        is_pval = True          #Keep track of overall progress (i.e. whether or not to continue)
        while is_pval:
                pval_ls = []            #Keep track of the p-value of each individual added param
                is_pval_ls = []         #Keep track of if all coefficients within the added-parameter model are significant
                hss_ls = []             #Keep track of the HSS
                hss_thresh = []         #Keep track of the HSS thresh
                for p in tqdm.tqdm(preds):
                        if p not in statsmod_preds:
                                mod = Logit(df[event],add_constant(df[statsmod_preds + [p]])).fit(disp=False)
                                param_pval = mod.summary2().tables[1].loc[p, "P>|z|"]
                                pval = mod.summary2().tables[1].loc[:, "P>|z|"]
                                pval_ls.append(param_pval)
                                is_pval_ls.append(all(pval <= alph))
                                if not pval_choice:
                                        logit_mod = logit.fit(df[statsmod_preds + [p]], df[event])
                                        df["predict"] = logit_mod.predict_proba(df[statsmod_preds + [p]])[:,1]
                                        iterable = itertools.product(np.linspace(0,1,100), [df[["predict", event]]], ["predict"], [event], ["hss"], [0.66])
                                        res2 = pool.map(pss, iterable)
                                        hss_ls.append(np.max([res2[i][0] for i in np.arange(len(res2))]))
                        else:
                                pval_ls.append(1)
                                is_pval_ls.append(False)
                                hss_ls.append(0)
                #If using pvalues to decide which variable to add, then chose the one with the minimum pvalue
                if pval_choice:
                        if (min(pval_ls) <= alph) & (is_pval_ls[np.argmin(pval_ls)]):
                                is_pval = True
                                statsmod_preds.append(preds[np.argmin(pval_ls)])
                                print("INFO: There are "+str(np.sum(is_pval_ls))+" new models which add value based on p-value")
                                print("INFO: The min p-value is "+str(np.min(pval_ls))+" based on "+preds[np.argmin(pval_ls)])
                        else:
                                print("INFO: Stopping at "+str(len(statsmod_preds))+" variables")
                                is_pval = False
                #Else, use the optimised HSS to decide (note that a different module is used to fit the model)
                else:
                        if any((hss_ls > current_hss) & (is_pval_ls)):      #If there is at least one predictor with a higher HSS and significant coef.
                                for z in np.arange(len(is_pval_ls)):        #Remove variables which add HSS but don't have a significant coef.
                                        if not is_pval_ls[z]:
                                                hss_ls[z] = 0
                                #Calculate bootstrapped HSS, and get the upper 5%
                                if len(statsmod_preds) >= 1:
                                        print("Bootstrapping the HSS to get confidence...")
                                        logit_mod = logit.fit(df[statsmod_preds], df[event])
                                        df["predict"] = logit_mod.predict_proba(df[statsmod_preds])[:,1]
                                        iterable = itertools.product(np.linspace(0,1,100), [df[["predict", event]]], ["predict"], [event], ["hss"], [0.66])
                                        res2 = pool.map(pss, iterable)
                                        hss_temp = [res2[i][0] for i in np.arange(len(res2))]
                                        hss_thresh = [res2[i][1] for i in np.arange(len(res2))][np.argmax(hss_temp)]
                                        hss_boot = []
                                        event_ind, non_inds = resample_events(df, event, N, df[event].sum())
                                        for i in tqdm.tqdm(np.arange(N)):
                                                iterable = itertools.product([hss_thresh],\
                                                        [df.loc[np.append(event_ind[i], non_inds[i])][["predict", event]]],\
                                                        ["predict"], [event], ["hss"], [0.66])
                                                res2 = pool.map(pss, iterable)
                                                hss_boot.append(res2[0][0])
                                else:
                                        hss_boot = [0]
                                #If the hss of the most skillful predictor is greater than the 95th percentile, then select the predictor and keep going.
                                #Else, halt the proceudre
                                if np.max(hss_ls) >= np.percentile(hss_boot, 95):
                                        is_pval = True
                                        statsmod_preds.append(preds[np.argmax(hss_ls)])
                                        statsmod_hss.append(np.max(hss_ls))
                                        print("INFO: There are "+str(np.sum((hss_ls > np.percentile(hss_boot, 95)) &\
                                                (is_pval_ls)))+" new models which add value based on HSS and p-values")
                                        print("INFO: The max HSS is "+str(np.max(hss_ls))+" based on "+preds[np.argmax(hss_ls)])
                                        current_hss = max(hss_ls)
                                else:
                                        is_pval = False
                                        print("INFO: Stopping at "+str(len(statsmod_preds))+" variables")
                        else:
                                is_pval = False
                                print("INFO: Stopping at "+str(len(statsmod_preds))+" variables")

	#Now save the output
        logit_mod = logit.fit(df[statsmod_preds], df[event])
        mod = Logit(df[event],add_constant(df[statsmod_preds])).fit(disp=False)
        pval = mod.summary2().tables[1].loc[:, "P>|z|"]
        out_df = pd.DataFrame({"coef":np.squeeze(logit_mod.coef_), "non_cv_hss":statsmod_hss}, index=statsmod_preds)
        out_df.loc["const", "coef"] = logit_mod.intercept_
        out_df.loc["const", "non_cv_hss"] = 0
        out_df.loc[:, "p-val"] = pval
        if pval_choice:
        	pval_str = "pval"
        else:
        	pval_str = "hss" 
        out_df.to_csv("/g/data/eg3/ab4502/ExtremeWind/skill_scores/logit_fwd_sel_cluster_"+str(cluster)+"_"+event+"_"+model+".csv")

if __name__ == "__main__":

        parser = argparse.ArgumentParser()
        parser.add_argument('-cluster', type=str)
        args = parser.parse_args()
        cluster = args.cluster

        N=100
        fwd_selection(cluster,N)

	#initial test based on all clusters, and just for Melbourne:
	#Uwindinf + Umean06 + lr03 + q1 + lr36
