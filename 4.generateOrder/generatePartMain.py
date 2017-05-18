'''

Generate Part Maintenance .csv file for Durex

Part ID	Description	Stock UM Fab

'''
import pandas as pd
import numpy as np
def main(allRadiators,directory):
	
	unique = allRadiators.SKU.unique()
	df = pd.DataFrame(unique,index=np.arange(0,len(unique)),columns=["Part ID"])
	df["Description"] = "COZY"
	df["Stock UM"] = "EA"
	df["Fab"] = "Yes"
	df.to_csv('orders/'+directory+"/PART_MAINT_"+directory+'.csv',index=False)
	
	return 