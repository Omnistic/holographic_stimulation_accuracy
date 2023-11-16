import json
from tkinter import filedialog, Tk

import json

def load_config_from_json(json_file_path, config_section):
    """
    Load configuration data from a JSON file. This includes image paths and blob count.
    
    Parameters:
    json_file_path (str): The path to the JSON configuration file.
    config_section (str): The section of the configuration file to load.
    
    Returns:
    tuple: A tuple containing the reference image path, target image path, and reference blob count.
    
    Raises:
    FileNotFoundError: If the JSON file is not found.
    KeyError: If the expected keys are not in the JSON file.
    """
    with open(json_file_path, 'r') as file:
        config = json.load(file)
    return config[config_section]

import json

def write_config_to_json(json_file_path, config_section, sub_section, new_data):
    """
    Write new configuration data to a sub-section of a section in a JSON file.

    Parameters:
    json_file_path (str): The path to the JSON configuration file.
    config_section (str): The section of the configuration file to update.
    sub_section (str): The sub-section within the main section to update.
    new_data (dict): The new data to be written to the specified sub-section.

    Raises:
    FileNotFoundError: If the JSON file is not found.
    KeyError: If the specified main section does not exist in the JSON file.
    """
    # Read the existing data
    try:
        with open(json_file_path, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {json_file_path}")

    # Ensure the main section exists, create if necessary
    if config_section not in config:
        config[config_section] = {}

    # Update the specified sub-section with new data
    if sub_section in config[config_section]:
        config[config_section][sub_section].update(new_data)
    else:
        config[config_section][sub_section] = new_data

    # Write the updated data back to the file
    with open(json_file_path, 'w') as file:
        json.dump(config, file, indent=4)  # indent for pretty printing

def ask_for_file_path(title="Select file", filetypes=(("JSON files", "*.json"), ("All files", "*.*"))):
    """
    Prompt the user to select a file via a file dialog window.

    Parameters:
    title (str): The title of the file dialog window.
    filetypes (tuple): A tuple defining the file types to filter in the dialog.

    Returns:
    str: The path to the selected file as a string. If the user cancels the operation, returns None.
    """
    root = Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()  # Close the root window after the file is selected
    return file_path