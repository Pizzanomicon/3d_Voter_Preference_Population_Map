#######################################################
#                 Making crisp spike maps with R
#                 Milos Popovic
#                 2023/03/12
#                 Altered by Phil Warren to address bugs
#                 2024/09/26
########################################################

library(albersusa)
libs <- c(
    "tidyverse", "R.utils",
    "httr", "sf", "stars",
    "rayshader"
)

# install missing libraries
installed_libs <- libs %in% rownames(installed.packages())
if (any(installed_libs == F)) {
    print(libs[!installed_libs])
    install.packages(libs[!installed_libs])
}
print("---------loading libraries-----")
#^ load libraries
invisible(lapply(libs, library, character.only = T))

print("======= 1: DOWNLOAD & UNZIP DATA")
# Download and unzip data (unchanged)
url <-
    "https://geodata-eu-central-1-kontur-public.s3.amazonaws.com/kontur_datasets/kontur_population_US_20231101.gpkg.gz"
file_name <- "kontur_population_US_20231101.gpkg.gz"
load_file_name <- gsub(".gz", "", file_name)

#Check if the downloaded file exists
if (file.exists(load_file_name)) {
    print("File's already here, not doing anything in this step...")
} else {
get_population_data <- function() {
    print("httr GET function...")
    res <- httr::GET(
        url,
        write_disk(file_name, overwrite = TRUE),
        progress()
    )
    print("gunzip function...")
    R.utils::gunzip(file_name, overwrite = TRUE, remove = F)
}
get_population_data()
}

print("======= 2: LOAD DATA")
# Load the USA map with Albers projection
usa_sf <- albersusa::usa_sf("laea")

# Visualize the elided population data (for verification)
ggplot() +
    geom_sf(data = usa_sf, fill = "beige", color = "black") +
    theme(panel.background = element_rect(fill = "cornflowerblue"))  # Set ocean color
crs_albers_usa <- sf::st_crs(albersusa::usa_sf("laea"))

#~## Custom function to elide and rescale Alaska and Hawaii

