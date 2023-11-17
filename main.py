import numpy as np
from file_io import ask_for_file_path, load_config_from_json, write_config_to_json
from image_processing import add_z, find_closest_regions, find_transform, locate_blobs, median_filter, read_image, transform_coordinates, write_image
from visualization import display_image_napari, plot_accuracy

def map(config_file_path):
    """
    Perform image mapping based on configuration from a JSON file.

    Parameters:
    config_file_path (str): Path to the JSON configuration file.

    This function will load configuration, process images, and update the configuration with mapping results.
    """
    # Load the mapping configuration
    try:
        config = load_config_from_json(config_file_path)
        mapping_settings = config["mapping"]["settings"]

        # Check if mapping is already done
        if not mapping_settings.get("mapped", False):
            print("Mapping data not available. Mapping now...")
        else:
            print("Mapping data available. Skipping mapping.")
            return

        path_1 = config["mapping"]["paths"]["map_img_1"]
        path_2 = config["mapping"]["paths"]["map_img_2"]

        image_1 = read_image(path_1, dtype=mapping_settings["bit_depth_1"])
        image_2 = read_image(path_2, dtype=mapping_settings["bit_depth_2"])

        mapping_blob_count = mapping_settings["blob_count"]
    except Exception as e:
        print(f"An error occurred while loading configuration: {e}")
        return

    # Process images and locate blobs
    try:
        auto_blob_1, blob_size_1 = locate_blobs(image_1, mapping_blob_count, source=0)
        auto_blob_2, blob_size_2 = locate_blobs(image_2, mapping_blob_count)
    except Exception as e:
        print(f"An error occurred during blob location: {e}")
        return

    # User interaction for blob selection
    napari_blob_1 = display_image_napari(image_1, mapping_blob_count, blob_size_1, title='Identify Blobs In First Image')
    napari_blob_2 = display_image_napari(image_2, mapping_blob_count, blob_size_2, title='Identify Blobs In Second Image')

    # Match and order automatically located blobs to user-selected blobs
    map_blob_1 = find_closest_regions(napari_blob_1, auto_blob_1)
    map_blob_2 = find_closest_regions(napari_blob_2, auto_blob_2)

    # Compute mapping parameters
    try:
        center_1, center_2, scaling, angle = find_transform(map_blob_1, map_blob_2)
    except Exception as e:
        print(f"An error occurred during transformation calculation: {e}")
        return

    # Perform mapping validation
    validation_blobs = transform_coordinates(map_blob_1, center_1, center_2, scaling, angle)
    display_image_napari(image_2, points_count=mapping_blob_count, points_size=blob_size_2, title='Mapping Validation', custom_points=validation_blobs)

    # Update mapping configuration
    update_mapping_configuration(config, center_1, center_2, scaling, angle)
    write_config_to_json(config_file_path, config)

def update_mapping_configuration(config, center_1, center_2, scaling, angle):
    """
    Update the mapping configuration in the configuration dictionary.

    Parameters:
    config (dict): Configuration dictionary.
    center_1, center_2 (list): Mapping centers.
    scaling (float): Scaling factor.
    angle (float): Rotation angle.
    """
    config["mapping"]["parameters"]["center_1"] = center_1.tolist()
    config["mapping"]["parameters"]["center_2"] = center_2.tolist()
    config["mapping"]["parameters"]["scaling"] = scaling
    config["mapping"]["parameters"]["angle"] = angle
    config["mapping"]["settings"]["mapped"] = True

def analyze_stack(config_file_path):
    # Load the mapping parameters from the selected JSON file
    try:
        config = load_config_from_json(config_file_path)
        analysis_settings = config["analysis"]["settings"]

        center_1 = config["mapping"]["parameters"]["center_1"]
        center_2 = config["mapping"]["parameters"]["center_2"]
        scaling = config["mapping"]["parameters"]["scaling"]
        angle = config["mapping"]["parameters"]["angle"]

        blob_z_spacing = config["analysis"]["settings"]["blob_z_spacing"]

        stack_blob_count = config["analysis"]["settings"]["blob_count"]

        ref_path = config["analysis"]["paths"]["ref_img"]

        ref_image = read_image(ref_path, dtype=config["mapping"]["settings"]["bit_depth_1"])
        ref_image = median_filter(ref_image)
        voxel_size = config["analysis"]["settings"]["voxel_size_um"]

        if "stack_median" in config["analysis"]["paths"]:
            stack_path = config["analysis"]["paths"]["stack_median"]
            stack = read_image(stack_path, dtype=config["mapping"]["settings"]["bit_depth_2"])
        else:
            stack_path = config["analysis"]["paths"]["stack"]
            stack = read_image(stack_path, dtype=config["mapping"]["settings"]["bit_depth_2"])
            stack = median_filter(stack)
            stack_path = stack_path[:-4] + "_median.tif"
            write_image(stack_path, stack)
            config["analysis"]["paths"]["stack_median"] = stack_path
            write_config_to_json(config_file_path, config)
            
        if not analysis_settings.get("analyzed", False):
            print("Analysis data not available. Analyzing now...")
        else:
            print("Analysis data available. Skipping analysis.")
            return stack, np.asarray(config['analysis']['results']['ref_blob_map']), np.asarray(config['analysis']['results']['stack_blobs']), 10, config['analysis']['settings']['voxel_size_um']
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

    # Automatically locate the blobs in the stack
    stack_blobs, _ = locate_blobs(stack, stack_blob_count)
    
    # Order located blobs
    stack_blobs = find_closest_regions(ref_blob_map, stack_blobs)

    try:
        config['analysis']['settings']['analyzed'] = True
        config['analysis']['results']['ref_blob_map'] = ref_blob_map.tolist()
        config['analysis']['results']['stack_blobs'] = stack_blobs.tolist()
        write_config_to_json(config_file_path, config)
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    return stack, ref_blob_map, stack_blobs, blob_size, voxel_size

def main():
    """
    Main function to execute the mapping and analysis workflow.
    """
    # Prompt the user to select the JSON configuration file
    config_file_path = ask_for_file_path(title="Select JSON configuration file")

    if not config_file_path:
        print("No file selected. Exiting program.")
        return
    
    # Perform mapping of the reference images
    try:
        map(config_file_path)
    except Exception as e:
        print(f"Error during mapping: {e}")
        return

    # Analyze a stack
    try:
        stack, reference_blobs, actual_blobs, blob_size, voxel_size = analyze_stack(config_file_path)
    except Exception as e:
        print(f"Error during stack analysis: {e}")
        return

    # Display and plot the results of the analysis
    try:
        display_image_napari(stack, points_count=reference_blobs.shape[0], points_size=blob_size, title='Holographic stimulation accuracy', custom_points=reference_blobs, auto_points=actual_blobs, scale=voxel_size)
        plot_accuracy(reference_blobs, actual_blobs, voxel_size=voxel_size)
    except Exception as e:
        print(f"Error during plotting accuracy: {e}")

if __name__ == '__main__':
    main()
