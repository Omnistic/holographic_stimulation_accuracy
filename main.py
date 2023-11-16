from file_io import ask_for_file_path, load_config_from_json, write_config_to_json
from image_processing import read_image, locate_blobs, find_closest_regions, find_transform, transform_coordinates, add_z, median_filter, write_image
from visualization import display_image_napari, plot_accuracy

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
    
    # Automatically locate the blobs in the mapping images
    auto_blob_1, blob_size_1 = locate_blobs(image_1, mapping_blob_count)
    auto_blob_2, blob_size_2 = locate_blobs(image_2, mapping_blob_count)

    # Let user select blobs in the mapping images
    napari_blob_1 = display_image_napari(image_1, mapping_blob_count, blob_size_1, title='Identify Blobs In First Image')
    napari_blob_2 = display_image_napari(image_2, mapping_blob_count, blob_size_2, title='Identify Blobs In Second Image')

    # Match and order automatically located blobs to user-selected blobs
    map_blob_1 = find_closest_regions(napari_blob_1, auto_blob_1)
    map_blob_2 = find_closest_regions(napari_blob_2, auto_blob_2)

    # Find mapping parameters
    center_1, center_2, scaling, angle = find_transform(map_blob_1, map_blob_2)

    # Transform validation
    validation_blobs = transform_coordinates(map_blob_1, center_1, center_2, scaling, angle)
    display_image_napari(image_2, points_count=mapping_blob_count, points_size=blob_size_2, title='Mapping Validation', custom_points=validation_blobs)

    # Update mapping configuration in JSON file
    write_config_to_json(config_file_path, "mapping", "settings", {"mapped": True})
    write_config_to_json(config_file_path, "mapping", "parameters", {"center_1": center_1.tolist(), "center_2": center_2.tolist(), "scaling": scaling, "angle": angle})

    return

def analyze_stack(config_file_path, display=True):
    # Load the mapping parameters from the selected JSON file
    try:
        mapping = load_config_from_json(config_file_path, "mapping")
        
        center_1 = mapping["parameters"]["center_1"]
        center_2 = mapping["parameters"]["center_2"]
        scaling = mapping["parameters"]["scaling"]
        angle = mapping["parameters"]["angle"]

        blob_z_spacing = mapping["settings"]["blob_z_spacing"]

        stack_blob_count = mapping["settings"]["stack_blob_count"]

        ref_path = mapping["paths"]["ref_img"]
        ref_image = read_image(ref_path)
        ref_image = median_filter(ref_image)

        if "stack_median" in mapping["paths"]:
            stack_path = mapping["paths"]["stack_median"]
            stack = read_image(stack_path)
        else:
            stack_path = mapping["paths"]["stack"]
            stack = read_image(stack_path, dtype='uint8')
            stack = median_filter(stack)
            stack_path = stack_path[:-4] + "_median.tif"
            write_image(stack_path, stack)
            write_config_to_json(config_file_path, "mapping", "paths", {"stack_median": stack_path})
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    
    # Automatically locate the blobs in the the reference image
    auto_blob, blob_size = locate_blobs(ref_image, stack_blob_count)

    # Let user select blobs in the reference image
    napari_blob = display_image_napari(ref_image, stack_blob_count, blob_size, title='Identify Blobs In Reference Image')

    # Match and order automatically located blobs to user-selected blobs
    ref_blob = find_closest_regions(napari_blob, auto_blob)

    # Map reference blob coordinates
    ref_blob_map = transform_coordinates(ref_blob, center_1, center_2, scaling, angle)

    # Augment mapped blobs with z coordinates
    ref_blob_map = add_z(ref_blob_map, blob_z_spacing, stack.shape[0])

    # Display stack with reference location of blobs
    if display:
        display_image_napari(stack, points_count=stack_blob_count, points_size=blob_size, title='Stack with Reference Location of Target Blobs', custom_points=ref_blob_map)

    # Automatically locate the blobs in the stack
    stack_blobs, _ = locate_blobs(stack, stack_blob_count)
    
    # Order located blobs
    stack_blobs = find_closest_regions(ref_blob_map, stack_blobs)

    display_image_napari(stack, points_count=stack_blob_count, points_size=blob_size, title='TEST', custom_points=ref_blob_map, auto_points=stack_blobs, scale=[1, 0.1725, 0.1725])

    return ref_blob_map, stack_blobs

def main():
    # Prompt the user to select the JSON configuration file
    config_file_path = ask_for_file_path(title="Select JSON configuration file")

    if not config_file_path:
        print("No file selected. Exiting program.")
        return
    
    # Perform mapping of the reference images
    map(config_file_path)

    # Analyze a stack
    reference_blobs, actual_blobs = analyze_stack(config_file_path, display=False)

    # Plot the results of the analysis
    plot_accuracy(reference_blobs, actual_blobs, voxel_size=[1, 0.1725, 0.1725])

if __name__ == '__main__':
    main()