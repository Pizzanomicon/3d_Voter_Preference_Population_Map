# make_map_simple.py
import pandas as pd
import plotly.express as px
import numpy as np #Just to calculate the winner
'''
A choropleth
'''

#! BUGS

#!// Connecticut is Missing
# It's because census data doesn't use FIPS in Connecticut
# Rebuilding manually.
# Using Region 3, which may be inaccurate, but I think is correct.

#!// SALT LAKE CITY IS BLACK?!
# Ironic, in many ways.
# This was the only county in Utah missing a TOTAL field, for some strange reason.

#!// Is there a hole in Utah?
# Nope.  It's the great salt lake.

#! One county in South Dakota is missing.
# Oglala Lakota (46102)
#? Is this disputed?  Does Oglola Lakota voting district have a different FIP?
# Everything is in order.  Which leads me to believe the json did not update the fip in 2014 when this changed.

#! There seem to be a few... suspect spots in Florida
# No idea why these are missing.  But they're fixed.
#// 12001
#// 12003
#// 12005
#// 12007

#!// DELAWARE
#// 10001
#// 10003
#// 10005

#! How can we patch Alaska?
#Ultimately I WANT to map alternate voting district fips onto this...

# TODO
# todo : Fix scale on left
# todo : Hide scale when irrelevant.



#~ Maptypes
## Last one wins!
maptype = "no_color"           ## Just the lines, ma'am.
maptype = "state_binary"       ## Which delegate won the election? (Can't work because of 2 states)
maptype = "county_binary"      ## Which delegate won the election?
maptype = "county_purple"      ## On a scale of red to blue, what did voters prefer?
maptype = "county_negated"     ## On a scale of red to gray to blue, what did voters prefer?
maptype = "county_philnegated" ## On a bivariate scale of red-to-gray-to-blue for rep/dem, pulling green for other, what did voters prefer?

#~ Load the CSV file into a DataFrame
df = pd.read_csv('nation_data_v1.4.csv')
# Convert the COUNTY_FIP to string to match the geojson format
df['COUNTY_FIP'] = df['COUNTY_FIP'].astype(str).str.zfill(5)


#~ ESTABLISH CONSTANTS AND CLEAN DATA A LITTLE
my_title = "Voter Preference - 2020 Presidential Election"
my_projection = "albers usa"
my_marker_width = .5  #Recommended .5 for on.
## WINNER COLUMN
#! Technically, a tie would go to a Republican with this code.  Doesn't matter in practice, though.
df['WINNER'] = np.where((df['DEMOCRAT'] < df['REPUBLICAN']), "Republican", "Democrat")
## NICELY FORMATTED COUNTY, STATE
df['NICE_TEXT'] = df['CTYNAME'] + ", " + df['STNAME']
## NICELY FORMATTED VOTING REPORT
df['VOTING_REPORT'] = "<br>"+ 'Republican Votes:' + df['REPUBLICAN'].astype(str) + "<br>" + 'Democrat Votes:' + df['DEMOCRAT'].astype(str) + "<br>" + "Winner: " + df['WINNER']
# Inject the # sign into the HexCode column
df['HexCode'] = df['HexCode'].apply(lambda x: f'#{x}')
df['RGB_STRING'] = 'rgb(' + df['8B_R'].astype(str) + "," + df['8B_G'].astype(str) + "," + df['8B_B'].astype(str) + ')'

#^ Working with color:  Map hexcode to a list of some sort
# This will only be used in county_philnegated.  It is my white whale.
# From hell's heart I stab at thee!
custom_colors = df['HexCode'].tolist()
custom_rgb = df['RGB_STRING'].tolist()

my_discrete_color_sequence = None  # Unsetting this so we don't get strange errors when forms that aren't county_philnegated call it.
my_color_discrete_map = None 

#~ MAP TYPE SPECIFIC FUNCTIONS
if maptype == "no_color":
    #! TODO:  FLESH THIS OUT.
    # Is there a recorded place where the state winner is written in the spreadsheet?
    my_color = '8B_B'
    my_scale = ['white', 'white']


if maptype == "state_binary":
    #! TODO:  FLESH THIS OUT.
    # Is there a recorded place where the state winner is written in the spreadsheet?
    # How do we handle Main and Nebraska??? #* https://www.270towin.com/content/split-electoral-votes-maine-and-nebraska/
    my_color = 'WINNER'
    my_scale = ['rgb(255, 0, 0)', 'rgb(0, 0, 255)']

if maptype == "county_binary":
    my_color = 'WINNER'
    my_scale = ['rgb(255, 0, 0)', 'rgb(0, 0, 255)']

if maptype == "county_purple":
    my_color = '8B_B'
    my_scale = [
        [0, 'rgb(255, 0, 0)'], #Red
        [1.0, 'rgb(0, 0, 255)'] #Blue
        ]

if maptype == "county_negated":
    my_color = '8B_B'
    my_scale = [
        [0, 'rgb(255, 0, 0)'], #Red
        # [0.2, 'rgb(255, 128, 128)'], #Perceptual 50% saturation
        [0.5, 'rgb(127, 127, 127)'],
        # [0.8, 'rgb(128, 128, 255)'], #Perceptual 50% saturation
        [1.0, 'rgb(0, 0, 255)'] #Blue
        ]
    
if maptype == "county_philnegated":
    custom_color_map = dict(zip(df['COUNTY_FIP'], df['HexCode']))
    my_scale = None
    my_color = 'COUNTY_FIP' #Will immediately be overwritten
    my_color_discrete_map = custom_color_map

# Create a Choropleth map
fig = px.choropleth( #? should this be choropleth_map?
                    df,
                    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
                    locations='COUNTY_FIP',
                    # showticklabels = False,
                    color = my_color,
                    color_continuous_scale = my_scale,
                    color_discrete_map = my_color_discrete_map,
                    # color_discrete_sequence = my_discrete_color_sequence,
                    # Later we can expand this, perhaps from: #* https://community.plotly.com/t/how-to-add-info-to-hover-name-in-y-unified-mode/79204/3
                    hover_name='NICE_TEXT',
                    hover_data=['VOTING_REPORT'],
                    projection=my_projection
                    )

# Update the layout for better visualization
fig.update_traces(
    marker_line_width=my_marker_width,
    # legend="legend2"
    )
fig.update_layout(
    title_text=my_title, 
    title_x=0.5,
    title_y=0.97,
    title_font_family="Times New Roman",
    title_font_size=50,
    geo = dict(showlakes=False),
    coloraxis_colorbar = dict(
        #* https://stackoverflow.com/questions/63094039/plotly-express-can-you-manually-define-legend-in-px-choropleth
        # This is a bit of a mess.  Doesn't matter too much, but obnoxious.
        title="Voter Preference",
        tickvals=[7,115,227],
        ticktext=[ "Republican", "No Preference", "Democrat"],
        )
    )

# Show the figure
fig.show()
