import pandas as pd
import os
from datetime import datetime
import re
#in: trade data from get_trade.py or calc_pct.py
#out: same data but with the cmdCodes updated to H6
data_path = '' #dir or single file
#note that the output of get_trade is CSV and the output of calc_pct is XLSX with two sheets
concord_path = 'nomenclature/concordances' #dir to concordances
def year_class(year:int):
	if year < 1996:
		return 'H0'
	if year < 2002:
		return 'H1'
	if year < 2007:
		return 'H2'
	if year < 2012:
		return 'H3'
	if year < 2017:
		return 'H4'
	if year < 2022:
		return 'H5'
	return 'H6'

#currently only supports one year at a time.
#in the future, could split the df into each year and merge each one... whatever...

def f(in_file, codecol=''):
	filename = os.fsdecode(in_file)
	if filename.endswith('.csv'):
		df = pd.read_csv(filename)
	elif(filename.endswith('.xlsx')):
		df = pd.read_excel(filename)
		#and replace for every sheet that has code
	else:
		print("Invalid file, neither CSV nor XLSX.")
		return
	colnames = df.columns
	this_year = -1
	try:
		year_col = next(x for x in colnames if "year" in x.lower())
		this_year = df[year_col][0]
	except:
		try:
			r = re.search(r'(199|198)\d{1}|20\d{2}', in_file)
			this_year = int(r.group(0))
		except:
			this_year = -1
	if(this_year < 0):
		print("Couldn't find the year for this data. Make sure a labeled column for year exists, or the year is clear in the filename.")
		return
	#code column
	if len(codecol) < 1: #no explicit code column name passed
		try:
			tmp = pd.DataFrame([str(x[0]) == 'int64' and len(str(x[1])) >= 5 for x in zip(df.dtypes, df.min(axis=0))], colnames)
			code_col = next(x for x in colnames if "code" in x.lower() and tmp.loc[[x],0].bool())
		except:
			print("Couldn't infer the column with the product codes. Run the script again and pass the column name to the --c flag.")
			return
	else: #explicit column name passed
		code_col = codecol

	this_class = year_class(this_year)
	if this_class == 'H0':
		print("The classification is already H0.")
		return
	concord_file = ''
	print("The inferred year and class are ", this_year, " and ", this_class, ".", sep='')
	for file in os.listdir(concord_path):
		if this_class.lower() in file.lower():
			concord_file = file
			break
	if len(concord_file) < 1:
		print("Didn't find a concordance file for ", filepath, ".", sep='')
		return
	concord_df = pd.read_csv(os.path.join(concord_path, concord_file))
	to_h0 = df.merge(concord_df, how='left', left_on = 'cmdCode', right_on = this_class)
	to_h0.drop(['cmdCode', this_class], axis=1, inplace=True)
	to_h0.rename(columns={'H0':'cmdCode'}, inplace=True)
	to_h0 = to_h0[colnames]
	print("Updated codes to H0.")
	outfile, ext = os.path.splitext(in_file)
	outfile = outfile + '_H0' + ext
	if filename.endswith('.csv'):
		to_h0.to_csv(outfile, index=False)
	elif(filename.endswith('.xlsx')):
		with pd.ExcelWriter(outfile) as writer:
				to_h0.to_excel(writer, index=False)
	print('Wrote to ', outfile, '.', sep='')
	return

# if __name__ == "__main__":
# 	parser = argparse.ArgumentParser(description="Create an .xlsx file with trade dependency percentages by product and country on one sheet and total import and export values on the second sheet for a given year. If the input is a directory, runs this script on all .csv files in the directory.")
# 	parser.add_argument("input", type=str, help="Filename of the input .csv.")
# 	parser.add_argument("out", nargs='?', default="trade_pcts", help="Path to directory for output files, if running script on directory. Default '/trade_pcts/'.")
# 	args = parser.parse_args()
# 	in_path = args.input
# 	out_dir = args.out
	
# 	if not os.path.exists(in_path):
# 		print("Invalid input, file or directory does not exist.")
# 		sys.exit()

# 	if os.path.isdir(in_path):
# 		print("Running script on all .csv files in directory ", in_path, ".", sep='')
# 		if not os.path.exists(out_dir):
# 			os.makedirs(out_dir)
# 		print("Output .xlsx files will be in directory ", out_dir, ".", sep='')
# 		for file in os.listdir(os.getcwd()):
# 			filename = os.fsdecode(file)
# 			if filename.endswith('.csv'):
# 				f(filename, out_dir)
# 	elif os.path.isfile(in_path):
# 		f(in_path)
# 	else:
# 		print('Input is neither a file nor directory.')

