'''

Helper Function Library to parse data and prepare the client approval form 

'''
from __future__ import print_function
from boto3.dynamodb.conditions import Key, Attr
from decimal import *
import pandas as pd 
import boto3
import io
import json 
from math import ceil
import dynamoCRUD
import numpy as np 
import datetime
import time

ses = boto3.client('ses')
s3 = boto3.client('s3')

def add(document,identifier,child,value):
	if u'options' in child.keys():
		types =[]
		for option in child["options"]:
			types.append(str(option.keys()[0]))
		if len(set(types))>1:
			raise ValueError('More than one option type for' + child['identifier'])
		type = types[0]
	else:
		type = str(child['type'])
		
	if str(value)=='nan':
		return document
	elif type =="text" or type=="image":
		document[identifier] = str(value)
	elif type =="boolean":
		document[identifier] = getBool(value)
	elif type=="decimal" or type=="integer":
		document[identifier] = getNumber(value)
	elif type=="phone_number":
		document[identifier] = getPhoneNumber(value)
	elif type=="email":
		document[identifier] = str(value)
	else:
		raise ValueError("type " + type + " for "+ identifier + " is unknown")
	return document
		
def getBool(x):
	if str(x)=="True":
		return True
	elif str(x)=="False":
		return False
	elif str(x)=="yes":
		return True
	elif str(x)=="no":
		return False
	else:
		raise ValueError(x)
		
def getNumber(x):
	y = 0.5 * ceil(2.0 * x)
	return Decimal(y/1.0)
	
def getPhoneNumber(x):
	return "+1" + ''.join(c for c in x if c not in '(){}<>-').replace(" ","")
	
def getBuilding(buildingId):
	## Get building information 	
	kce = Key('docType').eq("building") & Key('id').eq(buildingId);
	pe ="#b";
	ean={ "#b": "buildingName" };
		
	buildingDoc = dynamoCRUD.queryMeta("metadata", pe, ean, kce)["Items"][0]
	
	return buildingDoc
	
def getSurveyData(key):
	response = s3.get_object(Bucket='survey-data-bucket',Key=key)
	data = response['Body'].read()

	## Try reading the content
	try:
		surveyData = pd.read_csv(io.StringIO(data.decode('utf-8')),dtype={"floorName":"str","lineName":"str","unitName":"str","roomNumber":"str","radiatorNumber":"str"})
		return surveyData
	except:
		print ("error loading " + title)
		return pd.DataFrame()

def getSurveyJSON(surveyType,surveyVersion):
	path = "./versions/"+surveyType+"/"+surveyVersion.lower()+"-"+surveyType+"s.json"
	with open(path) as data_file:    
		data = json.load(data_file)
	return data 
	
def addBuildingInformation(buildingId, buildingDoc, surveyData):
	## Set common variables
	surveyData["buildingId"] = buildingId
	surveyData["buildingName"] = buildingDoc["buildingName"]
	surveyData["roomName"] = surveyData['roomName'] + " " + surveyData['roomNumber']
	surveyData['radiatorName'] = "Radiator "+surveyData['radiatorNumber']

	del surveyData["radiatorNumber"]
	del surveyData["roomNumber"]

	surveyData = surveyData.sort(["floorName","lineName","unitName","roomName","radiatorName"],ascending = [1,1,1,1,1])
	return surveyData
	
## Query existing documents from database 
def getExisting(docType,buildingId):
	kce = Key('docType').eq(docType) & Key('buildingId').eq(buildingId);
	i="buildingId-docType-index"	
	result = dynamoCRUD.queryMetaIndex("metadata",kce,i)
	df = pd.DataFrame.from_dict(result["Items"])
	if len(df)>0:
		df.index = df["id"].values
		df["integers"] = df["id"].apply(lambda x: int(x[-3:]))
	else:
		df = pd.DataFrame(columns = [docType+"Name","integers","floorId","unitId","roomId","radiatorId"])
	return df
	
## Get the largest id which already exists in the database 
## so that you can start assigning ids from that start
def getStart(df):
	if len(df)==0:
		return 0
	else:
		return np.max(df["integers"])+1

## Get all lines, test if already submitted, submit new lines
def submitLines(lines,surveyData,buildingId):
	line = getStart(lines) 
	for lineName in np.sort(surveyData["lineName"].unique()):
		
		if lineName in lines["lineName"].values:
			lineId = str(lines[lines['lineName'] == lineName].index.tolist()[0])
		else:
			lineId = buildingId + ('{:04d}'.format(line))
			lineDoc = { "lineName": lineName, "buildingId":buildingId,"id":lineId, "docType":"line"}
			dynamoCRUD.putItem("metadata",lineDoc)
			line +=1
			
		surveyData.ix[surveyData["lineName"] == lineName, "lineId"] = lineId
	return surveyData

