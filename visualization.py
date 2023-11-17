import matplotlib.pyplot as plt
import numpy as np
import napari
from config import CMAP, COLOR_PALETTE

plt.style.use('dark_background')

def visualize_image(image, title='Image Viewer'):
    plt.figure()
    plt.imshow(image, cmap=CMAP)
    plt.title(title)
    plt.show()

def plot_accuracy(target_positions, actual_positions, voxel_size=[1, 1, 1]):
    """
    Plot the accuracy of target versus actual positions in 3D coordinates.

    Parameters:
    target_positions (ndarray): Array of target positions.
    actual_positions (ndarray): Array of actual positions.
    voxel_size (list): Voxel size in each dimension.
    """
    # Generate labels for each point
    labels = [f'S{i + 1}' for i in range(target_positions.shape[0])]

    # Define accuracy in each dimension
    accuracies = [
        (target_positions[:, 1] - actual_positions[:, 1]) * voxel_size[1],  # X Accuracy
        (target_positions[:, 2] - actual_positions[:, 2]) * voxel_size[2],  # Y Accuracy
        (target_positions[:, 0] - actual_positions[:, 0]) * voxel_size[0]   # Z Accuracy
    ]

    # Plotting accuracies in each dimension
    for i, accuracy in enumerate(accuracies, start=1):
        plot_dimension_accuracy(i, labels, accuracy, f'{["X", "Y", "Z"][i-1]} Accuracy')

    plt.show()

def plot_dimension_accuracy(subplot_index, labels, accuracy, title):
    """
    Helper function to plot accuracy in one dimension.

    Parameters:
    subplot_index (int): Index of the subplot.
    labels (list): Labels for each data point.
    accuracy (ndarray): Accuracy values for the dimension.
    title (str): Title of the subplot.
    """
    plt.subplot(1, 4, subplot_index)
    plt.title(title)
    plt.scatter(labels, accuracy, c=COLOR_PALETTE[:-1])
    plt.grid()

def display_image_napari(image, points_count, points_size, title='Napari Image Viewer', colormap=CMAP, scale=[1, 1, 1], custom_points=None, auto_points=None):
    """
    Display the given image using Napari viewer with the specified colormap, an additional points layer
    positioned around the center of the image in 'select' mode, and text annotations for each point. Optionally,
    display custom points if provided.

    Parameters:
    image (ndarray): The image to visualize.
    points_count (int): The number of points to display in the points layer (ignored if custom_points is provided).
    points_size (float): The size of the points to be displayed.
    title (str): The window title for the Napari viewer.
    colormap (str): The name of the colormap to use.
    custom_points (ndarray): Optional custom points to display instead of the generated points.

    Returns:
    Viewer: The Napari viewer instance.
    """
    viewer = napari.Viewer(title=title)

    if image.ndim == 3:
        viewer.add_image(image, colormap=colormap, scale=scale)
        viewer.dims.ndisplay = 3
    elif image.ndim == 2:
        viewer.add_image(image, colormap=colormap)
        scale = [1, 1]

    # Assign colors from the palette to each point's edge
    point_colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(points_count)]

    # Set the properties for the points including the text
    properties = {'number': [str(i+1) for i in range(points_count)]}  # Starting at 1
    if image.ndim == 2:
        text_parameters = {
            'text': 'S{number}',
            'size': 10,
            'color': 'white',
            'anchor': 'upper_left',
            'translation': [-10, 0]  # Adjust text offset if needed
        }
    elif image.ndim == 3:
        text_parameters = {
            'text': 'S{number}',
            'size': 10,
            'color': 'white',
            'anchor': 'upper_left',
            'translation': [-4, -10, -10]  # Adjust text offset if needed
        }        

    # If custom points are provided, use them; otherwise, generate points around the center
    if custom_points is not None:
        points_layer = viewer.add_points(custom_points*scale, size=points_size/10, edge_width=0.1,
                                         face_color=point_colors, edge_color='black',
                                         symbol='cross',
                                         name='Transformed Points')

        points_layer.editable = False

        if auto_points is not None:
            points_layer = viewer.add_points(auto_points*scale, size=points_size/10, edge_width=0.1,
                                            face_color=point_colors, edge_color='black',
                                            symbol='disc',
                                            name='Detected Points')
            
            points_layer.editable = False
    else:
        # Calculate the center of the image
        center_y, center_x = np.array(image.shape[:2]) / 2

        # Generate points in a circular pattern around the center
        angle_step = 2 * np.pi / points_count
        radius = min(center_x, center_y) / 4  # Adjust the radius as necessary
        points = np.array([
            (center_y + radius * np.sin(i * angle_step), center_x + radius * np.cos(i * angle_step))
            for i in range(points_count)
        ])

        # Add a points layer with the generated points
        points_layer = viewer.add_points(points, size=points_size, edge_width=0.05,
                                            edge_color=point_colors, face_color='transparent',
                                            name='Target Points')
        
    # Update the points layer with the properties and text
    points_layer.properties = properties
    points_layer.text = text_parameters
    
    # Set the points layer to 'select' mode
    points_layer.mode = 'select'
    
    # Start the Napari event loop
    napari.run()

    # After the window is closed, return the coordinates
    return points_layer.data
