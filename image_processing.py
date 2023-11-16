import numpy as np
from config import MEDIAN_KERNEL_SIZE, OPENING_KERNEL_SIZE
from scipy.spatial import cKDTree
from scipy.optimize import minimize
from skimage import io
from skimage.filters import median, threshold_otsu
from skimage.measure import regionprops, label
from skimage.morphology import disk, ball, opening
from sklearn.metrics import mean_squared_error

def median_filter(image):
    if image.ndim == 2:
        return median(image, disk(MEDIAN_KERNEL_SIZE))
    elif image.ndim == 3:
        return median(image, ball(MEDIAN_KERNEL_SIZE))

def write_image(image_path, image):
    io.imsave(image_path, image)

def read_image(image_path, dtype=None):
    return np.asarray(io.imread(image_path), dtype=dtype)

def maximum_intensity_projection(stack):
    return np.amax(stack, axis=0)

def add_z(points, z_spacing, z_size):
    number_of_blobs = points.shape[0]
    middle_index = int( ( ( z_size - 1 ) / 2 ) )
    z_half_range = int( ( number_of_blobs - 1 ) / 2 * z_spacing )

    indices = np.zeros(number_of_blobs, dtype=int)

    for ii in range(number_of_blobs):
        indices[ii] = middle_index + z_half_range - ii * z_spacing

    return np.hstack((indices.reshape(-1, 1), points))

def binary_kernel(operator_size, dim=2):
    if dim == 2:
        return disk(operator_size)
    elif dim == 3:
        return ball(operator_size)
    else:
        return None

def get_largest_regions_by_area(labels, num_regions=1):
    """
    Return the specified number of regions with the largest areas from a labeled image.
    
    :param labels: Labeled input image (e.g., from skimage.segmentation).
    :param num_regions: Number of regions to return.
    :return: List of region properties for the largest areas.
    """
    # Get region properties
    regions = regionprops(labels)

    # Sort regions by area in descending order
    sorted_regions = sorted(regions, key=lambda x: x.area, reverse=True)

    # Return the top 'num_regions' regions
    return sorted_regions[:num_regions]

def locate_blobs(image, number_of_blobs):
    threshold = threshold_otsu(image)
    binary_image = image > threshold

    binary_image = opening(binary_image, binary_kernel(OPENING_KERNEL_SIZE, dim=image.ndim))

    labels = label(binary_image)
    regions = get_largest_regions_by_area(labels, number_of_blobs)

    centroids = np.array([region.centroid for region in regions])
    avg_major_axis_length = np.mean([region.major_axis_length for region in regions])
            
    return centroids, avg_major_axis_length

def find_closest_regions(napari_points, auto_points):
    """
    Match user-selected points from Napari to the closest unique automatically located points.

    Parameters:
    napari_points (ndarray): The coordinates of the points selected by the user in Napari.
    auto_points (ndarray): The coordinates of the points automatically located.

    Returns:
    ndarray: Unique centroids of the regions that are closest to the user-selected points, in the order the points were added.
    """
    used_indices = set()
    ordered_points = []

    for point in napari_points:
        # Rebuild the KD-tree in each iteration excluding already used points
        available_points = np.array([point for ii, point in enumerate(auto_points) if ii not in used_indices])
        tree = cKDTree(available_points)

        # Find the closest available point for the current user-selected point
        _, closest_idx = tree.query(point)
        closest_global_idx = [ii for ii in range(len(auto_points)) if ii not in used_indices][closest_idx]
        
        # Store the closest point and mark it as used
        ordered_points.append(auto_points[closest_global_idx])
        used_indices.add(closest_global_idx)

    return np.array(ordered_points)

def create_rotation_matrix(angle):
    """
    Create a 2D rotation matrix for a given angle.
    
    Parameters:
    angle (float or array-like): The rotation angle in radians. If an array is passed, it should have a single element.
    
    Returns:
    ndarray: The 2x2 rotation matrix.
    """
    # If the angle is an array with one element, extract the scalar value
    if isinstance(angle, (list, np.ndarray)) and len(angle) == 1:
        angle = angle[0]
    
    c, s = np.cos(angle), np.sin(angle)
    rotation_matrix = np.array([[c, -s], [s, c]])
    return rotation_matrix

def calculate_rmse_after_rotation(angle, reference_coordinates, coordinates_to_be_rotated):
    rotation_matrix = create_rotation_matrix(angle)
    rotated_coordinates = np.dot(coordinates_to_be_rotated, rotation_matrix.T)
    return mean_squared_error(reference_coordinates, rotated_coordinates)

def find_transform(points_1, points_2):
    # Find center of mass of each set of points
    center_of_mass_1 = np.mean(points_1, axis=0)
    center_of_mass_2 = np.mean(points_2, axis=0)

    # Center each set of points around its center of mass
    centered_points_1 = points_1 - center_of_mass_1
    centered_points_2 = points_2 - center_of_mass_2

    # Find the norm of each set of centered points
    norm_1 = np.linalg.norm(centered_points_1)
    norm_2 = np.linalg.norm(centered_points_2)

    # Find the scaling factor between the two sets of points
    scaling_factor = norm_2 / norm_1

    # Apply scaling to the first set of centered points
    scaled_1 = centered_points_1 * scaling_factor

    # Find the rotation angle from the reference to the target
    result = minimize(
        calculate_rmse_after_rotation,
        0,
        args=(scaled_1, centered_points_2),
        method="L-BFGS-B"
    )

    if not result.success:
        raise ValueError("Optimization failed: " + result.message)

    angle = result.x[0]

    return center_of_mass_1, center_of_mass_2, scaling_factor, angle

def transform_coordinates(points_1, center_1, center_2, scaling_factor, angle):
    # Center the coordinates
    coordinates_centered = points_1 - center_1

    # Scale the centered coordinates
    coordinates_scaled = coordinates_centered * scaling_factor

    # Create the rotation matrix using the given angle
    rotation_matrix = create_rotation_matrix(-angle)

    # Rotate the scaled coordinates
    coordinates_rotated = np.dot(coordinates_scaled, rotation_matrix.T)

    # Apply the target center
    coordinates_transformed = coordinates_rotated + center_2

    return coordinates_transformed