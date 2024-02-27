import math


def calculate_distance(x1, y1, x2, y2):
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

def is_point_in_hexagon(center_x, center_y, hex_radius, point_x, point_y):
    """
    Approximates whether a given point is within a hexagonal region based on the center and radius of the hexagon.
    This is a simplified approach that treats the hexagon as a circle.

    Args:
    - center_x (float): The x-coordinate of the hexagon's center.
    - center_y (float): The y-coordinate of the hexagon's center.
    - hex_radius (float): The radius of the hexagon (distance from center to any vertex).
    - point_x (float): The x-coordinate of the point to check.
    - point_y (float): The y-coordinate of the point to check.

    Returns:
    - bool: True if the point is within the hexagon, False otherwise.
    """
    # Calculate the distance from the point to the hexagon's center
    distance = math.sqrt((point_x - center_x) ** 2 + (point_y - center_y) ** 2)

    # Check if the distance is within the hexagon's radius
    return distance <= hex_radius

def calculate_hex_centers(world_extent, num_regions):
    # Extracting the minimum and maximum coordinates
    min_x, min_y = world_extent[0]
    max_x, max_y = world_extent[1]

    # Calculating the horizontal and vertical distances between hexagon centers
    horizontal_distance = (max_x - min_x) / (num_regions + 0.5)
    vertical_distance = (max_y - min_y) / (num_regions * math.sqrt(3))

    # Determining the hexagon radius
    hex_radius = min(horizontal_distance, vertical_distance)

    # Initializing list to store region centers
    region_centers = []

    # Calculating center coordinates for each region
    for i in range(num_regions):
        for j in range(num_regions):
            # Calculating center coordinates for each hexagon
            center_x = min_x + hex_radius * (1.5 * i + 1)
            center_y = min_y + hex_radius * (math.sqrt(3) * j + (i % 2) * math.sqrt(3) / 2)
            region_centers.append((center_x, center_y))

    return region_centers, hex_radius