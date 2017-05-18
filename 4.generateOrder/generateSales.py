'''

Generate Sales .csv file for Durex

Order ID,Customer ID,Customer Name,Status,Free On Board,Ship Via,Customer Id,Customer Po Ref,
Free On Board,Desired Ship Date

'''
import pandas as pd
import numpy as np

def main(pos,directory):

	df = pd.DataFrame(pos,columns=["Customer Po Ref"])
	df["Order ID"]= np.nan
	df["Customer ID"]= "RADLAB"
	df["Customer Name"]= "RADIATOR LABS"
	df["Status"]= np.nan
	df["Free On Board"]= "UNION, N.J."
	df["Ship Via"]= "TBD"
	df["Customer Id"]= "RADLAB"
	df["Free On Board"]= "UNION, N.J."
	df["Desired Ship Date"]= "ASAP"

	columns = ["Order ID",
	"Customer ID",
	"Customer Name",
	"Status",
	"Free On Board",
	"Ship Via",
	"Customer Id",
	"Customer Po Ref",
	"Free On Board",
	"Desired Ship Date"]

	df.to_csv('orders/'+directory+"/Sales_"+directory+'.csv',index=False,columns=columns)
	
	return 

	