rotate_geometry <- function(geometry, angle, center = c(0, 0)) {
  # Convert degrees to radians
  angle_rad <- angle * pi / 180
  
  # Create a rotation matrix
  rotation_matrix <- matrix(c(cos(angle_rad), -sin(angle_rad),
                              sin(angle_rad), cos(angle_rad)), nrow = 2)
  
  # Function to rotate a set of coordinates
  rotate_coords <- function(coords) {
    # Translate geometry to origin for rotation
    coords_translated <- cbind(coords[, 1] - center[1], coords[, 2] - center[2])
    
    # Apply the rotation matrix
    rotated_coords <- coords_translated %*% rotation_matrix
    
    # Translate back to the original position
    rotated_coords_back <- cbind(rotated_coords[, 1] + center[1], rotated_coords[, 2] + center[2])
    
    return(rotated_coords_back)
  }
  
  # Apply rotation to each polygon's coordinate set
  rotated_geometry <- lapply(sf::st_geometry(geometry), function(polygon) {
    if (inherits(polygon, "POLYGON")) {
      # For POLYGON, rotate each ring
      sf::st_polygon(lapply(polygon, rotate_coords))
    } else if (inherits(polygon, "MULTIPOLYGON")) {
      # For MULTIPOLYGON, rotate each polygon
      sf::st_multipolygon(lapply(polygon, function(ring) lapply(ring, rotate_coords)))
    }
  })
  
  #& centroid <- sf::st_coordinates(sf::st_centroid(geometry))
  #& rotated_polygon <- rotate_geometry(polygon_geom, angle = 45, center = centroid)

  # Create an sfc object with the rotated geometries and set the CRS
  rotated_sfc <- sf::st_sfc(rotated_geometry, crs = sf::st_crs(geometry))
#   rotated_sfc <- sf::st_sfc(rotate_geometry(polygon_geom, angle = 45, center = centroid)) #! Nope.
  return(rotated_sfc)
}
#
elide_geometries_v13 <- function(pop_sf) {
    alaska_move_x <- -1298669
    alaska_move_y <- -3018809
    alaska_scale <- 0.4347826086956522
    alaska_rotate <- 50
    hawaii_move_x <- 5400000
    hawaii_move_y <- -1400000
    hawaii_scale <- 1
    hawaii_rotate <- 35
    # Step 1: Check if CRS is defined, and if it's not WGS 84, transform it
    crs_info <- sf::st_crs(pop_sf)
    
    if (is.null(crs_info)) {
        warning("CRS is not defined. Assuming the input data is in WGS 84 (EPSG:4326).")
        sf::st_crs(pop_sf) <- 4326  # Assign WGS 84 if CRS is missing
    } else if (!is.na(crs_info$epsg) && crs_info$epsg != 4326) {
        pop_sf <- sf::st_transform(pop_sf, crs = 4326)
    }

    # Step 2: Transform the population data to the Albers USA projection (LAEA)
    crs_albers_usa <- sf::st_crs(albersusa::usa_sf("laea"))
    pop_sf <- sf::st_transform(pop_sf, crs = crs_albers_usa)

    # Step 3: Define pre-elision bounding boxes for Alaska and Hawaii in pop_sf
    alaska_bbox_pre_elision <- sf::st_as_sfc(sf::st_bbox(c(xmin = -4500000, xmax = -1500000, ymin = 1200000, ymax = 4000000), crs = crs_albers_usa))
    hawaii_bbox_pre_elision <- sf::st_as_sfc(sf::st_bbox(c(xmin = -5900000, xmax = -5200000, ymin = -1500000, ymax = -300000), crs = crs_albers_usa))

    # Step 4: Use st_intersects to filter out Alaska and Hawaii
    alaska <- pop_sf[sf::st_intersects(pop_sf, alaska_bbox_pre_elision, sparse = FALSE), ]
    hawaii <- pop_sf[sf::st_intersects(pop_sf, hawaii_bbox_pre_elision, sparse = FALSE), ]
    mainland <- pop_sf[!sf::st_intersects(pop_sf, alaska_bbox_pre_elision, sparse = FALSE) &
                       !sf::st_intersects(pop_sf, hawaii_bbox_pre_elision, sparse = FALSE), ]

    # Step 5: Transform Alaska based on its final position in usa_sf
    if (nrow(alaska) > 0) {
        cat("Transforming Alaska: [Scale:", alaska_scale, "]; [Translation:", alaska_move_x, ",", alaska_move_y,"]\n")
        alaska_geometry <- sf::st_geometry(alaska) * alaska_scale + c(alaska_move_x, alaska_move_y) #Formerly * 0.35 + c(-2100000 + 2000000, -2500000)
        cat("Transforming Alaska: [Rotation:", alaska_rotate, "]\n")
        alaska_centroid <- sf::st_coordinates(sf::st_centroid(alaska_geometry))
        alaska_geometry <- rotate_geometry(alaska_geometry, angle = alaska_rotate, center = alaska_centroid)
        #This secondary translation keeps me from chasing gremlines all day 
        # alaska_geometry <- sf::st_geometry(alaska) + c(2439970.2, 0)
        sf::st_geometry(alaska) <- alaska_geometry
        #alaska_geometry <- sf::st_geometry(alaska) + c(2425109, -320939.7)
        alaska_geometry <- sf::st_geometry(alaska) + c(2441109, -318939.7)  #How many pixels does 1000m buy us? (about 1px per 1000m) (We need to go up 2 and right 16)
        sf::st_geometry(alaska) <- alaska_geometry
        alaska <- sf::st_set_crs(alaska, crs_albers_usa)
    }
    # Step 6: Transform Hawaii based on its final position in usa_sf
    if (nrow(hawaii) > 0) {
        cat("Transforming Hawaii: [Scale:", hawaii_scale, "]; [Translation:", hawaii_move_x, ",", hawaii_move_y,"]\n")
        hawaii_geometry <- sf::st_geometry(hawaii) * hawaii_scale + c(hawaii_move_x, hawaii_move_y) # Formerly c(-743033.2 + 2000000, -2313784.4)
        cat("Transforming Hawaii: [Rotation:", hawaii_rotate, "]\n")
        hawaii_centroid <- sf::st_coordinates(sf::st_centroid(hawaii_geometry))
        hawaii_geometry <- rotate_geometry(hawaii_geometry, angle = hawaii_rotate, center = hawaii_centroid)
        sf::st_geometry(hawaii) <- hawaii_geometry
        #This secondary translation keeps me from chasing gremlines all day 
        # hawaii_geometry <- sf::st_geometry(hawaii) + c(-1396305, -280655.75)  #Right 21, down 4?
        # hawaii_geometry <- sf::st_geometry(hawaii) + c(-1375305, -284655.755)  #CHANGED SCALE- #UP 9 LEFT 17 (Let's pretend 500 per pixel now, and see what happens)
        hawaii_geometry <- sf::st_geometry(hawaii) + c(-1375305+(-16.5*386.3), -284655.755+(9.5*386.3))  #CHANGED SCALE- #UP 9 LEFT 17  So... 8500M=22px?
        sf::st_geometry(hawaii) <- hawaii_geometry
        hawaii <- sf::st_set_crs(hawaii, crs_albers_usa)
    }
    # Step 6.5: Calculate the elided bounding boxes for Alaska and Hawaii
    alaska_bbox_elided <- if (nrow(alaska) > 0) sf::st_bbox(alaska) else NA
    hawaii_bbox_elided <- if (nrow(hawaii) > 0) sf::st_bbox(hawaii) else NA

    # Print or return the bounding boxes
    print("Elided Alaska Bounding Box:")
    print(alaska_bbox_elided)
    print("Elided Hawaii Bounding Box:")
    print(hawaii_bbox_elided)
    # Debugging check: Ensure subsets have been created
    print(paste("Alaska geometries:", nrow(alaska)))
    print(paste("Hawaii geometries:", nrow(hawaii)))
    print(paste("Mainland geometries:", nrow(mainland)))

    # Step 7: Return final map (Alaska and Hawaii only for now)
    final_map <- rbind(mainland, alaska, hawaii) #final_map <- rbind(mainland, alaska, hawaii)

    return(final_map)
    #return(list(final_map = final_map, alaska_bbox_elided = alaska_bbox_elided, hawaii_bbox_elided = hawaii_bbox_elided))
}



