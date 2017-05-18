'''

All function relating to SKU fit 

'''
import os 
import boto3
import pandas as pd 
import numpy as np 

## Available SKU Bins
lengthBins = np.arange(23,59,6)
widthBins = np.arange(7.5,15.5,2)
heightBins = np.arange(24,48,6)

## Minimum add in each direction
minAddWidth = 2 
minAddHeight = 1
minDuctLength = 8
minDuctHeight = 5
minAddPanel = 1.8

def moveableTest(survey):
	rightMoveableLength = None
	rightObject = None
	leftMoveableLength = None
	leftObject = None

	## See if you can move obstructions on either side
	if survey["rightFreeSpace"]==False and survey["rightObstructionMoveable"]==True:
		rightMoveableLength = float(survey["rightFreeSpaceObstructionMeasurement"])
		rightObject = survey["rightObstruction"]
		
	if survey["leftFreeSpace"]==False and survey["leftObstructionMoveable"]==True:
		leftMoveableLength = float(survey["leftFreeSpaceObstructionMeasurement"])
		leftObject = survey["leftObstruction"]
		
	return 	rightMoveableLength, rightObject,leftMoveableLength, leftObject 
	
def getAP(survey,ductSide):
	if ductSide =="Right":
		if survey["rightCutout"] ==True:
			rightAP = "GC"
		else:
			rightAP = "GX"
		if survey["leftCutout"]==True:
			leftAP = "BC"
		else:
			leftAP = "BX"
	elif ductSide == "Left":
		if survey["leftCutout"] ==True:
			leftAP = "GC"
		else:
			leftAP = "GX"
		if survey["rightCutout"]==True:
			rightAP = "BC"
		else:
			rightAP = "BX"
	
	return rightAP,leftAP

## Test possible length configurations
# Figure out if an where you can place the specified duct
def getDuct(cutout,lower,lowerHeight,lowerLength,length,height,free):
	# Return boolean for duct fit, minimum length required to add for the enclosure to fit 
	if cutout == True:
		if lower ==True:
			if lowerHeight <=minDuctHeight and lowerLength>=minDuctLength:
				return True, minDuctLength,0
			else:
				return False, None, None
		else:
			return False, None, None
	elif height <= minDuctHeight:
		if length >= minDuctLength:
			return True, length,free 
		elif (length + free)>=minDuctLength:
			return True, minDuctLength,free
		else:
			return False, None, None
	else:
		if free >= minDuctLength:
			return True, (minDuctLength + length),free
		else:
			return False, None, None

## Test possible length configurations
def testLength(minLength,survey):
	try:
		length = sorted((i+minLength) for i in (lengthBins - minLength) if i >=-.9)[0]
		return True, length
	except:
		return False, "Length of radiator requires custom enclosure"	
		
# Figure out how much length you have to add on the other side 
def getAdded(cutout, length):
	if cutout==True:
		return minAddPanel
	else:
		return length + minAddPanel
		
def concatResults(results,test,length, rightCutout, leftCutout, ductSide, move, cutout,reason):
	if move == None:
		moveCode = 0
	elif move == "Right"or move=="Left":
		moveCode = 1
	elif move =="Both":
		moveCode=2
	if cutout == None:
		cutoutCode = 0
	else:
		cutoutCode = 1
	
	single = pd.DataFrame({"test":test,"length":length,"rightCutout":rightCutout,"leftCutout":leftCutout,"ductSide":ductSide,"move":move,"moveCode":moveCode,"forcedCutout":cutout,"forcedCutoutCode":cutoutCode,"reason":reason},index=[len(results)])
	results = pd.concat([results,single])
	return results
	
