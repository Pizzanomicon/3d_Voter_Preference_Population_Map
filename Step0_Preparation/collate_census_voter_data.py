#  collate_census_voter_data.py
#  Phil Warren
#  2024 October 24


## AT THIS TIME I do not have a way to download MIT/Harvard's election data automatically,
## so long as Amazon's S3 Cloud has authentication requirements

'''
This project downloads data and, eventually, cleans and preps a complex file to be mapped later.
While this will include census data, it is unlikely this census data will actually be used at this time.
Use polars, not pandas, for speed.  Please, society, catch up.
'''
#%%
#~ VARIABLES
year_in_focus = 2020

#color_treatment
RB_Decrease_Factor=0.75
G_Growth=0.515625

## census data is unused as of yet.
census_url = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/totals/co-est2023-alldata.csv"
census_file_name = "co-est2023-alldata.csv"

#* https://electionlab.mit.edu/data
#* https://dataverse.harvard.edu/file.xhtml?fileId=8092662&version=13.0&toolType=PREVIEW
voter_url = "https://dvn-cloud.s3.amazonaws.com/10.7910/DVN/VOQCHQ/18cefdb88fa-9581727dda46.orig?response-content-disposition=attachment%3B%20filename%2A%3DUTF-8%27%27countypres_2000-2020.csv&response-content-type=text%2Fcsv&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20241022T204445Z&X-Amz-SignedHeaders=host&X-Amz-Expires=3599&X-Amz-Credential=AKIAIEJ3NV7UYCSRJC7A%2F20241022%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=08b5d39f7bd0dc3e69c6fb652b7f4bbcb10f2eb096cc3ef4df2d17c8877bce02"
voter_file_name = "countypres_2000-2020.csv"
print('#####################################################')
print('# voting data distributed under')
print('# CC0 1.0 Universal deed')
print('# https://creativecommons.org/publicdomain/zero/1.0/')
print('#')
print('# MIT Election Data and Science Lab, 2018, ')
print('# "County Presidential Election Returns 2000-2020", ')
print('# https://doi.org/10.7910/DVN/VOQCHQ, Harvard Dataverse, V13; ')
print('# countypres_2000-2020.tab ')
print('# [fileName], UNF:6:KNR0/XNVzJC+RnAqIx5Z1Q== [fileUNF]')
print('#####################################################')

#%%
# LIBRARY SETUP

import os, sys, subprocess
import shutil
from urllib.request import urlretrieve

#conda create -n maps python numpy=1.26 pandas plotly

# List of required libraries
required_libraries = [
    "geopandas", "requests", "polars", "numpy",
    "gzip", "matplotlib", "plotly"
]

