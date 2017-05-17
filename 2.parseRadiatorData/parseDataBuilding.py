'''

Parse data and insert into database for version 1.0 of the building survey 

'''
import json
import pandas as pd
from decimal import *
from math import ceil
import time
from boto3.dynamodb.conditions import Key, Attr
import dynamoCRUD
from helpers import * 

def main(surveyData,surveyJSON):

	## Generate buildingId
	kce = Key('docType').eq("building");
	i="docType-index"	
	result = dynamoCRUD.queryMetaIndex("metadata",kce,i)
	
	df = pd.DataFrame.from_dict(result["Items"])
	df["id"] = df["id"].astype("int")
	
	buildingId = np.max(df["id"]) + 1
	buildingId = ('{:05d}'.format(buildingId))

	## Generate new building based on surveyData and surveyJSON
	buildingDoc = {"id":buildingId,
	  "docType":"building",
	  "active": False,
	  "addedOn": int(time.time()*1000),
	  "boilerControl": False}

	for child in surveyJSON["children"]:
		buildingDoc = add(buildingDoc,child["identifier"],child,surveyData.ix[0][child["identifier"]])
		
	dynamoCRUD.putItem("metadata",buildingDoc)
	
	return 