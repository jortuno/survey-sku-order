'''

Functions to help SKU generation

'''
import os 
import pandas as pd
import dynamoCRUD 
from boto3.dynamodb.conditions import Key, Attr

def ensureDirectory(directory):
	if not os.path.exists(directory):
		os.makedirs(directory)
	return 
	
def getBuilding(buildingId):
	kce = Key('docType').eq("building") & Key('id').eq(buildingId);
	pe ="#a";
	ean={ "#a": "addressLine1" };
		
	building = dynamoCRUD.queryMeta("metadata", pe, ean, kce)["Items"][0]["addressLine1"].replace(" ","-")
	return building
	
def getDocuments(docType,buildingId):
	ke = Key('docType').eq(docType) & Key('buildingId').eq(buildingId);
	i = "buildingId-docType-index"
	documents = dynamoCRUD.queryMetaIndex("metadata",ke,i)
	return documents
	
def getSurveys(buildingId):
	ke = Key('buildingId').eq(buildingId);
	i = "buildingId-index"
	documents = dynamoCRUD.queryMetaIndex("surveydata",ke,i)
	df = pd.DataFrame.from_dict(documents["Items"])
	df.index = df["id"]
	return df

def markMissing(final,df,variable):
	for d in df["Items"]:
		if d["id"] in final[variable+"Id"].values:
			continue
		else:
			ke = Key("id").eq(d["id"])
			i = "id-index"
			visits = dynamoCRUD.queryMetaIndex("visitdata",ke,i)
			if visits["Count"]>0:
				visits = pd.DataFrame.from_dict(visits["Items"]) 
				visits = visits[visits["reason"]==variable + " survey"]
				visits = visits.sort("UTCtimestamp",ascending=False)
				if visits.empty:
					continue
				else:
					d["No Survey Access"] = "No Access, " + str(visits.ix[0]["accessReason"])
					single = pd.DataFrame(d,index=[d["id"]])
					final = pd.concat([final,single])
			else:
				continue
	return final
			

def SKUoutput(building,final):
	final = final.dropna(subset=["SKU"])

	def pad(x,index):
		return ('{0:03d}'.format(int(float(x.split("_")[index])*10)))
	def padBP(x,index):
		return ('{0:03d}'.format(int((float(x.split("_")[index])-8)*10)))

	final.loc[:,"SPL"] = final["SKU"].map(lambda x: "SPL" + pad(x,3) + pad(x,4))
	final.loc[:,"SPR"] = final["SKU"].map(lambda x: "SPR" + pad(x,3) + pad(x,4))
	final.loc[:,"AP"] = final["SKU"].map(lambda x: "AP" + pad(x,3) + pad(x,4))
	final.loc[:,"FP"] = final["SKU"].map(lambda x: "FP" + pad(x,2) + pad(x,4))
	final.loc[:,"TP"] = final["SKU"].map(lambda x: "TP" + pad(x,2) + pad(x,3))
	final.loc[:,"BP"] = final["SKU"].map(lambda x: "BP" + pad(x,2) + padBP(x,4))
	final.loc[:,"insertLeft"] = final["SKU"].map(lambda x: "I"+str(x.split("_")[5]))
	final.loc[:,"insertRight"] = final["SKU"].map(lambda x: "I"+str(x.split("_")[6]))
	final.loc[:,"LP"] = final["SKU"].map(lambda x: "LP" + pad(x,3))

	## Write PO for the Building
	header = ["id","buildingName","floorName","lineName","unitName","roomName","radiatorName","SKU","SPL","SPR","AP","FP","TP","BP","insertRight","insertLeft","LP"]
	final.to_csv("skus/"+building+".csv",columns=header,index=False)
	return 