# Function to install missing libraries
def install_missing_libraries(libs):
    import importlib
    for lib in libs:
        try:
            importlib.import_module(lib)
        except ImportError:
            print(f"Installing missing library: {lib}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

# Check and install missing libraries
print("---------Loading libraries-----")
install_missing_libraries(required_libraries)

# Import libraries after ensuring they are installed
import requests
import gzip


import polars as pl
import numpy as np
# import geopandas as gpd
# import matplotlib.pyplot as plt
#from pyproj import CRS  #unnecessary?
# import plotoptix  #unnecessary?
# from matplotlib.colors import ListedColormap

#%%
# Step 1: DOWNLOAD & UNZIP DATA
print("========1. DOWNLOAD & UNZIP DATA")

# Check if the downloaded file exists
def download_csv(url, file_name):
    load_file_name = file_name.replace(".gz", "")  # Vestigial.  In case we're dealing with an archive, which we aren't.
    if os.path.exists(file_name):
        #why is this not detecting countypres_2000_2020.csv all of a sudden?!
        print("☑️",file_name, "is already here, not doing anything in this step...")
    else:
        response = requests.get(url, stream=True)
        file_binary = False
        if file_binary:
            read_mode = 'wb'
        else:
            read_mode = 'wt'
        if response.status_code == 200:
            # with open(file_name, read_mode, encoding='utf-8') as f:  #Trying to avoid using this if I can, keep it agnostic.
            with open(file_name, read_mode ) as f:
                f.write(response.text)
                print("File downloaded and saved as", file_name)
                # shutil.copyfileobj(response.raw, f)  #This is for binary, so... ignore this for now.
        else:
            print("⛔", end='')
            print(" Failed to download:",file_name,f"Status code: {response.status_code}")
            #sys.exit(1)
        
        # Decompression is, to the best of my knowledge, not necessary here.
        ## Leaving this as vestigial in case we wish to port this to a data source that's an archive:
        # print("Decompressing the file...")
        # with gzip.open(file_name, 'rb') as f_in:
        #     with open(load_file_name, 'wb') as f_out:
        #         shutil.copyfileobj(f_in, f_out)
        # print("Decompression complete.")
print("Downloading data...")

download_csv(census_url, census_file_name)
download_csv(voter_url, voter_file_name)

#~ Dataframe manipulation
#%% 
#^ Load CSV   
print("========2. Loading CSVs")
df_census = pl.read_csv(census_file_name)
df_census.head()

#%%
df_voter = pl.read_csv(voter_file_name, dtypes={
    # "year": pl.Utf8,
    "county_fips": pl.Utf8
})
df_voter.head()


#%%
#^ Modify CSVs   
print("========3. Modifying individual CSVs")
# CENSUS ALTERATION
def rgb_to_hex(r, g, b):
    """Converts 8-bit RGB values to a hexadecimal string."""
    return f"#{r:02x}{g:02x}{b:02x}"

#^ Create FIPS by concatenating STATE (2 digits) and COUNTY (3 digits)
df_census = df_census.with_columns(
    (
        pl.col('STATE').cast(pl.Utf8).str.zfill(2) +   # Ensure STATE is 2 digits, padded with zeros
        pl.col('COUNTY').cast(pl.Utf8).str.zfill(3)    # Ensure COUNTY is 3 digits, padded with zeros
    ).alias('COUNTY_FIPS')
)
df_census.head()
#%%
# VOTER ALTERATION
#^ update FIPS to 5 characters
#We're about to see how this strange case progresses.
df_voter = df_voter.with_columns(
    (pl.col('county_fips').cast(pl.Utf8).str.zfill(5)).alias('COUNTY_FIPS')
)
df_voter = df_voter.drop("county_fips")  #I don't want to confuse anything, let's ditch the old fips list.

# Filter rows where 'year' equals 'year_in_focus'
df_voter_yr = df_voter.filter(pl.col("year") == year_in_focus)
df_voter = df_voter.filter(pl.col("year") == year_in_focus) #! Just to be safe...
df_voter_yr.head()
#%%
#^ Mass fix for counties which did not correctly report TOTAL in this database
## We simply need to isolate the COUNTY_FIPS missing TOTAL

#Get a dataframe of unique COUNTY_FIPS values
unique_fips = df_voter_yr.select("COUNTY_FIPS").unique()
# Convert to a list
unique_fips_list = unique_fips["COUNTY_FIPS"].to_list()

# Dictionary to store DataFrames for each unique FIPS
fips_dataframes = {}
# Iterate over each unique FIPS and filter by FIPS code
for fips in unique_fips_list:
    # Filter the main DataFrame for rows matching the current FIPS code
    df_voter_fips = df_voter_yr.filter(pl.col("COUNTY_FIPS") == fips)
    
    # Create three DataFrames based on the 'party' column
    df_voter_democrat = df_voter_fips.filter(pl.col("party") == "DEMOCRAT")
    df_voter_republican = df_voter_fips.filter(pl.col("party") == "REPUBLICAN")
    ### THIRD PARTY
    df_voter_libertarian = df_voter_fips.filter(pl.col("party") == "LIBERTARIAN")
    df_voter_green = df_voter_fips.filter(pl.col("party") == "GREEN")
    df_voter_other = df_voter_fips.filter(pl.col("party") == "OTHER")
    # df_voter_other = df_voter_fips.filter(~(pl.col("party").is_in(["DEMOCRAT", "REPUBLICAN"])))
    
    # Store the DataFrames in a nested dictionary
    fips_dataframes[fips] = {
        "DEMOCRAT": df_voter_democrat,
        "REPUBLICAN": df_voter_republican,
        # "THIRD_PARTY": df_voter_other,
        "LIBERTARIAN_PARTY": df_voter_libertarian,
        "GREEN_PARTY": df_voter_green,
        "OTHER_PARTY": df_voter_other
    }

total_rows_list = []
for fips, parties in fips_dataframes.items():
    # I need to populate the following with the first row for the given fips- how?
    first_party_df = next(iter(parties.values()))  # Extract the first available DataFrame
    try:
        # Get the first row of the first available party DataFrame
        first_fips_row = first_party_df.row(0)
        
        # Now you have access to the first row for this FIPS
        placeholder_year = first_fips_row[0]  # should be the same as year_in_focus, but this is a good sanity check
        placeholder_state = first_fips_row[1]
        placeholder_state_po = first_fips_row[2]
        placeholder_county_name = first_fips_row[3]
        placeholder_office = first_fips_row[5]
        placeholder_totalvotes = first_fips_row[9]
        placeholder_version = first_fips_row[10]

        print(f"Assessing first row for FIPS {fips}: {first_fips_row}")
    except IndexError:
        # Handle the case where the DataFrame is entirely empty, which seems... REAL bad.
        print(f"No data found for FIPS {fips}.", end=' ')
        print('Exiting.'); sys.exit(1)  # Comment out this line to continue in case of a break.
        print("Continuing.")
        continue  # Skip to the next FIPS if no data is found    
    for party, df_voter_party in parties.items():
        # Check if there is a row where 'mode' equals 'TOTAL'
        if not df_voter_party.filter(pl.col("mode") == "TOTAL").shape[0] > 0:
            # If there is no 'TOTAL' row, sum the 'candidatevotes' column
            total_votes = df_voter_party["candidatevotes"].sum()
            
            # Extract the first row to use its values for the columns (except the ones to modify)
            try:
                first_row = df_voter_party.row(0)
                new_row = pl.DataFrame({
                    "year": [first_row[0]],                  # Copy from the first row
                    "state": [first_row[1]],                 # Copy from the first row
                    "state_po": [first_row[2]],              # Copy from the first row
                    "county_name": [first_row[3]],           # Copy from the first row
                    "office": [first_row[5]],                # Copy from the first row
                    "candidate": [first_row[6]],             # Set candidate to "TOTAL"
                    "party": [party],                        # Use current party
                    "candidatevotes": [total_votes],         # Sum of candidatevotes
                    "totalvotes": [first_row[9]],            # Copy totalvotes from first row
                    "version": [first_row[10]],              # Copy version from first row
                    "mode": ["TOTAL"],                        # Set mode to "TOTAL"
                    "COUNTY_FIPS": [fips],                   # Use current FIPS
                })
                print(party + ":  Added total for missing county:", [first_row[3]],"(",[first_row[1]],")")
            except:
                print("Error assessing missing total for:", fips, party)
                print("Filling in a 0-vote row using county fips information")
                #Here we can fill in a row with 0 as the "candidatevotes" cell, maintaining the other data for that particular fips?
                new_row = pl.DataFrame({
                    "year": [placeholder_year],                  # Copy from the first row
                    "state": [placeholder_state],                 # Copy from the first row
                    "state_po": [placeholder_state_po],              # Copy from the first row
                    "county_name": [placeholder_county_name],           # Copy from the first row
                    "office": [placeholder_office],                # Copy from the first row
                    "candidate": ["irrelevant"],             # Set candidate to "TOTAL"
                    "party": [party],                        # Use current party
                    "candidatevotes": [0],         # Sum of candidatevotes
                    "totalvotes": [placeholder_totalvotes],            # Copy totalvotes from first row
                    "version": [placeholder_version],              # Copy version from first row
                    "mode": ["TOTAL"],                        # Set mode to "TOTAL"
                    "COUNTY_FIPS": [fips],                   # Use current FIPS
                })
                print(party + ":  Noted zero votes for county:", [placeholder_county_name],"(",[placeholder_state],")")
        # Filter to keep only the rows where mode equals "TOTAL"
        #total_rows = df_voter_party.filter(pl.col("mode") == "TOTAL")
        # Append the filtered DataFrame (only "TOTAL" row) to the list
        #total_rows_list.append(total_rows)
# Concatenate all the "TOTAL" rows into a single DataFrame
#df_voter_total = pl.concat(total_rows_list)

#^ SANITY CHECK
# hand check the following:
#! 13029:  BRYAN, GEORGIA.  It sure looks like it's missing all third party votes, and didn't have totals for republican or democrat.  This is possibly correct, but smells funny.
#* 48133: EASTLAND, TEXAS.  It looks like this has totals for all five parties?  How cool would that be!?
#%%
#^ INTERLEAVING THESE RESULTS
# Initialize a list to hold the new interleaved rows
interleaved_rows_list = []

# Display the DataFrame containing only the "TOTAL" rows
#print(df_voter_total)

# Iterate over each FIPS and party combination in the nested dictionary
for fips, parties in fips_dataframes.items():
    # Extract the "TOTAL" rows for each party
    df_democrat_total = parties["DEMOCRAT"].filter(pl.col("mode") == "TOTAL")
    df_republican_total = parties["REPUBLICAN"].filter(pl.col("mode") == "TOTAL")
    ###
    df_libertarian_total = parties["LIBERTARIAN_PARTY"].filter(pl.col("mode") == "TOTAL")
    df_green_total = parties["GREEN_PARTY"].filter(pl.col("mode") == "TOTAL")
    df_other_total = parties["OTHER_PARTY"].filter(pl.col("mode") == "TOTAL")
    #
    # df_other_total = parties["THIRD_PARTY"].filter(pl.col("mode") == "TOTAL")
    
    # Ensure all three exist, otherwise skip this FIPS
    # if df_democrat_total.shape[0] > 0 and df_republican_total.shape[0] > 0 and df_other_total.shape[0] > 0:
    if df_democrat_total.shape[0] > 0 and df_republican_total.shape[0] > 0:
        # Extract common columns from one of the total rows (Democrat, Republican, or Other)
        # common_columns = df_democrat_total.row(0)[:5]  # Assuming the first 5 columns are shared
        common_columns = df_democrat_total.row(0)[:5]  # Assuming the first 5 columns are shared
        # Extract candidatevotes from each party's total row
        democrat_votes = df_democrat_total["candidatevotes"].sum()
        republican_votes = df_republican_total["candidatevotes"].sum()
        libertarian_votes = df_libertarian_total["candidatevotes"].sum()
        green_votes = df_green_total["candidatevotes"].sum()
        other_votes = df_other_total["candidatevotes"].sum()
        # If this works, move them down into the pl.DataFrame({}) directly
        third_party_votes = libertarian_votes + green_votes + other_votes
        total_votes = democrat_votes + republican_votes + third_party_votes
        r_8b = int(np.rint((republican_votes/total_votes)*255))
        b_8b = int(np.rint((democrat_votes/total_votes)*255))

        temp1_g_min = min(r_8b,b_8b)
        temp2_g_simple = np.rint((third_party_votes/total_votes)*255)
        g_8b = int(np.rint(temp1_g_min + ((third_party_votes/total_votes)*255)))
        hexcolor = rgb_to_hex(r_8b,g_8b,b_8b)
        rb_diff = np.abs(r_8b - b_8b)
        
        this_rb_decrease = ((255-rb_diff)/255)*RB_Decrease_Factor
        r_adv = int(np.clip(r_8b-np.rint(this_rb_decrease*temp2_g_simple), 0, 255))
        g_adv = int(np.clip(temp1_g_min + np.rint(G_Growth * temp2_g_simple), 0, 255))
        b_adv = int(np.clip(b_8b - np.rint(this_rb_decrease*temp2_g_simple), 0, 255))
        hexcolor_adv = rgb_to_hex(r_adv,g_adv,b_adv)
        #hexcolor_adv = '%02x%02x%02x' % (int(r_adv), int(g_adv), int(b_adv))
        # Create a new row with the common columns and the interleaved vote columns
        interleaved_row = pl.DataFrame({
            "COUNTY_FIPS": [fips],                      # it nows what it is.
            "STATE_NAME": [common_columns[1]],               # Copy state
            "STATE_PO": [common_columns[2]],            # Copy state_po
            "COUNTY_NAME": [common_columns[3]],         # Copy county_name
            "YEAR": [common_columns[0]],                # Copy year (Sanity Check)
            "REPUBLICAN_VOTES": [republican_votes],     # Republican votes
            "DEMOCRAT_VOTES": [democrat_votes],         # Democrat votes
            "LIBERTARIAN_VOTES": [libertarian_votes],
            "GREEN_VOTES": [green_votes],
            "OTHER_VOTES": [other_votes],               # Other (third-party) votes
            "THIRD_PARTY_VOTES": [third_party_votes],
            "MODE": ["interleaved"],                     # Set mode to "interleaved" as a sanity check.
            # We can store more here if need be, but leaving these commented out for now
            #"HEX_SIMPLE": [hexcolor],
            #"RB_DIFF": [rb_diff],
            #"RB_Decrease_Factor": [((255-rb_diff)/255)*RB_Decrease_Factor],
            #"R_8B_SIMPLE": [r_8b],
            #"G_8B_SIMPLE": [g_8b],
            #"B_8B_SIMPLE": [b_8b],
            #"R_8B_ADV": [r_adv],
            #"G_8B_ADV": [g_adv],
            #"B_8B_ADV": [b_adv],
            "HEX_ADVANCED": [hexcolor_adv]
        })

        # Append the new interleaved row to the list
        interleaved_rows_list.append(interleaved_row)

# Concatenate all interleaved rows into a single DataFrame
df_voter_interleaved = pl.concat(interleaved_rows_list)

df_voter_interleaved.head()

#%%
#^ Sort by the 'COUNTY_FIPS' column and export
df_voter_interleaved = df_voter_interleaved.sort("COUNTY_FIPS")
df_voter_interleaved.write_csv("df_voter_interleaved_241023_1404.csv")

#%%
#^ Force quotation marks around every cell value, 
# Polars does not currently support a direct option for this. 
# However, you can achieve this by post-processing the CSV file with Python's built-in csv module, 
# which allows you to customize quoting.
# This patch is as follows:

# import csv
# with open("troubleshooting_no_quotes.csv", "r", newline='', encoding='utf-8') as infile, \
#     open("troubleshooting.csv", "w", newline='', encoding='utf-8') as outfile:
#     reader = csv.reader(infile)
#     writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)  # Force quotes around all cells
#     for row in reader:
#         writer.writerow(row)
# print("CSV with forced quotes written to 'troubleshooting.csv'")
#%%
#^ Fix Oglala Lakota County, SD (46102) / Shannon County, SD (46113)
# Shannon County, SD (FIPS code = 46113) was renamed Oglala Lakota County and assigned anew FIPS code (46102) effective in 2014.
# Because this process should work regardless of time period analyzed, we're going to duplicate one and place it into the other.

#If FIPS "46113" exists, I would like to make an exact copy of all rows with this FIPS code, replacing the "county_name" entry with "OGLALA LAKOTA" and the "COUNTY_FIPS" entry with "46102"
if df_voter_interleaved.filter(pl.col("COUNTY_FIPS") == "46113").shape[0] > 0:
    #If Shannon County exists in the map, copy it into Oglala Lakota County
    df_voter_fips_46113 = df_voter_interleaved.filter(pl.col("COUNTY_FIPS") == "46113")
    df_voter_fips_46113_modified = df_voter_fips_46113.with_columns([
        pl.lit("OGLALA LAKOTA").alias("COUNTY_NAME"),   # Replace county_name with "OGLALA LAKOTA"
        pl.lit("46102").alias("COUNTY_FIPS")            # Replace COUNTY_FIPS with "46102"
    ])

    df_voter_interleaved_updated = pl.concat([df_voter_interleaved, df_voter_fips_46113_modified])
    print('Shannon County was referenced:  Copied into Oglala Lakota County')
else:
    #Otherwise, copy Oglala Lakota County, SD into Shannon County, SD
    df_voter_fips_46102 = df_voter_interleaved.filter(pl.col("COUNTY_FIPS") == "46102")
    df_voter_fips_46102_modified = df_voter_fips_46102.with_columns([
        pl.lit("SHANNON").alias("COUNTY_NAME"),         # Replace county_name with "SHANNON"
        pl.lit("46113").alias("COUNTY_FIPS")            # Replace COUNTY_FIPS with "46113"
    ])

    df_voter_interleaved_updated = pl.concat([df_voter_interleaved, df_voter_fips_46102_modified])
    print('Oglala Lakota County was referenced:  Copied into Shannon County County')
# From here on out we need to look for df_voter_interleaved_updated

#%% 
#^ PATCH CONNECTICUT
# There's only 8 voting counties
# 09001 Fairfield
# 09003 Hartford
# 09005 Litchfield
# 09007 Middlesex
# 09009 New Haven
# 09011 New London
# 09013 Tolland
# 09015 Windham

# However the census isn't collected in the same sense
# 09170 South Central Connecticut Planning Region
# 09120 Greater Bridgeport Planning Region
# 09160 Northwest Hills Planning Region
# 09190 Western Connecticut Planning Region
# 09150 Northeastern Connecticut Planning Region
# 09130 Lower Connecticut River Valley Planning Region
# 09140 Naugatuck Valley Planning Region
# 09180 Southeastern Connecticut Planning Region

# This cannot correctly be rectified 
#%% 
#^ PATCH KANSAS CITY MISSOURI
## I'd like to know what's going on here.


#%% 
#^ PATCH DELAWARE
# I've seen no evidence this is even a problem yet.

#%%
#^ PATCH FLORIDA
# In the past this has been an issue.  Just leaving it in here for now.

#%% 
#^ PATCH Kalawao County Hawaii
# There's 81 people in this county.  It really doesn't matter, but I want to be complete.



#%%
#^ COMBINE VOTING WITH CENSUS DATA
## This step is completely and totally unecessary, but it could be useful for later.
## It will also help troubleshoot errant counties.

# Create 'COUNTY_FIPS' in df_census by concatenating 'STATE' and 'COUNTY'
df_census = df_census.with_columns(
    (pl.col('STATE').cast(pl.Utf8).str.zfill(2) + pl.col('COUNTY').cast(pl.Utf8).str.zfill(3)).alias('COUNTY_FIPS')
)

# Perform a full outer join on 'COUNTY_FIPS', keeping all rows
df_merged = df_voter_interleaved_updated.join(df_census, on='COUNTY_FIPS', how='full')

# Create the `_merge` column to indicate the source of each row
#! Somewhat unclear in polars documentation, but the conditional results need to wrap strings in pl.lit()
#! Otherwise, polars lazy loading will assume the string is a (missing) column reference
df_merged = df_merged.with_columns(
    pl.when(pl.col(df_voter_interleaved_updated.columns[0]).is_null())  # If the first column of voter is null, it came from census
    .then(pl.lit("census_only"))
    .when(pl.col(df_census.columns[0]).is_null())  # If the first column of census is null, it came from voter
    .then(pl.lit("voter_only"))
    .otherwise(pl.lit("both"))  # Otherwise, it came from both
    .alias('_merge')
)
#^ OUTPUT VERSIONING
# Anything generated by hand is v1.x
# Anything generate by this file is v2.xx
# Anything generated by the (later) all-in-one script is v3.xx
df_merged.write_csv('nation_data_v2.00.csv')

# Filter for rows that are left-only (voter data only)
df_voter_only = df_merged.filter(pl.col('_merge') == 'voter_only').select(df_voter_interleaved_updated.columns)
df_voter_only.write_csv('voter_only.csv')

# Filter for rows that are right-only (census data only)
df_census_only = df_merged.filter(pl.col('_merge') == 'census_only').select(df_census.columns)
df_census_only.write_csv('census_only.csv')

# Filter for rows that exist in both (merged data)
df_shared_data = df_merged.filter(pl.col('_merge') == 'both')
df_shared_data.write_csv('shared_national_data.csv')

print("Files saved: 'voter_only.csv', 'census_only.csv', 'shared_national_data.csv', 'merged_national_data.csv'")

