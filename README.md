## get_trade.py

1. Open Windows Powershell by opening an Explorer window in this directory
   and clicking File > Open Windows Powershell.
2. Type	`python get_trade.py <year>` Example: `python get_trade.py 2023`
3. Wait for the script to finish running. It can take a while.
4. That's it!

Important note: This script does the following automatically:
  - Remove products where the sum of import values from the selected countries is less than 70% of the total World import value.
  - Add rows for products that China imported but did not export with value = 0.

Also, UN Comtrade only uses the classification "HS (As Reported)", which means the product codes aren't standardized across years, which may become an issue.

Some other ways you can use the CLI:

`python get_trade.py <year> --file my_file.csv`

`my_file.csv` should be a CSV with no column names and the country, country code of the countries you want to include. By default, it's the file `country_codes.csv` that came with this folder.

`python get_trade.py <year> -a`

Include the -a flag if you want to query all products and not only products	that have >=70% trade dependency.

`python get_trade.py <year> -c`

Include the -c flag if you want to test how many entries you would get for that	year and list of countries.

## convert_to_h0.py

Input: trade data from get_trade.py or calc_pct.py

Output: same data but with the cmdCodes updated to H0

## calc_pct.py

`python calc_pct.py <your file or directory> <optional folder for outputs>`

Using the .csv output from get_trade.py, create an .xlsx file with trade dependency percentages by product and country on one sheet and total import and export values on the second sheet for a given year. If the input is a directory, runs this script on all .csv files in the directory. The default output folder for directory input is `/trade_pcts/`.

This script uses the column names from the output of get_trade.py. Specifically:
```
	'partnerDesc': country imported/exported to.
	'flowDesc': Either 'Import' or 'Export'.
	'reporterDesc': For our purposes, this should just be 'China'.
	'refYear': Year of data.
	'primaryValue': Trade value.
	'cmdCode': Commodity code.
```
Examples:

`python calc_pct.py 2023_imports_exports.csv`

`python calc_pct.py folder_of_data`

`python calc_pct.py input_folder output_folder`

# Data dictionary

`HS1988_codes_chapter_sections.xlsx`

This Excel workbook contains three sheets with information for the 6-digit Harmonized System (HS) 1988 product codes. The levels of categorization from larger to more specific are section, chapter, product code. The first sheet contains each 6-digit product’s chapter, section, 1988 HS code, and description.  The second sheet maps chapter number to description. The third sheet maps section number to description. This sheet is used to read the three related tables productCodes, chapter, and section into Power BI.

`productCodes`

This table is the first sheet of product information from the Excel workbook for the columns chapterCode, productCode, productDesc, and sectionCode.
The calculated column productInData makes a Boolean value for each product on whether or not the product appears in the trade data we are using in the report. This allows us to omit products with no trade data in the dropdowns to search by product in the report.

The calculated column isCriticalMineral makes a Boolean value for each product on whether or not the product appears in the list of critical minerals from critical_minerals_list.csv. This allows us to make a slicer button to filter by critical minerals in the report.

The measure graphTitle is used to change the title of the graph in the “by product” report based on which product is selected.

`chapter`

This table contains each chapter’s code and description.

The calculated column code_desc concatenates the code and description so that both are visible in the dropdown to search by chapter.

`section`

This table contains each section’s code and description.

The calculated column code_desc concatenates the code and description so that both are visible in the dropdown to search by chapter.

The chapter and section tables are related to the productCodes table by their respective codes in one-to-many relationships (multiple products can have the same chapter or section code).

`countries.csv`

This CSV file contains the countries that are either a member of G7+Australia or are listed to be a collective resilience partner. Countries that are neither are not in this spreadsheet. The list of all distinct countries present in the data is generated when creating the main table. 

`critical_minerals_list.csv` -> `critical_minerals_list`

This single-column CSV file contains the product codes of critical minerals.

`prod_country_trade_combined.csv`, `countries.csv`, `main.R`

These three files are used to create the main table in the Power BI file. See the R file to see what exactly it does. At a high level, it creates the list of distinct countries present in the data, inserts rows of trade values to make sure that each product’s percentages sum to 100%, and inserts rows to represent the collective trade values for the G7+Aus and partner categories. These added rows are assigned to the country “Other”.

`main `

Each row contains the trade data for a given country, product code, and year. That is, each row tells that China imported trade_value worth of productcode from country in year, and that trade_value made up trade_percent of China’s imports of that product that year.

Not all products have trade data for all years.

`countries`

This table contains information for each country, namely whether or not they are in the G7+Aus and collective resilience categories. The _label columns are for being displayed on the slicer buttons.

The calculated column sortOrder (and table countriesSort) is used so that the legend in the “by product” graph isn’t sorted in alphabetical order and instead by each country’s total trade volume.

The measure TTTitle is used to title the mouse-over tool tip visual in the “by country” page.

`domestic_reliance2021.xlsx`  -> `domesticReliance `

This Excel workbook contains information about the ratios and differences between China’s imports and exports of each product in 2021.

Each row contains information on how much China imported and exported that product in 2021. The trade records sometimes list China exporting to themselves, which, if present, is subtracted from China’s total world export when used in calculations.

The import_trade_vol_ratio column is calculated as import — (export — China “exports” to itself) divided by the sum of import and export. A ratio of -1 means that China imports 0 this product, while a ratio of 1 means that China exports 0 of this product.

The domestic_reliance measure essentially ranks the products based on how much more China exports than imports the product. It is calculated as the output of a three-dimensional function where the two variables are import—export (x) and export (y). f(x,y) will be our domestic reliance measure that ranges from 0 to 1. For high values of import-export (x-axis in the figure), i.e. China is dependent on importing from other countries, the domestic reliance measure should also be high (1). When China exports more than imports, the measure should be low (0). I used import-export instead of just import because otherwise it would prioritize any import value as long as export=0 regardless of what the import value was. If China exports a lot of the product (y-axis), even if import-export is large, the product still isn’t as important to us because China could self-rely for this product.

Letting x = export, y = import-export, X = set of all export values and Y = set of all import values, the calculation for the measure is as follows:

`(1-(x-min⁡(X))/(max⁡(X)-min⁡(X) ))∙(y-min⁡(Y))/(max⁡(Y)-min⁡(Y))`
 
You can see calculations for this measure in the file domestic_realiance_calculated.xlsx workbook. In the workbook, subtraction of China’s exporting-to-self is used in the calculation, but I omitted it in this document for brevity.
The columns from domestic_reliance_2021.xlsx are used in the domesticReliance table in the Power BI file.

### Calculated tables

`aggregations`

Calculated values for each product code over both years.

Ratio is the aforementioned import_trade_vol_ratio value. Ratio2 is a Boolean value of whether this value is greater than 0. I don’t remember where I used this.

TotalVol measures the total import value for that product. The calculation excludes collective group values such as “G7 + Aus” and “Partner countries” to avoid double-counting when summing trade values. It’s used to filter products by how much of it China imports.

MaxPct does similar, but with trade percent, and includes the collective summed percentages (since the max function doesn’t sum). It’s used to filter out products by maximum import reliance percentage.

`X axis`

This is used to select the X axis of the graph in the “by product” page of the report. It was generated by going to Report view > Modeling tab > New parameter.