## Get all floors, test if already submitted, submit new floors
def submitFloors(floors,surveyData,buildingId):
	floor = getStart(floors)
	for floorName in np.sort(surveyData["floorName"].unique()):
		
		if floorName in floors["floorName"].values:
			floorId = str(floors[floors['floorName'] == floorName].index.tolist()[0])
		else:
			floorId = buildingId + ('{:03d}'.format(floor))
			floorDoc = { "floorName": floorName,"buildingId":buildingId,"id":floorId, "docType":"floor" }
			dynamoCRUD.putItem("metadata",floorDoc)
			floor +=1
		
		surveyData.ix[surveyData["floorName"] == floorName, "floorId"] = floorId	
	return surveyData
	
	## Get all units and submit 
def submitUnits(units,surveyData,buildingId,surveyJSON):
	for floorId in surveyData["floorId"].unique():
		unit = getStart(units[units["floorId"]==floorId])
		for unitName in np.sort(surveyData[surveyData["floorId"]==floorId]["unitName"].unique()):
			
			index = surveyData[(surveyData["floorId"]==floorId)&(surveyData['unitName'] == unitName)].index.tolist()[0]
			
			if unitName in units[units["floorId"]==floorId]["unitName"].values:
				unitId = str(units[(units['floorId'] == floorId)&(units['unitName'] == unitName)].index.tolist()[0])
			else:
				unitId = surveyData.ix[index]["floorId"] + ('{:03d}'.format(unit))
				list = ["floorName","lineName","unitName","unitNickName"]
				unitDoc = {"id":unitId, "docType":"unit","buildingId":buildingId,"buildingName":surveyData.ix[index]["buildingName"],"floorId":surveyData.ix[index]["floorId"],"lineId":surveyData.ix[index]["lineId"]}
				for child in surveyJSON["children"]:
					if str(child["identifier"]) in list:
						unitDoc = add(unitDoc,str(child["identifier"]),child,surveyData.ix[index][child["identifier"]])
				
				dynamoCRUD.putItem("metadata",unitDoc)
				unit +=1
				
			# Add unitId to matching units
			surveyData.ix[(surveyData["floorId"]==floorId)&(surveyData["unitName"] == unitName), "unitId"] = unitId

			if surveyData.ix[index]["unitAccess"] == "no":
				start =  datetime.datetime.strptime(surveyData.ix[index]['submissiondatetime'][:19], '%Y-%m-%d %H:%M:%S')
				utc = int(time.mktime(start.timetuple())*1000)
				visit = {
					"id": unitId,
					"UTCtimestamp":utc,
					"access":False,
					"accessReason": surveyData.ix[index]["unitAccessReason"],
					"reason":"unit survey",
					"success":False,
					"buildingId": surveyData.ix[index]["buildingId"],
					"floorId": surveyData.ix[index]["floorId"]
				}
				dynamoCRUD.putItem("visitdata",visit)
			else:
				pass
	return surveyData 

## Get all Rooms and Submit 
def submitRooms(rooms,surveyData,buildingId,surveyJSON):
	for unitId in surveyData[surveyData["unitAccess"]=="yes"]["unitId"].unique():
		room = getStart(rooms[rooms["unitId"]==unitId])
		for roomName in np.sort(surveyData[surveyData['unitId'] == unitId]["roomName"].unique()):
			index = surveyData[(surveyData['unitId'] == unitId) & (surveyData["roomName"]==roomName)].index.tolist()[0]
			
			if roomName in rooms[rooms["unitId"]==unitId]["roomName"].values:
				roomId = str(rooms[(rooms['unitId'] == unitId)&(rooms['roomName'] == roomName)].index.tolist()[0])
			else:
				roomId = surveyData.ix[index]["unitId"]+ ('{:03d}'.format(room))
				list = ["floorName","lineName","unitName","unitNickName","roomName","roomNickName","risers","risersInsulated","risersPhoto"]
				roomDoc = {"id":roomId, "buildingName":surveyData.ix[index]["buildingName"],"docType":"room","buildingId":buildingId,"floorId":surveyData.ix[index]["floorId"],"lineId":surveyData.ix[index]["lineId"],"unitId":surveyData.ix[index]["unitId"]}
				for child in surveyJSON["children"]:
					if str(child["identifier"]) in list:
						roomDoc = add(roomDoc,str(child["identifier"]),child,surveyData.ix[index][child["identifier"]])
				
				dynamoCRUD.putItem("metadata",roomDoc)
				room +=1
				
			surveyData.ix[(surveyData["unitId"]==unitId)&(surveyData["roomName"] == roomName), "roomId"] = roomId

			if surveyData.ix[index]["roomAccess"] == "no":
				start =  datetime.datetime.strptime(surveyData.ix[index]['submissiondatetime'][:19], '%Y-%m-%d %H:%M:%S')
				utc = int(time.mktime(start.timetuple())*1000)
				visit = {
					"id": roomId,
					"UTCtimestamp":utc,
					"access":False,
					"accessReason": surveyData.ix[index]["roomAccessReason"],
					"reason":"room survey",
					"success":False,
					"buildingId": surveyData.ix[index]["buildingId"],
					"floorId": surveyData.ix[index]["floorId"],
					"unitId": surveyData.ix[index]["unitId"]
				}
				dynamoCRUD.putItem("visitdata",visit)
				continue
			else:
				pass
	return surveyData

