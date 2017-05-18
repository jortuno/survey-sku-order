'''

generate Form for Approval 

'''
import os, sys
import pandas as pd
import numpy as np
import xlsxwriter
import string

sys.path.append("C:\Users/Meg/Documents/GitHub/survey-sku-po")
from barcodeGenerator import * 

def main(building,final):
	oldColumns = ["unitName","roomName","radiatorName","No Survey Access","cannotInstall","customFabricRequired","moveable","lengthFlag","heightFlag","id"]
	headerApproval = ["Unit","Room Name","Radiator","No Survey Access","Cannot Install","Custom Fabric Cover Required","Furniture","Length Flag","Height Flag","Radiator Id","Approval (Y/N)"]
	approval = final[oldColumns]
	approval = approval.drop_duplicates()
	approval.loc[:,"Approval (Y/N)"] = np.nan
	approval.columns = headerApproval
	approval.index = np.arange(0,len(approval))
	writeFile(building,approval)
	
	return 
	
def writeFile(building,approval):
	def write(location,value,format):
		if str(value)!="nan":
			worksheet.write(location,value,format)
		return
	
	# Create an new Excel file and add a worksheet.
	workbook = xlsxwriter.Workbook('./approvalForm/'+building+'.xlsx')

	worksheet = workbook.add_worksheet()

	formatTitle = workbook.add_format()
	formatTitle.set_font_size(10)
	formatTitle.set_align('center')
	formatTitle.set_align('vcenter')
	formatTitle.set_text_wrap()
	formatTitle.set_bold()

	format = workbook.add_format()
	format.set_font_size(8)
	format.set_align('center')
	format.set_align('vcenter')
	format.set_text_wrap()

	worksheet.set_default_row(45)
	worksheet.set_landscape()

	# Set the columns widths
	worksheet.set_column('A:C', 10)

								
	columns = ["Unit","Room Name","Radiator","No Survey Access","Cannot Install",
	"Custom Fabric Cover Required","Furniture","Length Flag","Height Flag","Confirm Order","Radiator Id"]

	start = ord('a') 

	for c in columns:
		if c=="No Survey Access" or c=="Cannot Install":
			worksheet.set_column(chr(start).upper()+":"+chr(start).upper(), 15)
		elif start>=100:
			worksheet.set_column(chr(start).upper()+":"+chr(start).upper(), 20)
		if c == "Confirm Order":
			worksheet.write(chr(start).upper()+str(1),c,formatTitle)
			for i in approval.index:
				if str(approval.ix[i]["Cannot Install"])=="nan" and str(approval.ix[i]["No Survey Access"])=="nan":
					write(chr(start).upper()+str(i+2),"Order",format)
					worksheet.data_validation(chr(start).upper()+str(i+2), {'validate': 'list','source': ['Order', 'Do Not Order']})
			worksheet.set_column(chr(start).upper()+":"+chr(start).upper(), 8)
			start +=1
		elif c in approval.columns:
			worksheet.write(chr(start).upper()+str(1),c,formatTitle)
			for i in approval.index:
				write(chr(start).upper()+str(i+2),str(approval.ix[i][c]),format)
		
			start +=1

	workbook.close()
	return 