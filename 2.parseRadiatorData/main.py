'''

Parse data and insert into the surveydata table 

Export the client approval form to the client-approval-forms s3 bucket 

'''
from helpers import *
import boto3
import sys

ses = boto3.client('ses')
s3 = boto3.client('s3')

def email(emailTo,subject,body):
		
	response = ses.send_email(
		Source = 'meg@radiatorlabs.com',
		Destination={
			'ToAddresses': [
				emailTo,
			],

		},
		Message={
			'Subject': {
				'Data': subject
			},
			'Body': {
				'Text': {
					'Data': body
				}
			}
		}
	)
	return 
	
def lambda_handler(event, context):
	try:
		print (event)
		## variables passed to the function call 
		try:
			buildingId = event["buildingId"]
		except:
			buildingId = None
		
		key = event["key"]
		emailTo = event["id"]
		print(key)
		print(emailTo)
		
		## parse the file key to get information 
		date, building, surveyType, surveyVersion = key.strip(".csv").split("_")

		surveyData = getSurveyData(key) ## load the survey data from the survey-data-bucket
		surveyJSON = getSurveyJSON(surveyType,surveyVersion) ## load the local json survey version information

		## If document is a building, parse
		if surveyType == "building":
			import parseDataBuilding
			parseDataBuilding.main(surveyData,surveyJSON)
			email(emailTo,key,key + " was successfully parsed with no errors")
			s3.delete_object(Bucket='survey-data-bucket',Key=key)
			return
			
		## If document is radiators, parse
		elif surveyType == "radiator":
			
			buildingDoc = getBuilding(buildingId) ## get building information 

			## add building information & sort the dataset
			surveyData = addBuildingInformation(buildingId, buildingDoc, surveyData) 

			## Get all the existing documents for the building 
			floors = getExisting("floor",buildingId)
			lines = getExisting("line",buildingId)
			units = getExisting("unit",buildingId)
			rooms = getExisting("room",buildingId)
			radiators = getExisting("radiator",buildingId)

			## submit all documents
			surveyData = submitLines(lines,surveyData,buildingId)
			surveyData = submitFloors(floors,surveyData,buildingId)
			surveyData = submitUnits(units,surveyData,buildingId,surveyJSON)
			surveyData = submitRooms(rooms,surveyData,buildingId,surveyJSON)
			surveyData = submitRadiators(radiators,surveyData,buildingId,surveyJSON,surveyType,surveyVersion)
			
			email(emailTo,key,key + " was successfully parsed with no errors")
			s3.delete_object(Bucket='survey-data-bucket',Key=key)
			return 
			
		else:
			email(emailTo,key,surveyType + " surveyType is not supported")
			s3.delete_object(Bucket='survey-data-bucket',Key=key)
			return
			
	except:
		print ("Unexpected error:", str(sys.exc_info()))

		email(emailTo,"Unexpected error",str(sys.exc_info()))
		return
						