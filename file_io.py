import json
from tkinter import filedialog, Tk

def load_config_from_json(json_file_path):
    """
    Load the entire configuration data from a JSON file.

    Parameters:
    json_file_path (str): Path to the JSON configuration file.

    Returns:
    dict: The entire configuration data from the JSON file.

    Raises:
    FileNotFoundError: If the JSON file is not found.
    """
    try:
        with open(json_file_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

def write_config_to_json(json_file_path, new_config):
    """
    Overwrite a JSON file with new configuration data.

    Parameters:
    json_file_path (str): Path to the JSON configuration file.
    new_config (dict): Entire new configuration data to be written to the JSON file.

    Raises:
    FileNotFoundError: If the JSON file is not found.
    """
    try:
        with open(json_file_path, 'w') as file:
            json.dump(new_config, file, indent=4)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

def ask_for_file_path(title="Select file", filetypes=(("JSON files", "*.json"), ("All files", "*.*"))):
    """
    Open a file dialog for the user to select a file.

    Parameters:
    title (str): Title of the file dialog window.
    filetypes (tuple): File types to display in the dialog.

    Returns:
    str: Path to the selected file, or None if operation is canceled.
    """
    root = Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return file_path
