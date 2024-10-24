# Creating a Color-Coded Voter Preference v Population Map of America 
![The Output and End Goal of this Project!](https://github.com/Pizzanomicon/3d_Voter_Preference_Population_Map/blob/main/images/Americas_Spikey_Voting_2020-v1.04.png)

This project is very much a work in progress.  It has been an educational tool to help me, as a cartography beginner, learn some basic concepts of map making, projection, and R-based raytracing.

Future work will merge this into a single Pythonic solution

## Glossary of Terms:
* FIPS county code - The Federal Information Processing Standards county code is a five-digit number that uniquely identifies a county in the United States.  The first two digits represent the state, the last three the county.
* Choropleth map - A color-filled thematic map that is used to represent statistical data using color mapping symbology within defined boundaries.

## Step 0:  Preperation

Election data from:

MIT Election Data and Science Lab, 2018, "County Presidential Election Returns 2000-2020", https://doi.org/10.7910/DVN/VOQCHQ, Harvard Dataverse, V13; countypres_2000-2020.tab [fileName], UNF:6:KNR0/XNVzJC+RnAqIx5Z1Q== [fileUNF]


* Download, collate, and clean voter data.
  * Not all states sum the voter information into a "total" row
  * Alaska does not/cannot return county data, so it will not be used.
  * ?Delaware? was broken?
* Prepare virtual environments (optional)
  * I prepped two virtual environments using miniconda
  * R 
  * Maps


### todo:
Check that there are no individual counties that are broken, which often tends to be the case straight out of the download.

## Step 1: Make Coropleth
This, ultimately, is the texture map to be used in the last stage of the render.  But x

### requirements:
* python
* plotly



### todo:  
Figure out how to 3D extrusions of FIPs counties in python


## Step 2:  Make Color Scale Legend
Imports a csv file with "HexAdvanced" column containing hex color codes for each county.  (Optional), and generates a legend plotting on a bivariate scale of Republican-Democrat-Third_Party

Largely an exercise in future proofing.  While this is designed to be a semi-circle in the final project, you'll note the code exists to make this a triangle.

### requirements:
* python
* cupy (GPU accelerated)
* matplotlib
* pandas

numpy should be fairly easily to drop in and substitute, if a non cuda-accelerated system needs to run this.

### todo:
* Convert pandas to polars for good practice and speed increase.
* If cupy is not available, fail to numpy

## Step 3:  Make Spike Map

## Further Steps
Not best illustrated here, but should be acknowledged.
### Warp Texture Map in Photoshop
For the time being, the Plotly Albers USA projection is slightly off from the R-based Albers USA projection.  
Modifying the projection in code could solve this, but such a band-aid solution would be wasted time when the end goal is to move out of the R projection anyway.


### Render in Blender

## ToDo
* Transliterate the spike map into python.
* Merge legend into python
  * add alpha to 
* Move Excel processing into python
