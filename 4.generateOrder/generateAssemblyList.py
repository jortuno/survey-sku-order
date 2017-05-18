'''

generate PO

'''

import pandas as pd
from barcodeGenerator import * 
import xlsxwriter

def main(b,df,directory):
	
	def getInsul(x):
		if x=="B":
			return "Board"
		elif x=="F":
			return "Fabric"
			
	def getXbee(x):
		if x=="R":
			return "Regular"
		elif x=="P":
			return "Pro"
			
	def getTraps(x):
		if x=="N":
			return "None"
		elif x=="S":
			return "SteamTraps"	
			
	df["Insulation"] = df["SKU"].apply(lambda x : getInsul(x.split("_")[6]))
	df["Xbee"] = df["SKU"].apply(lambda x : getXbee(x.split("_")[7]))
	df["SteamTraps"] = df["SKU"].apply(lambda x : getTraps(x.split("_")[8]))
	
	df["Length"] = df["SKU"].apply(lambda x : float(x.split("_")[1]))
	df["Width"] = df["SKU"].apply(lambda x : float(x.split("_")[2]))
	df["Height"] = df["SKU"].apply(lambda x : float(x.split("_")[3]))
	
	df = df.sort(["Length","Width","Height","insertLeft","insertRight","Insulation","Xbee","SteamTraps"],ascending=[1,1,1,1,1,1,1,1])
	
	for i in df.index:
		generate_barcode(i)

	# Create an new Excel file and add a worksheet.
	workbook = xlsxwriter.Workbook('orders/'+directory+'/Assembly_'+b + "_"+directory+'.xlsx')
	worksheet = workbook.add_worksheet()
	worksheet.set_margins(left=0.05,right=0.05,top=0.5,bottom=0.5)

	format = workbook.add_format()
	format.set_font_size(7)
	format.set_align('center')
	format.set_align('vcenter')
	format.set_text_wrap()
	
	formatSKU = workbook.add_format()
	formatSKU.set_font_size(10)
	formatSKU.set_align('center')
	formatSKU.set_align('vcenter')
	formatSKU.set_text_wrap()
	
	formatShaded = workbook.add_format()
	formatShaded.set_font_size(8)
	formatShaded.set_align('center')
	formatShaded.set_align('vcenter')
	formatShaded.set_text_wrap()
	formatShaded.set_pattern(1)  # This is optional when using a solid fill.
	formatShaded.set_bg_color('#D3D3D3')
	
	formatShadedSKU = workbook.add_format()
	formatShadedSKU.set_font_size(10)
	formatShadedSKU.set_align('center')
	formatShadedSKU.set_align('vcenter')
	formatShadedSKU.set_text_wrap()
	formatShadedSKU.set_pattern(1)  # This is optional when using a solid fill.
	formatShadedSKU.set_bg_color('#D3D3D3')
	
	formatBold = workbook.add_format()
	formatBold.set_font_size(8)
	formatBold.set_align('center')
	formatBold.set_align('vcenter')
	formatBold.set_text_wrap()
	formatBold.set_bold()

	worksheet.set_default_row(60)
	worksheet.set_landscape()
	
	worksheet.set_header('&CPage &P of &N')
	worksheet.set_footer('&F')

	# Widen the first column to make the text clearer.
	worksheet.set_column('A:A',2.5)
	worksheet.set_column('B:B',28)
	worksheet.set_column('C:D',8)
	worksheet.set_column('E:I',7)
	worksheet.set_column('J:N',5)
	worksheet.set_column('O:O',18)
	
	columns = ["Qty","Radiator Assembly SKU","Structural Panel Left","Structural Panel Right","Leveling Panel (x2)","Aesthetic Panel (x2)","Top Panel","Front Panel","Back Panel","Cover Panel Left","Cover Panel Right","Insul.","Xbee","Steam Traps","Radiator Id"]
	start = ord("a")
	for c in columns:
		worksheet.write(chr(start).upper()+"1",c,formatBold)
		start+=1
	
	formatter = 1
	for sku in df["SKU"].unique():
		#alternate format
		if formatter ==0:
			formatter =1
		elif formatter==1:
			formatter =0
		
		quantity = len(df[df["SKU"]==sku])		
		if formatter ==0:
			for i in df[df["SKU"]==sku].index:
				j = df.index.get_loc(i)
				if i == df[df["SKU"]==sku].index[0]:
					worksheet.write("A"+str(j+2),str(quantity),format)
				else:
					worksheet.write("A"+str(j+2),"",format)
					
				worksheet.write("B"+str(j+2),str(df.ix[i]["SKU"]),formatSKU)
				worksheet.write("C"+str(j+2),str(df.ix[i]["SPL"]),format)
				worksheet.write("D"+str(j+2),str(df.ix[i]["SPR"]),format)
				worksheet.write("E"+str(j+2),str(df.ix[i]["LP"]),format)
				worksheet.write("F"+str(j+2),str(df.ix[i]["AP"]),format)
				worksheet.write("G"+str(j+2),str(df.ix[i]["TP"]),format)
				worksheet.write("H"+str(j+2),str(df.ix[i]["FP"]),format)
				worksheet.write("I"+str(j+2),str(df.ix[i]["BP"]),format)
				worksheet.write("J"+str(j+2),str(df.ix[i]["insertLeft"]),format)
				worksheet.write("K"+str(j+2),str(df.ix[i]["insertRight"]),format)
				worksheet.write("L"+str(j+2),str(df.ix[i]["Insulation"]),format)
				worksheet.write("M"+str(j+2),str(df.ix[i]["Xbee"]),format)
				worksheet.write("N"+str(j+2),str(df.ix[i]["SteamTraps"]),format)
				worksheet.insert_image("O"+str(j+2), './images/'+i+'.png', {'x_offset':5, 'y_offset': 25,'x_scale': 10, 'y_scale': 10})
		elif formatter==1:			
			for i in df[df["SKU"]==sku].index:
				j = df.index.get_loc(i)

				if i == df[df["SKU"]==sku].index[0]:
					worksheet.write("A"+str(j+2),str(quantity),formatShaded)
				else:
					worksheet.write("A"+str(j+2),"",formatShaded)
				
				worksheet.write("B"+str(j+2),str(df.ix[i]["SKU"]),formatShadedSKU)
				worksheet.write("C"+str(j+2),str(df.ix[i]["SPL"]),formatShaded)
				worksheet.write("D"+str(j+2),str(df.ix[i]["SPR"]),formatShaded)
				worksheet.write("E"+str(j+2),str(df.ix[i]["LP"]),formatShaded)
				worksheet.write("F"+str(j+2),str(df.ix[i]["AP"]),formatShaded)
				worksheet.write("G"+str(j+2),str(df.ix[i]["TP"]),formatShaded)
				worksheet.write("H"+str(j+2),str(df.ix[i]["FP"]),formatShaded)
				worksheet.write("I"+str(j+2),str(df.ix[i]["BP"]),formatShaded)
				worksheet.write("J"+str(j+2),str(df.ix[i]["insertLeft"]),formatShaded)
				worksheet.write("K"+str(j+2),str(df.ix[i]["insertRight"]),formatShaded)
				worksheet.write("L"+str(j+2),str(df.ix[i]["Insulation"]),formatShaded)
				worksheet.write("M"+str(j+2),str(df.ix[i]["Xbee"]),formatShaded)
				worksheet.write("N"+str(j+2),str(df.ix[i]["SteamTraps"]),formatShaded)
				worksheet.insert_image("O"+str(j+2), './images/'+i+'.png', {'x_offset': 5, 'y_offset':25,'x_scale': 10, 'y_scale': 10})
	workbook.close()
	return 