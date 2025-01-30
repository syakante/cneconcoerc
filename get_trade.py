import argparse
from concurrent.futures import ThreadPoolExecutor
from time import sleep

try:
	import pandas as pd
	import comtradeapicall
except ImportError:
	import pip
	pip.main(['install', '--user', 'pandas'])
	import pandas as pd
	pip.main(['install', '--user', 'urllib3'])
	pip.main(['install', '--user', 'comtradeapicall'])
	import comtradeapicall


with open('apikey.txt', 'r') as f:
	my_key = f.read()

# with ThreadPoolExecutor() as exe:
# 	threads = exe._max_workers

my_colnames = ['refYear','flowDesc','reporterDesc','partnerDesc','cmdCode','cmdDesc','primaryValue']

def pretty_call(year:int, flow:str, partners:str, count_only=False, preview=False, code='AG6'):
	if preview:
		return(comtradeapicall.previewFinalData(typeCode='C', freqCode='A', clCode='HS', period=str(year),
									reporterCode='156', cmdCode=code, flowCode=flow, partnerCode=partners, partner2Code="0",
									customsCode=None, motCode=None, maxRecords=500, format_output='JSON',
									aggregateBy=None, breakdownMode='plus', countOnly=count_only, includeDesc=False))
	return(comtradeapicall.getFinalData(subscription_key = my_key,
									typeCode='C', freqCode='A', clCode='HS', period=str(year),
									reporterCode='156', cmdCode=code, flowCode=flow, partnerCode=partners, partner2Code="0",
									customsCode=None, motCode=None, maxRecords=None, format_output='JSON',
									aggregateBy=None, breakdownMode='plus', countOnly=count_only, includeDesc=True))

def mx_string(s):
	if(s == 'M'):
		return 'import'
	if(s == 'X'):
		return 'export'
	if(s == 'M,X' or s == 'X,M'):
		return 'imp_exp'
	else:
		return s

def stringify_code(code:int):
	s = str(code)
	n = len(s)
	if(n < 6):
		diff = 6-n
		s = diff*'0' + s
	return(s)

def get_import_yr(year:int, countries_list, count_only = False):
	#flow is M (import) or X (export)
	#technically you can do M,X but for our purposes we won't.
	#countries_list is list of country codes List[int]
	countries_list = [0] + countries_list
	countries = ','.join([str(x) for x in countries_list])
	print("Getting trade data for", str(year), 'countries', countries_list[1], "-", countries_list[-1], "...")
	tmp = pretty_call(year, 'M', countries, True, True)
	
	print("Found", tmp['count'][0], "entries.")
	if count_only:
		return(tmp)

	df = pretty_call(year, 'M', countries)
	#need error catch if result is None wtf
	if df is None:
		print("Server side error while getting imports", countries[1:])
		print("(Probably rate limit, waiting and trying again...)")
		#idt theres any way to error handle this correctly.
		#due to no error returned (lmao) and even if I check print output or sth theres multithreading
		sleep(11)
		df = pretty_call(year, 'M', countries)
		if df is None:
			print("Error.")
			df = pd.DataFrame([],columns=my_colnames)
	
	df = df[my_colnames]
	return df

#worlds worst error handling
#bc the py api doesn't return an error it just prints it -_-

def get_export_yr(year:int, codes:str, count_only = False):
	df = pretty_call(year, 'X', '0', count_only = count_only, code=codes)
	if df is None:
		print("Server side error while getting exports.")
		counter = 0
		flag = True
		while(flag or counter < 3):
			print("(Probably rate limit, waiting and trying again...)")
			sleep(10)
			df = pretty_call(year, 'X', '0', count_only = count_only, code=codes)
			flag = (df is None)
			counter += 1
		if df is None:
			print("Error.")
			if count_only:
				return(pd.DataFrame([0],columns=['count']))
			df = pd.DataFrame([], columns=my_colnames)
	if count_only:
		print("Found", df['count'][0], "entries.")
		return(df)
	df = df[my_colnames]
	return(df)

