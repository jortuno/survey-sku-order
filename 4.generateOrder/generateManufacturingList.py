'''

Generate Manufacturing List 

'''

import pandas as pd
import xlsxwriter
import numpy as np


def main(df,directory):

	df.index=df["id"]
	
	allPanels = pd.read_csv("allPanels.csv")
	allPanels["Count"] = 0

	columns = ["SPL","SPR","AP","FP","TP","BP","insertRight","insertLeft","LP"]
	for c in columns:
		for key, group in df.groupby(c):
			index = allPanels[allPanels["Part Number"]==key].index[0]
			if key[0:2]=="AP" or key[0:2]=="LP":
				allPanels.loc[index,"Count"] = allPanels.ix[index,"Count"] + 2*len(group)
			else:
				allPanels.loc[index,"Count"] = allPanels.ix[index,"Count"] + len(group)
				
	# Create an new Excel file and add a worksheet.
	workbook = xlsxwriter.Workbook('orders/'+directory+"/Manufacturing_"+directory+'.xlsx')
	worksheet = workbook.add_worksheet()

	format = workbook.add_format()
	format.set_font_size(8)
	format.set_align('center')
	format.set_align('vcenter')
	format.set_text_wrap()

	formatLeft = workbook.add_format()
	formatLeft.set_font_size(8)
	formatLeft.set_align('center')
	formatLeft.set_align('vcenter')
	formatLeft.set_text_wrap()
	formatLeft.set_left()

	formatBold = workbook.add_format()
	formatBold.set_font_size(8)
	formatBold.set_align('center')
	formatBold.set_align('vcenter')
	formatBold.set_text_wrap()
	formatBold.set_bold()

	formatBoldLeft = workbook.add_format()
	formatBoldLeft.set_font_size(8)
	formatBoldLeft.set_align('center')
	formatBoldLeft.set_align('vcenter')
	formatBoldLeft.set_text_wrap()
	formatBoldLeft.set_bold()
	formatBoldLeft.set_left()

	formatBoldUpper = workbook.add_format()
	formatBoldUpper.set_font_size(8)
	formatBoldUpper.set_align('center')
	formatBoldUpper.set_align('vcenter')
	formatBoldUpper.set_text_wrap()
	formatBoldUpper.set_bold()
	formatBoldUpper.set_top()

	worksheet.set_default_row(15)
	worksheet.set_landscape()

	# Widen the first column to make the text clearer.
	worksheet.set_column('A:Z', 9.57)
	worksheet.set_row('1:1', 30)
	
	worksheet.set_header('&CPage &P of &N')
	worksheet.set_footer('&F')
	
	start = ord('a') 
	categories = ["Structural Panel Left (D x H)","Structural Panel Right (D x H)","Aesthetic Panel (D x H)","Front Panel (H x L)","Top Panel (D x L)","Back Panel (H x L)","Cover Panel","Leveling Panel (D)"]

	for c in categories:
		
		worksheet.write(chr(start).upper()+"1",c.replace(" x ","x"),formatBoldLeft)
		worksheet.write(chr(start+1).upper()+"1","Quantity",formatBold)
		worksheet.write(chr(start+2).upper()+"1","SKU",formatBold)
		
		if len(allPanels[allPanels["Panel"] == c])==16:
			for fill in np.arange(21,29,1):
				worksheet.write(chr(start).upper()+str(fill),"",formatLeft)
		elif len(allPanels[allPanels["Panel"] == c])==4:
			for fill in np.arange(6,29,1):
				worksheet.write(chr(start).upper()+str(fill),"",formatLeft)
				
		number = 2
		current = np.nan
		
		for i in allPanels[allPanels["Panel"] == c].index:
			if c!="Cover Panel" and c!="Leveling Panel (D)" and str(current)!='nan':
				if current == str(allPanels.ix[i]["Part Print"].split(" x ")[0]):
					pass
				else:
					worksheet.write(chr(start).upper()+str(number),"",formatLeft)
					number +=1
				
			worksheet.write(chr(start).upper()+str(number),allPanels.ix[i]["Part Print"],formatLeft)
			worksheet.write(chr(start+1).upper()+str(number),allPanels.ix[i]["Count"],format)
			worksheet.write(chr(start+2).upper()+str(number),allPanels.ix[i]["Part Number"],format)
			current = str(allPanels.ix[i]["Part Print"].split(" x ")[0])
			worksheet.write(chr(start).upper()+"29","",formatLeft)
			worksheet.write(chr(start).upper()+"29","",formatBoldUpper)
			worksheet.write(chr(start+1).upper()+"29",np.sum(allPanels[allPanels["Panel"] == c]["Count"]),formatBoldUpper)
			worksheet.write(chr(start+2).upper()+"29","",formatBoldUpper)
			number +=1
		start+=3
		
	worksheet.write("Y29",str(np.sum(allPanels["Count"]))+" Parts Total",formatBold)
	workbook.close()
	return 