def submitRadiators(radiators,surveyData,buildingId,surveyJSON,surveyType,surveyVersion):
	## Get all Rooms and Submit 
	for roomId in surveyData[(surveyData["roomAccess"]=="yes")&(surveyData["unitAccess"]=="yes")]["roomId"].unique():
		radiator = getStart(radiators[radiators["roomId"]==roomId])
		for radiatorName in np.sort(surveyData[surveyData['roomId'] == roomId]["radiatorName"].dropna().unique()):

			index = surveyData[(surveyData['roomId'] == roomId) & (surveyData["radiatorName"]==radiatorName)].index.tolist()[0]
			
			list = ["floorName","lineName","unitName","unitNickName","roomName",
				"roomNickName","radiatorName","radiatorNickName",
				"radiatorType","pipingSystem"]
			if radiatorName in radiators[radiators["roomId"]==roomId]["radiatorName"].values:
				radiatorId = str(radiators[(radiators['roomId'] == roomId)&(radiators['radiatorName'] == radiatorName)].index.tolist()[0])
			else:
				radiatorId = surveyData.ix[index]["roomId"]+ ('{:03d}'.format(radiator))
				radiatorDoc = {
					"id":radiatorId, 
					"docType":"radiator",
					"buildingId":buildingId,
					"buildingName":surveyData.ix[index]["buildingName"],
					"floorId":surveyData.ix[index]["floorId"],
					"lineId":surveyData.ix[index]["lineId"],
					"unitId":surveyData.ix[index]["unitId"],
					"roomId":surveyData.ix[index]["roomId"],
					"radiatorName":surveyData.ix[index]["radiatorName"],
					"active":False
					}

				
				for child in surveyJSON["children"]:
					if str(child["identifier"]) in list:
						radiatorDoc = add(radiatorDoc,str(child["identifier"]),child,surveyData.ix[index][child["identifier"]])

				dynamoCRUD.putItem("metadata",radiatorDoc)
				radiator +=1
			
			surveyData.ix[(surveyData["roomId"]==roomId)&(surveyData["radiatorName"] == radiatorName), "radiatorId"] = radiatorId

			if surveyData.ix[index]["radiatorAccess"] == "no":
				start =  datetime.datetime.strptime(surveyData.ix[index]['submissiondatetime'][:19], '%Y-%m-%d %H:%M:%S')
				utc = int(time.mktime(start.timetuple())*1000)
				visit = {
					"id": radiatorId,
					"UTCtimestamp":utc,
					"access":False,
					"accessReason": surveyData.ix[index]["radiatorAccessReason"],
					"reason":"room survey",
					"success":False,
					"buildingId": surveyData.ix[index]["buildingId"],
					"floorId": surveyData.ix[index]["floorId"],
					"unitId": surveyData.ix[index]["unitId"],
					"roomId": surveyData.ix[index]["roomId"]
				}
				dynamoCRUD.putItem("visitdata",visit)
				continue
			else:
				noSurveyList = list + ["roomNumber","radiatorNumber","roomAccess","roomAccessReason","unitAccess","unitAccessReason","risers","risersInsulated","risersPhoto"]
				
				start =  datetime.datetime.strptime(surveyData.ix[index]['submissiondatetime'][:19], '%Y-%m-%d %H:%M:%S')
				utc = int(time.mktime(start.timetuple())*1000)
				survey = {
					"id":radiatorId,
					"surveyType":surveyType,
					"version":surveyVersion.lower().strip('v'),
					"UTCtimestamp":utc,
					"buildingId": surveyData.ix[index]["buildingId"],
					"floorId": surveyData.ix[index]["floorId"],
					"lineId": surveyData.ix[index]["lineId"],
					"unitId": surveyData.ix[index]["unitId"],
					"roomId": surveyData.ix[index]["roomId"],
					"submittedBy": surveyData.ix[index]["username"]
				}
				for child in surveyJSON["children"]:
					if str(child["identifier"]) not in noSurveyList:
						survey = add(survey,str(child["identifier"]),child,surveyData.ix[index][child["identifier"]])
				dynamoCRUD.putItem("surveydata",survey)
				
				visit = {
					"id": radiatorId,
					"UTCtimestamp":utc,
					"access":True,
					"reason":"radiator survey",
					"success":True,
					"buildingId": surveyData.ix[index]["buildingId"],
					"floorId": surveyData.ix[index]["floorId"],
					"unitId": surveyData.ix[index]["unitId"],
					"roomId": surveyData.ix[index]["roomId"],
					"submittedBy": surveyData.ix[index]["username"]
				}
				dynamoCRUD.putItem("visitdata",visit)
	return surveyData
			