def chunks(L, n):
	k, m = divmod(len(L), n)
	return (L[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def main(year:int, countries_list, count_only=False, all_products=False):
	if(len(countries_list) > 4):
		args_L = [(year, i, count_only) for i in list(chunks(countries_list, 4))]
	else:
		args_L = [(year, i, count_only) for i in list(chunks(countries_list, len(countries_list)))]
	#4 is just arbitrary tbh
	#print(args_L)
	with ThreadPoolExecutor(4) as executor:
		futures = [executor.submit(get_import_yr, *args) for args in args_L]
		results = [fut.result() for fut in futures] #list of DataFrames
	df = pd.concat(results, ignore_index=True)
	
	if count_only:
		return(df)
	####
	if not(all_products):
		#removing products where there is no trade dependency > 70%
		#this is defined by sum of selected countries cuz collective resilience
		not_world = df.loc[df['partnerDesc'] != 'World', ['cmdCode', 'primaryValue']].groupby('cmdCode').sum().reset_index()
		world_val = df.loc[df['partnerDesc'] == 'World', ['cmdCode', 'primaryValue']].drop_duplicates(ignore_index=True)
		merged = pd.merge(not_world, world_val, on='cmdCode', how='left')
		filtered_codes = merged.loc[merged['primaryValue_x'] >= 0.7 * merged['primaryValue_y'], 'cmdCode']
		df = df[df['cmdCode'].isin(filtered_codes)]
	#print(tmp, df.shape)
	####
	print("waiting for rate limit...")
	sleep(10)

	keep_codes_L = [stringify_code(x) for x in df['cmdCode'].unique().tolist()]
	print(len(keep_codes_L))
	# print(threads)
	# args_L = [(year, ','.join(i), count_only) for i in list(chunks(keep_codes_L, threads))]
	# with ThreadPoolExecutor(threads) as executor:
	# 	futures = [executor.submit(get_export_yr, *args) for args in args_L]
	# 	results = [fut.result() for fut in futures]
	#I fucking give up :joy:
	keep_codes = [','.join(i) for i in list(chunks(keep_codes_L, 10))]
	#also arbitrary
	results = []
	for i in range(len(keep_codes)):
		results.append(get_export_yr(year, keep_codes[i]))
		print("waiting for rate limit...")
		sleep(10)

	df_exp = pd.concat(results, ignore_index=True)

	if count_only:
		return(pd.concat(df,df_exp))
	
	imp_codes = set(df['cmdCode'])
	exp_codes = set(df_exp['cmdCode'])
	zero_exp = imp_codes - exp_codes
	tmp = { 'refYear': year, 'flowDesc': 'Export', 'reporterDesc':'China', 'partnerDesc':'World', 'primaryValue': 0 }
	z_exp_df = pd.DataFrame({'cmdCode': list(zero_exp), **tmp})
	tmp_d = df.drop_duplicates('cmdCode').set_index('cmdCode')['cmdDesc'].to_dict()
	z_exp_df['cmdDesc'] = z_exp_df['cmdCode'].map(tmp_d)
	out = pd.concat([df, df_exp, z_exp_df], ignore_index=True)
	return(out.drop_duplicates())

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Get a CSV file of selected imports and exports from China for a given year.")
	parser.add_argument("year", type=int, help="Year to query (required).")
	parser.add_argument("--file", nargs='?', default="country_codes.csv", help="Filepath to headerless CSV with countries and their codes. Default country_codes.csv")
	parser.add_argument("-a", "--all_products", action="store_true", help="Query all products instead of only those with >70% trade dependency (optional)")
	parser.add_argument("-c", "--count_only", action="store_true", help="Only count the number of entries and not the entries themselves (optional)")
	args = parser.parse_args()
	year = args.year
	filepath = args.file
	all_prod = args.all_products
	count_only = args.count_only

	country_codes = pd.read_csv(filepath,header=None)
	country_L = country_codes.iloc[:,1].tolist()

	ret = main(year, country_L, count_only, all_prod)
	if(count_only):
		print("Up to", ret['count'].sum(), "commodities.")
	else:
		filename = str(year) + '_imports_exports_' + str(country_L[0]) + '-' + str(country_L[-1]) + '.csv'
		ret.to_csv(filename, index=False)
		print("Wrote to", filename)