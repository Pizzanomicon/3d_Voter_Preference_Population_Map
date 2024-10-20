import cupy as cp
import matplotlib.pyplot as plt

# Image dimensions
width, height = 256, 512

# Create a 2D grid of coordinates
x = cp.arange(width)
y = cp.arange(height)
xx, yy = cp.meshgrid(x, y)

# Define the three points through which the circle passes
A = cp.array([0, 0])
B = cp.array([256, 256])
C = cp.array([0, 512])

# Function to compute the circumcenter of a triangle
def circumcenter(A, B, C):
    D = 2 * (A[0] * (B[1] - C[1]) + B[0] * (C[1] - A[1]) + C[0] * (A[1] - B[1]))
    Ux = ((A[0]**2 + A[1]**2) * (B[1] - C[1]) + (B[0]**2 + B[1]**2) * (C[1] - A[1]) + (C[0]**2 + C[1]**2) * (A[1] - B[1])) / D
    Uy = ((A[0]**2 + A[1]**2) * (C[0] - B[0]) + (B[0]**2 + B[1]**2) * (A[0] - C[0]) + (C[0]**2 + C[1]**2) * (B[0] - A[0])) / D
    return cp.array([Ux, Uy])

# Compute the circumcenter (center of the circle)
center = circumcenter(A, B, C)

# Compute the radius of the circle (distance from center to any vertex)
radius = cp.sqrt(cp.sum((center - A)**2))

# Create a mask for the full circle
distances = cp.sqrt((xx - center[0])**2 + (yy - center[1])**2)
circle_mask = distances <= radius

# To form the correct semicircle, we need to find which half of the circle contains the points A, B, and C.
def angle_from_center(point, center):
    return cp.arctan2(point[1] - center[1], point[0] - center[0])

angle_A = angle_from_center(A, center)
angle_B = angle_from_center(B, center)
angle_C = angle_from_center(C, center)

# Calculate the angle for each pixel in the grid
angles_grid = cp.arctan2(yy - center[1], xx - center[0])

# Determine the angular range for the semicircle that includes points A, B, and C
min_angle = cp.minimum(angle_A, angle_C)
max_angle = cp.maximum(angle_A, angle_C)

# Create the semicircle mask: points must lie within the angular range and inside the circle
semicircle_mask = circle_mask & (angles_grid >= min_angle) & (angles_grid <= max_angle)

#~ THE COLORATION LOGIC

#* Red Channel (height-based gradient: 255 to 0 decrementing every 2 pixels)
R = cp.floor(255 - (yy / 2))

#* Blue Channel (height-based gradient: 0 to 255 incrementing every 2 pixels)
B = cp.floor(yy / 2)

#* Diff Channel:
Diff= cp.abs(R-B)

#* TEMP1: The minimum of R and B
TEMP1 = cp.minimum(R, B)

#* TEMP2: Gradient over width (x-axis: 0 to 255 incrementing 1 by every 1 pixel)
TEMP2 = xx

#* Decrease in R and B logic
#This is a little touchy-feely
#What if the decrease was a gamma curve, or linear dependent on the diff between them?
Diff_factor = (255 - Diff) / 255
RB_decrease_factor = Diff_factor * .75 #.2
R_decreasing = cp.clip(R - cp.rint(RB_decrease_factor * TEMP2), 0, 255)
B_decreasing = cp.clip(B - cp.rint(RB_decrease_factor * TEMP2), 0, 255)

#* Green Channel: The sum of TEMP1 and TEMP2 (capped at 255)
G = cp.clip((TEMP1 + cp.rint((132/256)*TEMP2)), 0, 255)

# Apply the semicircle mask to the color channels (set to black outside the semicircle)
Rm = cp.where(semicircle_mask, R_decreasing, 0)
Gm = cp.where(semicircle_mask, G, 0)
Bm = cp.where(semicircle_mask, B_decreasing, 0)

# Stack the channels to create the final image
imagem = cp.stack([Rm, Gm, Bm], axis=-1).astype(cp.uint8)
image = cp.stack([R_decreasing, G, B_decreasing], axis=-1).astype(cp.uint8)

# Convert to host memory (from GPU) for display
image_hostm = cp.asnumpy(imagem)
image_host = cp.asnumpy(image)

# Display the result
plt.imshow(image_hostm)

# Custom tick labels for y-axis (Republican, Neutral, Democrat)
plt.yticks([10, 255, 500], ['Republican', 'Neutral', 'Democrat'])

# Custom tick label for x-axis (Libertarian/Green/Other at 220)
plt.xticks([256], ['Libertarian\nGreen\nOther'])


plt.title("Voting Preference Color Scale")
plt.show()
