'''

Validate Radiator

'''
from __future__ import print_function
import json
import pandas as pd
import numpy as np
from math import ceil
import sys

def main(surveyData,version):
	try:
		surveyJSON = "./versions/radiator/"+version+'-radiators.json'
		try:
			with open(surveyJSON) as data_file:    
				data = json.load(data_file)
		except:
			return "Radiator survey " + version +" not supported",None

		## Parse through survey 
		errors = "Please remedy the following errors:\n"

		def float_int_string(df,c):
			for i in df.index:
				if str(df.ix[i][c])!='nan':
					df.ix[i,c]=str(int(df.ix[i][c]))
			return df
			
		## Set columns to string
		surveyData['floorName'] = surveyData['floorName'].astype(str)
		surveyData['lineName'] = surveyData['lineName'].astype(str)
		surveyData['unitName'] = surveyData['unitName'].astype(str)
		surveyData = float_int_string(surveyData,"roomNumber")
		surveyData = float_int_string(surveyData,"radiatorNumber")

		def check_existing(list,value):
			for l in list:
				if l[l.keys()[0]]==value:
					return True
			return False
			
		## Determine if all required fields are present in the file
		for child in data["children"]:
			if str(child["identifier"]) not in surveyData.columns:
				errors +=(child["identifier"] + " not in submitted survey information.\n")

		## Determine if the required fields have the right structure
		for child in data["children"]:
			if u'options' in child.keys() and child["identifier"]!="lineName" and child["identifier"]!="floorName":
				answers = surveyData[child["identifier"]].unique()
				answers = filter(lambda x: str(x)!='nan',answers)
				for a in answers:
					if child["options"][0]=="text":
						if check_existing(child["options"],str(a))==False:
							errors +=(str(a) + ' is not a valid answer for ' + child["identifier"] + ", must be one of the listed options\n")
					else:
						if check_existing(child["options"],a)==False:
							errors +=(str(a) + ' is not a valid answer for ' + child["identifier"] + ", must be one of the listed options\n")
			
			elif child['type']=="decimal" or child['type']=="integer":
				answers = surveyData[child["identifier"]].unique()
				answers = filter(lambda x: str(x)!='nan',answers)
				for a in answers:
					try:
						a = 0.5 * ceil(2.0 * a)
					except:
						errors +=(str(a) + ' is not a valid answer for ' + child["identifier"] + ", must be number\n")
			elif child['type']=="boolean":
				answers = surveyData[child["identifier"]].unique()
				answers = filter(lambda x: str(x)!='nan',answers)
				for a in answers:
					if a!='yes' and a!='no':
						errors +=(str(a) + " is not a valid answer for " + child["identifier"] + ", must be yes or no\n")
			else:
				pass
						
		## Determine that the required fields are answered, based on conditions
		def getBool(x):
			if x=="yes" or x=="true":
				return True
			elif x=="no" or x=="false":
				return False
			else:
				return x
				
		# There are several variables which are not required, but not accurately referenced in the radiator survey
		notRequired = ["unitNickName","roomNickName","radiatorNickName","miscellaneousPhoto","miscellaneousPhoto2","risersPhoto","frontPhoto","topPhoto"]

		for child in data["children"]:
			if child["identifier"] in notRequired:
				continue
			if "visible_rule" in child.keys():
				if child["visible_rule"]!="when":
					errors +=("visible rule is equal to " + child["visible_rule"]+"\n")
				allRules = child["visible_expr"].split(",")
				ruleVariables = []
				ruleValues = []
				ruleTest = []
				for r in allRules:
					rule = str(r).replace("AND(","").replace("OR(","").replace(")","").replace('"',"")
					if "=" in rule:
						ruleVariables.append(rule.split(" = ")[0])
						ruleValues.append(getBool(rule.split(" = ")[1]))
						ruleTest.append("bool")
					elif ">":
						ruleVariables.append(rule.split(" > ")[0])
						ruleValues.append(rule.split(" > ")[1])
						ruleTest.append("greater than")
					else:
						print (rule)
				rules = pd.DataFrame(ruleValues,index=ruleVariables)
				rules["ruleTest"] = ruleTest
				
				for i in surveyData.index:
					required = True
					for r in rules.index.unique():
						if len(rules[rules.index==r])==1:
							ruleTest = rules.ix[r]["ruleTest"]
						else:
							ruleTest = rules.ix[r]["ruleTest"].unique()[0]
						if ruleTest =="bool":
							if getBool(surveyData.ix[i][r]) not in list(rules[rules.index==r][0]):	
								required = False
						elif ruleTest =="greater than":
							if float(surveyData.ix[i][r]) <= float(rules.ix[r][0]):
								required = False
					if required==True:
						if str(surveyData.ix[i][child["identifier"]])=='nan':
							errors +=("Variable " + child["identifier"] + " in line "+ str(i+2) + " is required\n")
					else:
						if str(surveyData.ix[i][child["identifier"]])!='nan':
							errors +=("Variable " + child["identifier"] + " in line "+ str(i+2) + " should be blank\n")
			else:
				if "required_rule" in child.keys():
					if child["required_rule"]=="always":
						for i in surveyData.index:
							if str(surveyData.ix[i][child["identifier"]])=='nan':
								errors +=("Variable " + child["identifier"] + " in line "+ str(i+2) + " is required\n")
					else:
						pass
						
		## Get Room and Radiator Names
		surveyData['roomName'] = surveyData['roomName'] +" "+surveyData['roomNumber']
		surveyData['radiatorName'] = "Radiator "+surveyData['radiatorNumber']

		## Determine that radiators numbers are listed properly 
		for key, group in surveyData[surveyData["roomAccess"]=="yes"].groupby(["unitName","roomName"]):
			numbers = np.arange(1,len(group)+1)
			for name in group["radiatorName"]:
				if int(name.replace("Radiator ","")) not in numbers:
					errors +=(name +" is listed, but there are only " + str(len(group))+ " radiators in "+ key[0] + " " + key[1]+"\n")
					
		## Determine that no radiators are listed twice 
		for key, group in surveyData.groupby(["unitName","roomName","radiatorName"]):
			if len(group)>1:
				errors +=(str(key) + " was listed more than once in the survey\n")
				
		## Determine that floors, lines, or units aren't duplicated because of a typo
		def findDuplicates(variable,errors):
			unique = surveyData[variable].unique()
			cleaned = [x.upper().replace(" ","").replace("-","").replace("_","") for n, x in enumerate(unique)]
			duplicates = [x for n, x in enumerate(cleaned) if x in cleaned[:n]]
			for d in duplicates:
				errors+= variable + " " + d + " is listed in two different ways\n"
			return errors
			
		errors = findDuplicates("floorName",errors)
		errors = findDuplicates("lineName",errors)
		errors = findDuplicates("unitName",errors)

		## Print out the final validated data
		returnString = "The submitted survey shows the following:"
		for variable in ["floorName","lineName","unitName"]:
			returnString+= "\n\n"+str(len(surveyData[variable].unique())) + " " + variable.replace("Name","s:") + "\n"
			for l in list(surveyData.sort(variable)[variable].unique()):
				returnString+= l +", "
			returnString = returnString[:-2]
			
		roomCount = 0 
		rooms=""
		for key, group in surveyData.groupby(["unitName","roomName"]):
			roomCount +=1
			rooms+= key[0] + " " + key[1] + ", "

		returnString+= "\n\n"+str(roomCount) + " Rooms\n" + rooms
		returnString = returnString[:-2]

		radiatorCount = 0 
		radiators=""
		for key, group in surveyData.groupby(["unitName","roomName","radiatorName"]):
			radiatorCount+=1
			radiators+= key[0] + " " + key[1] + " "+ key[2] + ", "
			
		returnString+= "\n\n"+str(radiatorCount) + " Radiators\n" + radiators
		returnString = returnString[:-2]

		returnString+= "\n\nPlease ensure that these counts align with your own"
		return errors,returnString
		
	except:
		return str(sys.exc_info()),None
		