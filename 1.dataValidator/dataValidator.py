'''

Validate Data for version 1.2 of the radiator survey 

'''
from __future__ import print_function
import json
import numpy as np
import pandas as pd
import io
import boto3
import sys

import validateRadiatorSurvey
import validateBuildingSurvey

ses = boto3.client('ses')
s3 = boto3.client('s3')

def email(email_to,subject,body):
	for email in email_to:
		
		response = ses.send_email(
			Source = 'meg@radiatorlabs.com',
			Destination={
				'ToAddresses': [
					email,
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

		emailTo = ["rigers@radiatorlabs.com"]

		bucket = str(event['Records'][0]['s3']['bucket']['name'])
		title = str(event['Records'][0]['s3']['object']['key'])

		print (bucket)
		print (title)
		
		response = s3.get_object(Bucket=bucket,Key=title)
		data = response['Body'].read()

		## Try reading the content
		try:
			surveyData = pd.read_csv(io.StringIO(data.decode('utf-8')))
		except:
			print ("error loading " + title)
			email(emailTo,title,"Error loading "+ title)
			return 
			
		## Get the surveyors
		surveyors = surveyData["username"].unique()
		if "Stephen Claffey" in surveyors:
			emailTo.append("stephen@radiatorlabs.com")
		if "John Ortuno" in surveyors:
			emailTo.append("john@radiatorlabs.com")
			
		## Get survey version, type, and open surveyJSON file
		version = title.split("_")[-1].replace(".csv","").lower()
		type = title.split("_")[-2].lower()
		
		if type=="radiator":
			errors,returnString = validateRadiatorSurvey.main(surveyData,version)
		elif type=="building":
			errors,returnString = validateBuildingSurvey.main(surveyData,version)
		else:
			print("Survey type " + type + " is not supported")
			s3.delete_object(Bucket=bucket,Key=title)
			email(emailTo,title,"Survey type " + type + " is not supported")
			return 
			
		if errors!="Please remedy the following errors:\n":
			print (errors)
			s3.delete_object(Bucket=bucket,Key=title)
			email(emailTo,title,errors)
			return
		else:
			print (returnString)
			email(emailTo,title,returnString)
			return
			
	except:
		print ("Unexpected error:", str(sys.exc_info()))
		try:
			s3.delete_object(Bucket=bucket,Key=title)
		except:
			pass
		email(emailTo,"Unexpected error",str(sys.exc_info()))
		return 