def getLength(results,survey, rightCutout, leftCutout, rightFree, leftFree, ductSide, move,cutout):
				
	## If right or left free is none - it means that moving obstructions was not possible. Return without analysis.
	if move!=None:
		if rightFree is None or leftFree is None:
			results = concatResults(results,False,np.nan,rightCutout,leftCutout,ductSide,move,cutout,"Moving obstructions not possible")
			return results
		
	## If no freespace, and no cutout, cannot retrofit (test both sides)
	if rightFree==0 and rightCutout==False:
		results = concatResults(results,False,np.nan,rightCutout,leftCutout,ductSide,move,cutout,"No space available on right side for enclosure installation")
		return results
	if leftFree==0 and leftCutout==False:
		results = concatResults(results,False,np.nan,rightCutout,leftCutout,ductSide,move,cutout,"No space available on left side for enclosure installation")
		return results
	
	## Test if there is a lower section of the pipe to put the duct over. 
	rightLowerHeight,rightLowerLength,leftLowerHeight,leftLowerLength = (np.nan,)*4 

	rightLower = survey["rightLowerPipe"]
	if rightLower == True:
		rightLowerHeight = survey["rightLowerPipeHeight"]
		rightLowerLength = survey["rightLowerPipeLength"]
		
	leftLower = survey["leftLowerPipe"]
	if leftLower ==True:
		leftLowerHeight = survey["leftLowerPipeHeight"]
		leftLowerLength = survey["leftLowerPipeLength"]

	## If cutout is not None - a new cutout is trying to be forced on the right or left side. Check if this is possible. 
	if cutout!=None:
		if cutout == "Right":
			if float(survey["rightHeight"])<5:
				pass
			elif rightLowerHeight<5:
				pass
			else:
				results = concatResults(results,False,np.nan,rightCutout,leftCutout,ductSide,move,cutout,"Cannot apply cutout on the right side")
				return results
		elif cutout == "Left":
			if float(survey["leftHeight"])<5:
				pass
			elif leftLowerHeight<5:
				pass
			else:
				results = concatResults(results,False,np.nan,rightCutout,leftCutout,ductSide,move,cutout,"Cannot apply cutout on the left side")
				return results
	
	## Check if the duct fits on the specified side
	if ductSide == "Right":
		duct, rightAdded,rightFree = getDuct(rightCutout,rightLower,rightLowerHeight,rightLowerLength,float(survey["rightLength"]),float(survey["rightHeight"]),rightFree)
		leftAdded = getAdded(leftCutout, float(survey["leftLength"]))
	elif ductSide == "Left":
		duct, leftAdded,leftFree = getDuct(leftCutout,leftLower,leftLowerHeight,leftLowerLength,float(survey["leftLength"]),float(survey["leftHeight"]),leftFree)
		rightAdded = getAdded(rightCutout, float(survey["rightLength"]))
		
	if duct == False:
		results = concatResults(results,False,np.nan,rightCutout,leftCutout,ductSide,move,cutout,"Duct does not fit")# on the " + ductSide.lower() + "side")
		return results
	else:
		pass
				
	## Find minimum length 
	minLength = float(survey["radLength"]) + rightAdded + leftAdded

	## Find Binned Length 
	lengthTest, length = testLength(minLength,survey)
	if lengthTest==False: # cannot fit enclosure, return false 
		results = concatResults(results,False,np.nan,rightCutout,leftCutout,ductSide,move,cutout,"Minimum length of " + str(minLength) + " requires a custom enclosure length")
		return results
		
	## Test that there is enough total room for the required length of the enclosure
	addLength = length - minLength 
	if addLength >(rightFree + leftFree):
		results = concatResults(results,False,np.nan,rightCutout,leftCutout,ductSide,move,cutout,"An enclosure of length " + str(length)+ " is required, but not sufficient free space to install")
		return results
	else:
		results = concatResults(results,True,length,rightCutout,leftCutout,ductSide,move,cutout,"")
		return results
		
