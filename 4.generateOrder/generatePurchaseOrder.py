'''

Generate the Purchase Order for the weekly order placed with Durex

Display the total first, then break it down by building 

'''
import pandas as pd
import xlsxwriter
import numpy as np
import dynamoCRUD
from boto3.dynamodb.conditions import Key, Attr
import datetime

def main(buildingName,df,directory):
	
	def getFrequency(df):
		frequencies = []
		skus = []
		for key, group in df.groupby("SKU"):	
			frequencies.append(len(group))
			skus.append(key)
		frequency = pd.DataFrame(frequencies,index=skus,columns=["Count"])
		
		frequency["Cost"] = 297.33
		frequency["Total Cost"] = frequency["Cost"]*frequency["Count"]
		return frequency
		
	df["buildingId"] = df["id"].map(lambda x:  x[:5])
	building = df["buildingId"].unique()[0]
	poNumber = datetime.datetime.now().strftime("%Y%m%d")+building

	df["Insulation"] = df["SKU"].apply(lambda x : x.split("_")[6])
	df["Xbee"] = df["SKU"].apply(lambda x : x.split("_")[7])
	df["SteamTraps"] = df["SKU"].apply(lambda x : x.split("_")[8])

	df["Length"] = df["SKU"].apply(lambda x : float(x.split("_")[1]))
	df["Width"] = df["SKU"].apply(lambda x : float(x.split("_")[2]))
	df["Height"] = df["SKU"].apply(lambda x : float(x.split("_")[3]))

	df = df.sort(["Length","Width","Height","insertLeft","insertRight","Insulation","Xbee","SteamTraps"],ascending=[1,1,1,1,1,1,1,1])
	
	## Write in order totals
	countAll = getFrequency(df)
	
	##Create an new Excel file and add a worksheet.
	workbook = xlsxwriter.Workbook('orders/'+directory+"/PurchaseOrder_"+buildingName+"_"+directory+'.xlsx')
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
	worksheet.write("E3",poNumber,formatCenter)
	
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
		
	## Query DB for building information 
	pe = "#a1,#a2,#c,#s,#z"
	ean = { "#a1":"addressLine1","#a2":"addressLine2","#c":"city","#s":"state","#z":"zipCode"}
	ke = Key('docType').eq('building') & Key('id').eq(building);
	b = dynamoCRUD.queryMeta("metadata", pe, ean, ke)["Items"][0]

	## Write in Building Address
	worksheet.merge_range('A17:E17',"Ship to Address:", merge_formatBold)
	worksheet.write("A18",b["addressLine1"].title(),format)
	worksheet.write("C18","Contact: ",format)
	try:
		worksheet.write("A19",b["addressLine2"].title(),format)
		worksheet.write("C19","Phone: ",format)
		worksheet.write("A20"+str(j),"Attn: ",format)
		worksheet.write("C20"+str(j),"Email: ",format)
		worksheet.write("A21"+str(j),b["city"].title() + ", "+b["state"] + " " + b["zipCode"],format)
		worksheet.write("A22"+str(j),"United States",format)
	except:
		worksheet.write("A19","Attn: ",format)
		worksheet.write("C19","Phone:",format)
		worksheet.write("A20",b["city"] + ", "+b["state"] + " " + b["zipCode"],format)
		worksheet.write("C20","Email: ",format)
		worksheet.write("A21","United States",format)
	
	worksheet.write("A24","Line #",formatBold)
	worksheet.write("B24","SKU",formatBold)
	worksheet.write("C24","Qty",formatBold)
	worksheet.write("D24","Cost",formatBold)
	worksheet.write("E24","Extended Cost",formatBold)
		
	j = 25
	for i in countAll.index:
		k = countAll.index.get_loc(i) + 1
		worksheet.write("A"+str(j),k,format)
		worksheet.write("B"+str(j),str(i),format)
		worksheet.write("C"+str(j),countAll.ix[i]["Count"],format)
		worksheet.write("D"+str(j),countAll.ix[i]["Cost"],formatAccounting)
		worksheet.write("E"+str(j),countAll.ix[i]["Total Cost"],formatAccounting)
		j+=1
		
	worksheet.write("B"+str(j),"Total Units",formatBold)
	worksheet.write("C"+str(j),np.sum(countAll["Count"]),formatBold)
	
	## Write the pricing out
	j+=1
	worksheet.write("D"+str(j),"SubTotal",formatBold)
	worksheet.write("E"+str(j),np.sum(countAll["Total Cost"]),formatAccounting)
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
	worksheet.write("E"+str(j),np.sum(countAll["Total Cost"]),formatAccounting)
	
	workbook.close()
	return poNumber

	
