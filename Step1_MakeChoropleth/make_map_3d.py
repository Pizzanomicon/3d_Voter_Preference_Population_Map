import trimesh
from shapely.geometry import Polygon, MultiPolygon
import numpy as np
import matplotlib.colors as mcolors
import polars as pl
import geopandas as gpd


# Load your dataset with COUNTY_FIPS, HEX_ADVANCED, and POPESTIMATE2020
df = pl.read_csv('path_to_data.csv')


# Create an empty Trimesh scene to hold the extrusions
scene = trimesh.Scene()

# Helper function to convert HEX to RGB
def hex_to_rgb(hex_color):
    return [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]

# Iterate through each county in the merged dataframe
for _, row in merged_df.iterrows():
    geom = row['geometry']  # Shapely geometry object (Polygon or MultiPolygon)
    pop = row['POPESTIMATE2020']  # Extrusion height based on population
    color = hex_to_rgb(row['HEX_ADVANCED'])  # County color as RGB

    if isinstance(geom, Polygon):
        polys = [geom]
    elif isinstance(geom, MultiPolygon):
        polys = list(geom)
    else:
        continue

    # Iterate through the individual polygons
    for poly in polys:
        # Convert the exterior of the polygon into a 3D mesh
        exterior_coords = np.array(poly.exterior.coords)
        base_height = 0  # Ground level
        top_height = pop * 0.00001  # Scale population to create extrusion height

        # Create the base and top faces of the extrusion
        base_face = trimesh.path.polygons.to_polygon(exterior_coords)
        top_face = base_face.copy()
        top_face.apply_translation([0, 0, top_height])

        # Create a 3D prism by connecting base and top faces
        extrusion = trimesh.creation.extrude_polygon(base_face, height=top_height)

        # Set the color for the entire county extrusion
        extrusion.visual.face_colors = np.tile(color + [255], (extrusion.faces.shape[0], 1))

        # Add the extrusion to the Trimesh scene
        scene.add_geometry(extrusion)

# After adding all extrusions, export the scene to OBJ format
scene.export('us_counties_3d.obj')
import trimesh
from shapely.geometry import Polygon, MultiPolygon
import numpy as np
import matplotlib.colors as mcolors

# Create an empty Trimesh scene to hold the extrusions
scene = trimesh.Scene()

# Helper function to convert HEX to RGB
def hex_to_rgb(hex_color):
    return [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]

# Iterate through each county in the merged dataframe
for _, row in merged_df.iterrows():
    geom = row['geometry']  # Shapely geometry object (Polygon or MultiPolygon)
    pop = row['POPESTIMATE2020']  # Extrusion height based on population
    color = hex_to_rgb(row['HEX_ADVANCED'])  # County color as RGB

    if isinstance(geom, Polygon):
        polys = [geom]
    elif isinstance(geom, MultiPolygon):
        polys = list(geom)
    else:
        continue

    # Iterate through the individual polygons
    for poly in polys:
        # Convert the exterior of the polygon into a 3D mesh
        exterior_coords = np.array(poly.exterior.coords)
        base_height = 0  # Ground level
        top_height = pop * 0.00001  # Scale population to create extrusion height

        # Create the base and top faces of the extrusion
        base_face = trimesh.path.polygons.to_polygon(exterior_coords)
        top_face = base_face.copy()
        top_face.apply_translation([0, 0, top_height])

        # Create a 3D prism by connecting base and top faces
        extrusion = trimesh.creation.extrude_polygon(base_face, height=top_height)

        # Set the color for the entire county extrusion
        extrusion.visual.face_colors = np.tile(color + [255], (extrusion.faces.shape[0], 1))

        # Add the extrusion to the Trimesh scene
        scene.add_geometry(extrusion)

# After adding all extrusions, export the scene to OBJ format
scene.export('us_counties_3d.obj')