def getSKU(final,r):
	if "fabricRequired" in r.keys():
		if r["fabricRequired"] == True:
			if r["existingCover"] == True:
				r["customFabricRequired"] = "Fabric Cozy Required"
				single = pd.DataFrame(r,index=[r["id"]])
				final = pd.concat([final,single])
				return final 
			else:
				r["customFabricRequired"] = np.nan
				r["cannotInstall"] = "Fabric Cozy Required, but no existing enclosure"
				single = pd.DataFrame(r,index=[r["id"]])
				final = pd.concat([final,single])
				return final 
		else:
			r["customFabricRequired"] = np.nan
	else:
		r["customFabricRequired"] = np.nan
		
	## If radiatorType is not stand alone cast iron, cannot retrofit, return 
	if r["radiatorType"] == "Obstructed":
		r["cannotInstall"] = "The heating element is obstructed"
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
		return final 
	elif r["radiatorType"] == "Riser Only" or r["radiatorType"] == "No Heating Source":
		r["cannotInstall"] = r["radiatorType"]
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
		return final 
	elif r["radiatorType"] != "Stand Alone Cast Iron":
		r["cannotInstall"] = "The heating element is a " + r["radiatorType"]
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
		return final 		
	else:
		pass
	
	## If left or right side panel is obstructed, cannot retrofit, return 
	if 	r["rightSidePanelObstruction"]==True:
		r["cannotInstall"] = "Right side of radiator is obstructed by " + str(r["rightSidePanelObstructionObject"])
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
		return final 
	
	if 	r["leftSidePanelObstruction"]==True:
		r["cannotInstall"] = "Left side of radiator is obstructed by " + str(r["leftSidePanelObstructionObject"])
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
		return final 

	## Get Width
	minwidth = float(r["radWidth"]) + minAddWidth
	try:
		width = sorted((i+minwidth) for i in (widthBins - minwidth) if i >=0)[0]
		r['width'] = width
	except:
		r["cannotInstall"] = "Width of radiator requires custom enclosure"
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
		return final 
		
	## Get Height
	minheight = float(r["radHeight"]) + minAddHeight
	try:
		height = sorted((i+minheight) for i in (heightBins - minheight) if i >=0)[0]
		if r["heightFreeSpace"] == False:
			if (r["heightFreeSpaceMeasurement"] + r["radHeight"]) < height:
				r["cannotInstall"] = "Required enclosure height is " + str(height) + '" available space is ' + str(r["heightFreeSpaceMeasurement"] + r["radHeight"]) + '" (limited by ' + r["heightFreeSpaceObstruction"]+")"
				single = pd.DataFrame(r,index=[r["id"]])
				final = pd.concat([final,single])
				return final 	
			else:
				r['height'] = height
		else:
			r['height'] = height
	except:
		r["cannotInstall"] = "Height of radiator requires custom enclosure"
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
		return final 
	
	## Test if enough room (heightwise) for the enclosure 		
	if r["belowWindow"]==True:
		try:
			if float(r["windowHeight"]) < height:
				if r["fireGate"]==True:
					r["cannotInstall"] = "Required height of enclosure is " + str(height) +'", which would block fire gate'
					single = pd.DataFrame(r,index=[r["id"]])
					final = pd.concat([final,single])
					return final 
		except:
			pass
				
	# Vary all possible configurations to find the optimal fit which minimizes size and actions taken for installation. 
	# results, survey, rightCutout, leftCutout, rightFree, leftFree, ductSide, move,cutout

	results = pd.DataFrame(columns=["test","length","ductSide","moveRight","moveLeft","rightCutout","leftCutout"])

	## Identify existing available free space and if this can be increased by moving obstructions.		
	if r["rightFreeSpace"]==False:
		rightFree = float(r["rightFreeSpaceMeasurement"])
	else:
		rightFree = 10
		
	if r["leftFreeSpace"]==False:
		leftFree = float(r["leftFreeSpaceMeasurement"])
	else:
		leftFree = 10
		
	rightMove,rightObject,leftMove, leftObject = moveableTest(r)

	###########################################################################################################
	# Initial 
	results = getLength(results, r, r["rightCutout"],r["leftCutout"],rightFree,leftFree,"Right",None,None)
	results = getLength(results, r, r["rightCutout"],r["leftCutout"],rightFree,leftFree,"Left",None,None)

	# Move Right
	results = getLength(results, r, r["rightCutout"],r["leftCutout"],rightMove,leftFree,"Right","Right",None)
	results = getLength(results, r, r["rightCutout"],r["leftCutout"],rightMove,leftFree,"Left","Right",None)

	# Move Left 
	results = getLength(results, r, r["rightCutout"],r["leftCutout"],rightFree,leftMove,"Right","Left",None)
	results = getLength(results, r, r["rightCutout"],r["leftCutout"],rightFree,leftMove,"Left","Left",None)

	# Move Both
	results = getLength(results, r, r["rightCutout"],r["leftCutout"],rightMove,leftMove,"Right","Both",None)
	results = getLength(results, r, r["rightCutout"],r["leftCutout"],rightMove,leftMove,"Left","Both",None)
	 
	###########################################################################################################
	if r["rightCutout"]==False:
		
		# Initial 
		results = getLength(results, r,True,r["leftCutout"],rightFree,leftFree,"Right",None,"Right")
		results = getLength(results, r,True,r["leftCutout"],rightFree,leftFree,"Left",None,"Right")

		# Move Right
		results = getLength(results, r,True,r["leftCutout"],rightMove,leftFree,"Right","Right","Right")
		results = getLength(results, r,True,r["leftCutout"],rightMove,leftFree,"Left","Right","Right")

		# Move Left 
		results = getLength(results, r,True,r["leftCutout"],rightFree,leftMove,"Right","Left","Right")
		results = getLength(results, r,True,r["leftCutout"],rightFree,leftMove,"Left","Left","Right")

		# Move Both
		results = getLength(results, r,True,r["leftCutout"],rightMove,leftMove,"Right","Both","Right")
		results = getLength(results, r,True,r["leftCutout"],rightMove,leftMove,"Left","Both","Right")

	###########################################################################################################
	if r["leftCutout"]==False:
		
		# Initial 
		results = getLength(results, r, r["rightCutout"],True,rightFree,leftFree,"Right",None,"Left")
		results = getLength(results, r, r["rightCutout"],True,rightFree,leftFree,"Left",None,"Left")

		# Move Right
		results = getLength(results, r, r["rightCutout"],True,rightMove,leftFree,"Right","Right","Left")
		results = getLength(results, r, r["rightCutout"],True,rightMove,leftFree,"Left","Right","Left")

		# Move Left 
		results = getLength(results, r, r["rightCutout"],True,rightFree,leftMove,"Right","Left","Left")
		results = getLength(results, r, r["rightCutout"],True,rightFree,leftMove,"Left","Left","Left")

		# Move Both
		results = getLength(results, r, r["rightCutout"],True,rightMove,leftMove,"Right","Both","Left")
		results = getLength(results, r, r["rightCutout"],True,rightMove,leftMove,"Left","Both","Left")

	## All length options are now gathered in the results dataframe 
	
	choices = results.dropna(subset=['length'])

	if len(choices)==0:
		r["cannotInstall"] = results.ix[0]["reason"]
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
		return final 
	else:
		## Select the choice which minimizes the length, the furniture that has to be moved, and any cutouts forced via the survey process
		choices = choices.sort(["length","moveCode","forcedCutoutCode"],ascending=[1,1,1])
		if r["id"]=="00000009005000000":
			print choices
		choice = choices.ix[choices.index[0]]
		ductSide = choice['ductSide']
		
		if choice["moveCode"] == 0:
			pass
		elif choice["moveLeft"]==True and choice["moveRight"]==True:
			r["moveable"] = rightObject + "on the right side of the radiator and " + leftObject + " on the left side of the radiator must be moved in order to install"
		elif choice["moveLeft"]==True:
			r["moveable"] =  leftObject + " on the left side of the radiator must be moved in order to install"
		elif choice["moveRight"]==True:
			r["moveable"] =  rightObject + " on the right side of the radiator must be moved in order to install"

		r['length']= choice['length']
		r["rightCutout"] = choice["rightCutout"]
		r["leftCutout"] = choice["leftCutout"]
		
		## Create length flags
		r["addedFootprint"] = r["length"] - float(r["radLength"]) -float(r["rightLength"]) - float(r["leftLength"])
			
		if r['length'] > float(r["radLength"])*2:
			r["lengthFlag"] = "Added footprint is " + str(r["addedFootprint"])+'"'
		elif r['length'] - float(r['radLength']) > 20:
			r["lengthFlag"] = "Added footprint is " + str(r["addedFootprint"])+'"'
		else:
			r["lengthFlag"] = np.nan
			
		## Create Height Flags
		if r["belowWindow"]==True:
			try:
				if float(r["windowHeight"]) < height:
					r["heightFlag"] = "Height of enclosure will exceed the windowsill by "+str(height - float(r["windowHeight"]) )+'"'
				else:
					r["heightFlag"] = np.nan
			except:
				r["heightFlag"] = np.nan
		else:
			r["heightFlag"] = np.nan
		
		## Get aesthetic panels
		rightAP, leftAP = getAP(r,ductSide)
		r['leftAP'] = leftAP
		r['rightAP'] = rightAP
		
		## Get Insulation 
		try:
			if r["backPanelObstruction"]==True:
				if r["requiredBackPanel"]== "Fabric Back Panel":
					insul = "B"
				elif r["requiredBackPanel"]== "Can Not Retrofit":
					r["cannotInstall"] = "No clearance for back panel, obstructed by " + r["backPanelObstructionObject"]
					single = pd.DataFrame(r,index=[r["id"]])
					final = pd.concat([final,single])
					return final 
			else:
				insul = "B"
		except:
			insul="B"
			
		## Add a placeholder for the xbee in the SKU
		r["xbee"] = "R"
		
		## Determine if there are steamtrap sensors or not 
		if r["pipingSystem"]=="single pipe" or r["pipingSystem"]=="One-Pipe" or r["pipingSystem"]=="SINGLE PIPE":
			steamtrap = "N"
		else:
			steamtrap = "S"
		
		r["SKU"] = "22_M_"+str(r['length'])+"_"+str(width)+"_"+str(height)+"_"+leftAP + "_" +rightAP+ "_" + insul + "_" + r['xbee'] + "_" + steamtrap
		single = pd.DataFrame(r,index=[r["id"]])
		final = pd.concat([final,single])
	return final 