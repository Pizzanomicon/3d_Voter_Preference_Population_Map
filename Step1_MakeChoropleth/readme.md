# Choropleth_Mapper
make_map_advanced.py

This can create 6 different maps (though state is unfinished/unrealized) to illustrate county voting preference in:
* "no_color"           ## Just the lines, ma'am.
* "state_binary"       ## Which delegate won the election? (Can't work because of 2 states)
* "county_binary"      ## Which delegate won the election?
* "county_purple"      ## On a scale of red to blue, what did voters prefer?
* "county_negated"     ## On a scale of red to gray to blue, what did voters prefer?
* "county_philnegated" ## On a bivariate scale of red-to-gray-to-blue for rep/dem, pulling green for other, what did voters prefer?


_My first attempt at making a map with python._

## intended to be run in env: maps
yaml to come.

# Initially from:
https://plotly.com/python/county-choropleth/

Note we use FIPS to give a value to each county, which makes sense, and will give us an easy way to associate depth.

## MAKING THE CSV
### this doesn't really have to be noted here, but felt like I should note it somewhere.
DOWNLOAD CENSUS DATA

This was an avenue that did not end up being used, but good to understand that it exists.

https://www.census.gov/data/tables/time-series/demo/popest/2020s-counties-total.html
https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/totals/co-est2023-alldata.csv

DOWNLOAD VOTING DATA

https://electionlab.mit.edu/data
https://dataverse.harvard.edu/file.xhtml?fileId=8092662&version=13.0&toolType=PREVIEW

#Install these:
pip install plotly-geo==1.0.0
pip install geopandas==0.8.1
pip install pyshp==2.1.2
pip install shapely==1.7.1   #! FAILED?!  But a differing version was already installed, so perhaps we can ignore this.
'''

# COLORATION
Using an offshoot of Larry Weru and Teddy the Bear's "neutralized gray" map, replacing the purple map for visual clarity.
https://medium.com/matter/the-trouble-with-the-purple-election-map-31e6cb9f1827
https://imgur.com/Id3fU
