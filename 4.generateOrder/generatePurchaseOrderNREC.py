'''

Generate NREC Purchase Order

'''
import pandas as pd
import xlsxwriter
import numpy as np
import dynamoCRUD
from boto3.dynamodb.conditions import Key, Attr
import datetime
import os

def main(df,directory):
	
	panels = pd.read_csv("allPanels.csv")

	dirs = os.listdir("./orders")

	for d in dirs:
		exists = []
		files = os.listdir("./orders/"+d)
		for f in files:
			if "Assembly" in f and ".pdf" not in f:
				exists = []
				assembly = pd.read_excel("./orders/"+d+"/"+f)
				for p in panels["Part Number"]:
					if p in assembly.values:
						exists.append(1)
					else:
						exists.append(0)
		
				panels[f.split("_")[1]+f.split("_")[2] + "_"+f.split("_")[3].strip(".xlsx")] = exists
	for i in panels.index:
		set = False
		for c in panels.columns:
			if set ==True:
				panels.ix[i,c]=0
			if panels.ix[i][c] == 1:
				set = True
				
	newPanelColumns = filter(lambda x: directory in x,panels.columns)
	newPanels = panels[newPanelColumns]
	newPanels.index = panels["Part Number"]
	total = np.sum(newPanels,axis=1).to_frame()
	total = total[total[0]==1]
	total["Cost"]= 75
	total["Count"] = 1
	total["Total Cost"] = total["Cost"]*total["Count"]
	
	##Create an new Excel file and add a worksheet.
	workbook = xlsxwriter.Workbook('orders/'+directory+"/PurchaseOrder_NREC_"+directory+'.xlsx')
	worksheet = workbook.add_worksheet()
	
	merge_format = workbook.add_format({
    'align': 'center',
    'valign': 'vcenter'})
	
	merge_formatBold = workbook.add_format({
	'bold':1,
	'border':1,
	'font_size':10,
    'align': 'center',
    'valign': 'vcenter'})
	
	format = workbook.add_format()
	format.set_font_size(10)
	format.set_align('left')
	format.set_align('vcenter')
	
	formatCenter = workbook.add_format()
	formatCenter.set_font_size(10)
	formatCenter.set_align('center')
	formatCenter.set_align('vcenter')
	
	formatBold = workbook.add_format()
	formatBold.set_font_size(10)
	formatBold.set_align('left')
	formatBold.set_align('vcenter')
	formatBold.set_bold()
	
	formatBoldUpper = workbook.add_format()
	formatBoldUpper.set_font_size(10)
	formatBoldUpper.set_align('left')
	formatBoldUpper.set_align('vcenter')
	formatBoldUpper.set_bold()
	formatBoldUpper.set_top()
	
	formatAccounting = workbook.add_format({'num_format': "_($* #,##0.00_);_($* (#,##0.00);_($* ""-""??_);_(@_)"})
	formatAccounting.set_font_size(10)
	
	## Set header and footer
	worksheet.set_header('&CPage &P of &N')
	worksheet.set_footer('&F')
	
	## Set row and column heights
	worksheet.set_default_row(15)
	worksheet.set_column('A:A',5)
	worksheet.set_column('B:B',30)
	worksheet.set_column('C:E',15)

	## Write in all default aspects of the PO
	worksheet.insert_image("A1", 'logo.png')
	
	worksheet.merge_range('D1:E1', 'Purchase Order', merge_format)

	worksheet.write("D2","Date",formatCenter)
	worksheet.write("D3",datetime.datetime.now().strftime("%m/%d/%Y"),formatCenter)
	worksheet.write("E2","PO #",formatCenter)
	worksheet.write("E3",datetime.datetime.now().strftime("%Y%m%d")+"NREC",formatCenter)
	
	worksheet.merge_range('A4:E4',"Bill To:", merge_formatBold)
	worksheet.write("A5","Radiator Labs",format)
	worksheet.write("A6","Brooklyn Navy Yard, Bldg 3 #606",format)
	worksheet.write("A7","63 Flushing Avenue Unit 286",format)
	worksheet.write("A8","Brooklyn, NY 11205",format)
	worksheet.write("A9","United States",format)
	
	worksheet.write("C5","Contact: Marshall Cox",format)
	worksheet.write("C6","Phone: 646-902-4328",format)
	worksheet.write("C7","Email: marshall@radiatorlabs.com",format)
	
	worksheet.merge_range('A11:E11',"Vendor:", merge_formatBold)
	worksheet.write("A12","Durex Inc",format)
	worksheet.write("A13","5 Stahuber Avenue",format)
	worksheet.write("A14","Union, NJ 07083",format)
	worksheet.write("A15","United States",format)
	
	worksheet.write("C12","Contact: Bob Denholtz",format)
	worksheet.write("C13","Phone: 908-688-0800 x208",format)
	worksheet.write("C14","Email: bdenholtz@durexinc.com",format)
	
	worksheet.write("A18","Line #",formatBold)
	worksheet.write("B18","SKU",formatBold)
	worksheet.write("C18","Qty",formatBold)
	worksheet.write("D18","Cost",formatBold)
	worksheet.write("E18","Extended Cost",formatBold)
	
	
	j = 20
	for i in total.index:
		k = total.index.get_loc(i) + 1
		worksheet.write("A"+str(j),k,format)
		worksheet.write("B"+str(j),str(i) + " NREC",format)
		worksheet.write("C"+str(j),total.ix[i]["Count"],format)
		worksheet.write("D"+str(j),total.ix[i]["Cost"],formatAccounting)
		worksheet.write("E"+str(j),total.ix[i]["Total Cost"],formatAccounting)
		j+=1
	
	## Write the pricing out
	j+=1
	worksheet.write("D"+str(j),"SubTotal",formatBold)
	worksheet.write("E"+str(j),np.sum(total["Total Cost"]),formatAccounting)
	j+=1
	worksheet.write("D"+str(j),"Shipping",formatBold)
	worksheet.write("E"+str(j),0,formatAccounting)
	j+=1
	worksheet.write("D"+str(j),"Discount",formatBold)
	worksheet.write("E"+str(j),0,formatAccounting)
	j+=1
	worksheet.write("D"+str(j),"Other Adjustment",formatBold)
	worksheet.write("E"+str(j),0,formatAccounting)
	j+=1
	worksheet.write("D"+str(j),"Tax",formatBold)
	worksheet.write("E"+str(j),0,formatAccounting)
	j+=1
	worksheet.write("D"+str(j),"Total",formatBold)
	worksheet.write("E"+str(j),np.sum(total["Total Cost"]),formatAccounting)
	
	workbook.close()
	return 

	
