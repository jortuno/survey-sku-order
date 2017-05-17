'''

Validate building survey 

'''
from __future__ import print_function
import json
import pandas as pd
import numpy as np
from math import ceil
import sys

def main(surveyData,version):
	try:
		surveyJSON = "./versions/building/"+version+'-building.json'
		try:
			with open(surveyJSON) as data_file:    
				data = json.load(data_file)
		except:
			return "Building survey " + version +" not supported",None
		
		## Parse through survey 
		errors = "Please remedy the following errors:\n"
		
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
			if u'options' in child.keys():
				answers = surveyData[child["identifier"]].unique()
				answers = filter(lambda x: str(x)!='nan',answers)
				if u'multiple' in child.keys():
					if child["multiple"]==True:
						for a in answers:
							if len(a.split(","))>1:
								answers.remove(a)
								answers += a.split(",")
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
		notRequired = ["sitePartnerAddressLine2"]

		for child in data["children"]:
			if child["identifier"] in notRequired:
				continue
			if "visible_rule" in child.keys():
				if child["visible_rule"]!="when":
					errors +=("visible rule is equal to " + child["visible_rule"]+"\n")
				allRules = child["visible_expr"].split(",")
				ruleVariables = []
				ruleValues = []
				for r in allRules:
					rule = str(r).replace("AND(","").replace("OR(","").replace(")","").replace('"',"")
					ruleVariables.append(rule.split(" = ")[0])
					ruleValues.append(getBool(rule.split(" = ")[1]))
				rules = pd.DataFrame(ruleValues,index=ruleVariables)
				
				for i in surveyData.index:
					required = True
					for r in rules.index.unique():
						if getBool(surveyData.ix[i][r]) not in list(rules[rules.index==r][0]):	
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
		return errors,"File is validated. Ready for database"
	except:
		return str(sys.exc_info()),None