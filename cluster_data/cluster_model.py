from sklearn.cluster import KMeans as kmeans
import pandas as pd

def reconstruct_kmeans_model():

    df = pd.read_csv("tint_processing/cluster_data/cluster_input_era5.csv")
    
    var=["s06","qmean01","lr13","Umean06"]
    
    df_norm = (df - df.min(axis=0)) / (df.max(axis=0) - df.min(axis=0))
    mod=kmeans(n_clusters=3, verbose=0, random_state=0)
    mod_fit=mod.fit(df_norm[var])

    return mod, df[var]

if __name__ == "__main__":

	#SEE README FOR PACKAGE REQUIREMENTS

	#First reconstruct the kmeans clustering model based on cluster_input_era5.csv
	mod, original_df = reconstruct_kmeans_model()

	#Now say we want to apply this to a new dataset with some values of s06, qmean01, lr13 and Umean06...
	new_df = pd.DataFrame({"s06":[19],"qmean01":[10],"lr13":[12],"Umean06":[10]})

	#We need to normalise it by the min/max of our original dataframe, then we apply the kmeans model
	new_df_norm = new_df_norm = (new_df - original_df.min(axis=0)) / (original_df.max(axis=0) - original_df.min(axis=0))
	print("Cluster for our new data point: ",mod.predict(new_df_norm))

	#Note that cluster==1 is the strong background wind cluster, cluster==2 is the steep lapse rate cluster, and cluster==0 is the high moisture cluster.
                            
