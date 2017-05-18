'''

Order Submission

Generate a master PO, a master manufacturing list, and an assembly list for each building

'''

import os
import numpy as np
import pandas as pd
import datetime
import time
from win32com import client

import generateAssemblyList
import generateManufacturingList
import generatePurchaseOrder
import generatePurchaseOrderNREC
import generatePartMain
import generateSales
import dynamoCRUD

## Add buildings you want to order to the list 
buildings = ["DEMO"]

## Date for filename
date = datetime.datetime.now()
week = (date.day-1)//7+1
month = date.strftime("%b%Y")

directory = month + "_Week" + str(week)

## Ensure correct directories exist 
if not os.path.exists("./orders/"+directory):
	os.makedirs("./orders/"+directory)
if not os.path.exists("./images"):
	os.makedirs("./images")
	
## Enclosure Order Date
orderDate = date.replace(hour=0, minute=0, second=0, microsecond=0)
enclosureOrderDate = int(time.mktime(orderDate.timetuple())*1000)
	
def excel2pdf(file,directory):
	xlApp = client.Dispatch("Excel.Application")
	xlApp.Visible = False
	books = xlApp.Workbooks.Open(os.getcwd()+'/orders/'+directory+"/"+file+"_"+directory+'.xlsx')
	ws = books.Worksheets[0]
	ws.Visible = 1
	ws.ExportAsFixedFormat(0,os.getcwd()+'/orders/'+directory+"/"+file+"_"+directory+'.pdf')
	xlApp.Quit()
	return 
		
allRadiators = pd.DataFrame()
pos=[]
for b in buildings:
	approved = pd.read_excel("../3.generateSKU/approvalForm/"+b+".xlsx",converters={'Radiator Id': str})
	output = pd.read_csv("../3.generateSKU/skus/"+b+".csv",converters={'id': str})

	approved = approved[approved["Confirm Order"]=="Order"]
	
	## Set index to common id & combine 
	approved.index = approved["Radiator Id"]
	output.index = output["id"]

	final = pd.concat([approved,output],axis=1)
	final = final.dropna(subset=["Radiator Id"])
	
	## Mark which units are Pros & update the SKU in the database
	for i in final.index:
		if final.ix[i]["Pro"]==1:
			final.ix[i,"Xbee"]="Pro"
			final.ix[i,"SKU"] = final.ix[i]["SKU"].replace("_R_","_P_")
		else:
			pass
		key = {'id':final.ix[i]["id"],'docType':'radiator'}
		update = "set enclosureSKU =:enclosureSKU, enclosureManufacturer =:enclosureManufacturer, enclosureOrderDate=:enclosureOrderDate"
		expression = {':enclosureSKU':final.ix[i]["SKU"],
			':enclosureManufacturer': "Durex",
			':enclosureOrderDate':enclosureOrderDate
			}
		dynamoCRUD.updateItem("metadata",key,update,expression)
	
	## Fix the SKU to be under 30 characters
	for i in final.index:
		final.ix[i,"SKU"] = final.ix[i]["SKU"].replace("M_","")
	
	## Generate Assembly list and Purchase Order for the building
	generateAssemblyList.main(b,final,directory)
	
	num = generatePurchaseOrder.main(b,final,directory)
	pos.append(num)
	
	allRadiators = pd.concat([allRadiators,final])
	
	## Make PDF copies of the document
	excel2pdf("Assembly_"+b,directory)
	excel2pdf("PurchaseOrder_"+b,directory)

## Generate bundled manufacturing list
allRadiators.index=np.arange(0,len(allRadiators))
generateManufacturingList.main(allRadiators,directory)
generatePurchaseOrderNREC.main(allRadiators,directory)
generatePartMain.main(allRadiators,directory)
generateSales.main(pos,directory)

excel2pdf("PurchaseOrder_NREC",directory)
