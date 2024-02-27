import requests
from string_utils import remove_hex
import json
from math_utils import calculate_distance
import aiohttp

dynamic_map_data_global = {}
static_map_data_global = {}

async def get_json_response(url):
    """Asynchronous helper function to send a GET request and parse the JSON response."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def fetch_dynamic_map_data():
    """Asynchronously fetch dynamic map data for all regions and store it in the global variable."""
    global dynamic_map_data_global
    root_endpoint = "https://war-service-live.foxholeservices.com/api"
    maps_url = f"{root_endpoint}/worldconquest/maps"
    map_names = await get_json_response(maps_url)

    for map_name in map_names:
        dynamic_data_url = f"{root_endpoint}/worldconquest/maps/{map_name}/dynamic/public"
        dynamic_map_data_global[map_name] = await get_json_response(dynamic_data_url)

async def fetch_static_map_data():
    """Asynchronously fetch static map data for all regions and store it in the global variable."""
    global static_map_data_global
    root_endpoint = "https://war-service-live.foxholeservices.com/api"
    maps_url = f"{root_endpoint}/worldconquest/maps"
    map_names = await get_json_response(maps_url)

    for map_name in map_names:
        static_data_url = f"{root_endpoint}/worldconquest/maps/{map_name}/static"
        static_map_data_global[map_name] = await get_json_response(static_data_url)

def save_to_file():
    global dynamic_map_data_global, static_map_data_global
    data_to_save = {
        "dynamic": dynamic_map_data_global,
        "static": static_map_data_global
    }
    with open('temp', 'w') as file:
        json.dump(data_to_save, file)

def load_from_file():
    global dynamic_map_data_global, static_map_data_global
    try:
        with open('temp', 'r') as file:
            data_loaded = json.load(file)
            dynamic_map_data_global = data_loaded.get("dynamic", {})
            static_map_data_global = data_loaded.get("static", {})
    except FileNotFoundError:
        print("File not found. Ensure 'temp' file exists and is in the correct location.")

def controlled_regions(side):
    """Return a list of region names controlled by the specified side after applying remove_hex on each name."""
    # Ensure side is uppercased to match API values
    side = side.upper()
    if side not in ["WARDENS", "COLONIALS"]:
        raise ValueError("Side must be either 'WARDENS' or 'COLONIALS'.")

    load_from_file()

    controlled_regions = []
    map_names_real = []

    for map_name, dynamic_map_data in dynamic_map_data_global.items():
        for item in dynamic_map_data.get("mapItems", []):
            if item.get("teamId") == side:
                # Apply remove_hex function on each map name before adding it to the list
                cleaned_name = remove_hex(map_name)
                map_names_real.append(map_name)
                controlled_regions.append(cleaned_name)
                break
    print (controlled_regions)
    return controlled_regions , map_names_real

def region_storages(region_name,side):
    """
    Returns the names with corresponding types ('Depot' or 'Seaport') of every storage depot (Storage Facility)
    and seaport (Seaport) in the given region that corresponds to the specified side,
    by finding the closest 'Major' map text item to each.

    Args:
    - region_name (str): The name of the region to search for storages and seaports.
    - side (str): The side (e.g., 'WARDENS') the storage or seaport must belong to.

    Returns:
    - list: A list of names with types for every matching storage depot and seaport in the specified region.
    """
    load_from_file()

    # Check if the region name exists in the dynamic map data
    if region_name not in dynamic_map_data_global:
        return "Region not found."

    # Retrieve the dynamic map data for the specified region
    region_data = dynamic_map_data_global[region_name]

    # Retrieve the static map data for the specified region
    static_region_data = static_map_data_global[region_name]

    # Filter for items that are Storage Facilities or Seaports and match the specified side
    storage_and_seaport_items = [
        item for item in region_data.get('mapItems', [])
        if item.get('iconType') in {33, 52} and item.get('teamId') == side
    ]

    # Extract 'Major' labeled items from static data for name mapping
    major_labeled_items = [
        item for item in static_region_data.get('mapTextItems', [])
        if item['mapMarkerType'] == 'Major'
    ]

    storage_names_with_types = []
    for item in storage_and_seaport_items:
        closest_major = min(
            major_labeled_items,
            key=lambda major: calculate_distance(major['x'], major['y'], item['x'], item['y'])
        )
        item_type = 'Depot' if item['iconType'] == 33 else 'Seaport'
        storage_names_with_types.append(f"{closest_major['text']} {item_type}")

    return storage_names_with_types

async def fetch_n_save():
    await fetch_dynamic_map_data()
    await fetch_static_map_data()
    save_to_file()

