'''

Generate SKU for radiators with matching buildingId 

'''
import pandas as pd 

## Import custom functions 
from helperFunctions import * 
import enclosureFitFunctions
import generateApproval 

## Define building by Id
buildingId = "00046"

## Ensure required directories exist
ensureDirectory("./approvalForm")
ensureDirectory("./skus")

## Get location documents for building 
building = getBuilding(buildingId)
units = getDocuments("radiator",buildingId)
rooms = getDocuments("room",buildingId)
radiators = getDocuments("radiator",buildingId)

## Get survey data 
surveys = getSurveys(buildingId)

## Provision dataset to hold final SKU information 
final = pd.DataFrame(columns = ["No Survey Access","cannotInstall","moveable"])

## Generate SKU for each radiator
for r in radiators[u'Items']:
	try:
		survey = surveys.ix[r["id"]].to_dict()
		survey = dict(r,**survey)
	except:
		continue
	
	final = enclosureFitFunctions.getSKU(final,survey)

## Mark rooms and units not eligible for retrofit | no survey access 
final = markMissing(final,rooms,"room")
final = markMissing(final,units,"unit")

## Sort Dataframe 
try: 
	final["floorName"] = final["floorName"].astype(int)
except:
	pass
try: 
	final["lineName"] = final["lineName"].astype(int)
except:
	pass	
final = final.sort(["floorName","lineName","unitName","roomName","radiatorName"],ascending= [1,1,1,1,1])

## Write out file with all the details for approval
generateApproval.main(building,final)

## Output SKU details for enclosures we can manufacture
SKUoutput(building,final)