import pip
import argparse
import sys, importlib
import os

def import_or_install(package:str):
	try:
		__import__(package)
	except ImportError:
		pip.main(['install', '--user', package])

import_or_install('pandas')
importlib.reload(sys.modules['pandas'])
import pandas as pd
import_or_install('xlsxwriter')

def f(path, out_dir=''):
	df = pd.read_csv(path)
	#columns: ['refYear', 'flowDesc', 'reporterDesc', 'partnerDesc', 'cmdCode', 'cmdDesc', 'primaryValue']
	by_country = df[df['partnerDesc'] != 'World'].drop(['flowDesc', 'reporterDesc'], axis=1)
	year = df['refYear'][0]
	#^ since 'export' can only have partner 'world', this leaves only imports, so flowDesc is redundant
	world_only = df[df['partnerDesc'] == 'World'][['cmdCode', 'flowDesc', 'primaryValue']]
	imp_exp = world_only.set_index(['cmdCode','flowDesc']).rename_axis(['fucking kms'], axis=1).stack().unstack('flowDesc').reset_index()
	imp_exp.drop(['fucking kms'], axis=1, inplace=True)
	imp_exp.columns.name = None
	#return(imp_exp)
	out = by_country.merge(imp_exp[['cmdCode','Import']],
														how = 'left',
														on = 'cmdCode')
	out['trade_pct'] = out['primaryValue']/out['Import']
	out.drop('Import', axis=1, inplace=True)
	filename = os.path.join(out_dir, str(year) + '_imp_exp_trade_pcts.xlsx')

	with pd.ExcelWriter(filename) as writer:
		out.to_excel(writer, sheet_name = 'by_country', index=False)
		imp_exp.to_excel(writer, sheet_name = 'imports_exports', index=False)

	print('Wrote to ', filename, '.', sep='')
	return

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Using the .csv output from get_trade.py, create an .xlsx file with trade dependency percentages by product and country on one sheet and total import and export values on the second sheet for a given year. If the input is a directory, runs this script on all .csv files in the directory.")
	parser.add_argument("input", type=str, help="Filename of the input .csv.")
	parser.add_argument("out", nargs='?', default="trade_pcts", help="Path to directory for output files, if running script on directory. Default '/trade_pcts/'.")
	args = parser.parse_args()
	in_path = args.input
	out_dir = args.out
	
	if not os.path.exists(in_path):
		print("Invalid input, file or directory does not exist.")
		sys.exit()

	if os.path.isdir(in_path):
		print("Running script on all .csv files in directory ", in_path, ".", sep='')
		if not os.path.exists(out_dir):
			os.makedirs(out_dir)
		print("Output .xlsx files will be in directory ", out_dir, ".", sep='')
		for file in os.listdir(os.getcwd()):
			filename = os.fsdecode(file)
			if filename.endswith('.csv'):
				f(filename, out_dir)
	elif os.path.isfile(in_path):
		f(in_path)
	else:
		print('Input is neither a file nor directory.')