#~## 2. LOAD POPULATION DATA AND TRANSFORM TO ALBERS PROJECTION
get_population_data <- function() {
    pop_df <- sf::st_read(load_file_name) |> 
        sf::st_transform(crs = crs_albers_usa)
    #^ Apply the custom function to elide and rescale Alaska and Hawaii
    pop_df_elided <- elide_geometries_v13(pop_df)
    return(pop_df_elided)
}


pop_sf <- get_population_data()
alaska_bbox <- sf::st_as_sfc(sf::st_bbox(c(xmin = -4500000, xmax = -1500000, ymin = 1200000, ymax = 4000000), crs = crs_albers_usa))
hawaii_bbox <- sf::st_as_sfc(sf::st_bbox(c(xmin = -5900000, xmax = -5200000, ymin = -1500000, ymax = -300000), crs = crs_albers_usa)) 
the_all_box <- sf::st_as_sfc(sf::st_bbox(c(xmin = -2100000, xmax = 2516373.8, ymin = -2500000, ymax = 732103.3), crs = crs_albers_usa))  #This is exact, with no margin.  WE SHOULD PROBABLY EXPAND THIS.
#     xmin     ymin     xmax     ymax
# -4525109 -2171024 -3064873 -1228431
elision_alaska_bbox <- sf::st_as_sfc(sf::st_bbox(c(xmin =  -4525109 , xmax =  -3064873 , ymin =  -2171024 , ymax =  -1228431 ), crs = crs_albers_usa))
#       xmin       ymin       xmax       ymax
#  667909.1 -2034035.8 1264050.9 -1620965.0
elision_hawaii_bbox <- sf::st_as_sfc(sf::st_bbox(c(xmin =  667909.1 , xmax =  1264050.9 , ymin =  -2034035.8 , ymax =  -1620965.0 ), crs = crs_albers_usa))

#~ FUTHER TROUBLESHOOTING
# Extract Alaska and Hawaii geometries from usa_sf
alaska_usa_sf <- usa_sf[usa_sf$name == "Alaska", ]
hawaii_usa_sf <- usa_sf[usa_sf$name == "Hawaii", ]
# Get the bounding boxes of Alaska and Hawaii in usa_sf (final positions)
alaska_bbox_usa_sf <- sf::st_bbox(alaska_usa_sf)
hawaii_bbox_usa_sf <- sf::st_bbox(hawaii_usa_sf)
all_box_bb <- sf::st_bbox(the_all_box)
# Convert bbox to numeric for coord_sf()
xlim <- c(as.numeric(all_box_bb["xmin"]), as.numeric(all_box_bb["xmax"]))
ylim <- c(as.numeric(all_box_bb["ymin"]), as.numeric(all_box_bb["ymax"]))

ggplot() +
    geom_sf(data = usa_sf, fill = "beige", color = "black") +
    # geom_sf(data = pop_sf, fill = NA, color = "blueviolet") +
    geom_sf(data = pop_sf, fill = "blueviolet", color = NA) +
    # geom_sf(data = elision_alaska_bbox, fill = NA, color = "red", linetype = "dashed", size = 1.5) +
    # geom_sf(data = elision_hawaii_bbox, fill = NA, color = "green", linetype = "dashed", size = 1.5) +
    # geom_sf(data = the_all_box, fill = NA, color = "darkgoldenrod2", linetype = "dashed", size = 1.5) +
    coord_sf(xlim = xlim, ylim = ylim, expand = FALSE) +                                 # Restrict plot to bounding box
    # theme_minimal() +
    theme(panel.background = element_rect(fill = "cornflowerblue"))  # Set ocean color
    ggtitle("Population Data: Alaska")
message("plotted")
#




#? alaska_bbox_elided <- pop_sf$alaska_bbox_elided #? What?  This absolutely hasn't been defined.
#? hawaii_bbox_elided <- pop_sf$hawaii_bbox_elided #? What?  This absolutely hasn't been defined.

