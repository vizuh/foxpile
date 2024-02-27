import json
import os


def save_to_json(data, filename, file_path=None):
    """
    Saves a dictionary or dictionaries to a JSON file in a specified file path.

    :param data: Dictionary or dictionaries to be saved.
    :param filename: Name of the file to save the data to.
    :param file_path: The directory path where the file will be saved.
    """
    if file_path is None:
        file_path = os.getcwd()  # Use the current working directory if file_path is None
    full_path = os.path.join(file_path, filename)
    with open(full_path, 'w') as file:
        json.dump(data, file, indent=4)


def load_from_json(filename, file_path):
    """
    Loads and returns a dictionary or dictionaries from a JSON file in a specified file path.
    If the file does not exist, prints 'File not found' and does not raise an error.

    :param filename: Name of the file to load the data from.
    :param file_path: The directory path from where the file will be loaded.
    :return: Loaded dictionary or dictionaries, or None if the file does not exist.
    """
    full_path = f"{file_path}/{filename}"
    try:
        with open(full_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print('File not found')
        return None