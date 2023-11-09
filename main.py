from file_io import ask_for_file_path, load_config_from_json
from image_processing import read_image, locate_blobs
from visualization import visualize_image

def map(config_file_path):
    # Load the mapping configuration from the selected JSON file
    try:
        mapping = load_config_from_json(config_file_path, "mapping")

        if not mapping["settings"]["mapped"]:
            print("Mapping data not available. Mapping now...")
        else:
            print("Mapping data available. Skipping mapping.")
            return
        
        path_1 = mapping["paths"]["map_img_1"]
        path_2 = mapping["paths"]["map_img_2"]

        image_1 = read_image(path_1)
        image_2 = read_image(path_2)

        mapping_blob_count = mapping["settings"]["blob_count"]
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    
    visualize_image(locate_blobs(image_1, mapping_blob_count))
    
def main():
    # Prompt the user to select the JSON configuration file
    config_file_path = ask_for_file_path(title="Select JSON configuration file")

    if not config_file_path:
        print("No file selected. Exiting program.")
        return
    
    # Perform mapping of the reference images
    map(config_file_path)

if __name__ == '__main__':
    main()