#alaska_bbox_elided <- sf::st_bbox(pop_sf$alaska)
#hawaii_bbox_elided <- sf::st_bbox(pop_sf$hawaii)


# Print bounding boxes to inspect final positions
print("Alaska bbox in usa_sf:")
print(alaska_bbox_usa_sf)
    #   xmin       ymin       xmax       ymax
# -2100000.0 -2500000.0  -610041.6 -1549370.7

print("Hawaii bbox in usa_sf:")
print(hawaii_bbox_usa_sf)
#       xmin       ymin       xmax       ymax
#  -743033.2 -2313784.4 -117616.8 -1902527.9

### 3. SHP TO RASTER
### ----------------
# Anticipated Bounding Box (xmin, ymin, xmax, ymax):
# xmin: -179.14891 (westmost point of Alaska)
# xmax: -66.93457 (eastmost point of the contiguous U.S.)
# ymin: 24.396308 (southmost point of Florida)
# ymax: 49.384358 (northmost point of Minnesota)
# Numerical Representation:
# Bounding Box: c(xmin = -179.14891, ymin = 24.396308, xmax = -66.93457, ymax = 49.384358)


# get_raster_size <- function() {
#     height <- sf::st_distance(
#         sf::st_point(c(bb[["xmin"]], bb[["ymin"]])),
#         sf::st_point(c(bb[["xmin"]], bb[["ymax"]]))
#     )
#     width <- sf::st_distance(
#         sf::st_point(c(bb[["xmin"]], bb[["ymin"]])),
#         sf::st_point(c(bb[["xmax"]], bb[["ymin"]]))
#     )

#     if (height > width) {
#         height_ratio <- 1
#         width_ratio <- width / height
#     } else {
#         width_ratio <- 1
#         height_ratio <- height / width
#     }

#     return(list(width_ratio, height_ratio))
# }

sf::st_bbox(usa_sf)
bb <- sf::st_bbox(pop_sf)

print(bb)
get_raster_size <- function() {
    height <- sf::st_distance(
        sf::st_point(c(all_box_bb[["xmin"]], all_box_bb[["ymin"]])),
        sf::st_point(c(all_box_bb[["xmin"]], all_box_bb[["ymax"]]))
    )
    width <- sf::st_distance(
        sf::st_point(c(all_box_bb[["xmin"]], all_box_bb[["ymin"]])),
        sf::st_point(c(all_box_bb[["xmax"]], all_box_bb[["ymin"]]))
    )

    if (height > width) {
        height_ratio <- 1
        width_ratio <- width / height
    } else {
        width_ratio <- 1
        height_ratio <- height / width
    }

    return(list(width_ratio, height_ratio))
}

width_ratio <- get_raster_size()[[1]]
height_ratio <- get_raster_size()[[2]]

size <- 5000 #3000
width <- round((size * width_ratio), 0)
height <- round((size * height_ratio), 0)
#
get_population_raster <- function() {
    pop_rast <- stars::st_rasterize(
        pop_sf |>
            dplyr::select(population, geom),
        nx = width, ny = height
    )

    return(pop_rast)
}

pop_rast <- get_population_raster()
plot(pop_rast)

pop_mat <- pop_rast |>
    as("Raster") |>
    rayshader::raster_to_matrix()

cols <- rev(c(
    "#0b1354", "#283680",
    "#6853a9", "#c863b3"
))

texture <- grDevices::colorRampPalette(cols)(256)
print("")
print("Creating 3D object...")
# Create the initial 3D object
pop_mat |>
    rayshader::height_shade(texture = texture) |>
    rayshader::plot_3d(
        heightmap = pop_mat,
        solid = F,
        soliddepth = 0,
        zscale = 15,  #Reduce?
        shadowdepth = 0,
        shadow_darkness = .85,
        windowsize = c(1800, 1800), #was c(800,800)
        phi = 65,
        zoom = .65,
        theta = -30,
        background = "white"
    )
print("    done")
print("Adjusting Render Camera...")
# Use this to adjust the view after building the window object
rayshader::render_camera(phi = 75, zoom = .7, theta = 0)
print("    done")

print("Exporting OBJ...")
#* https://www.rayshader.com/reference/save_obj.html
rayshader::save_obj("AlbersSpikes_v4.obj")


print("Rendering...")

#* https://www.rayshader.com/reference/render_highquality.html
rayshader::render_highquality(
    filename = "US_spike-AlbersUSAv2.1_population_2022.png",
    sample_method = "sobol",
    samples = 512, #Was defaulting to 128
    preview = F, #I suspect we're getting a problem here.  Changing to F
    light = T,
    lightdirection = 225,
    lightaltitude = 60,
    lightintensity = 400,
    interactive = F,
    width = width, 
    height = height
)
print("    done")
#