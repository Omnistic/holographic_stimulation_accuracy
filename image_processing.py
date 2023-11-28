import numpy as np
from config import MEDIAN_KERNEL_SIZE, OPENING_KERNEL_SIZE, DILATION_KERNEL_SIZE
from scipy.spatial import cKDTree
from scipy.optimize import minimize
from skimage import io
from skimage.filters import median, threshold_otsu
from skimage.measure import regionprops, label
from skimage.morphology import disk, ball, opening, dilation
from sklearn.metrics import mean_squared_error

def median_filter(image):
    """
    Apply a median filter to an image.

    Parameters:
    image (ndarray): The input image.

    Returns:
    ndarray: The filtered image.
    """
    return median(image, binary_kernel(MEDIAN_KERNEL_SIZE, image.ndim))

def write_image(image_path, image):
    """
    Save an image to a specified path.

    Parameters:
    image_path (str): The file path to save the image.
    image (ndarray): The image to be saved.
    """
    io.imsave(image_path, image)

def read_image(image_path, dtype=None):
    """
    Read an image from a specified path.

    Parameters:
    image_path (str): The file path of the image to read.
    dtype (data-type, optional): The desired data-type for the array. If None, the dtype of the loaded image is used.

    Returns:
    ndarray: The image as an array.
    """
    return np.asarray(io.imread(image_path), dtype=dtype)

def add_z(points, z_spacing, z_size):
    """
    Add a Z-dimension to 2D points based on specified spacing and size.

    Parameters:
    points (ndarray): The 2D points.
    z_spacing (int): The spacing between points in the Z dimension.
    z_size (int): The total size in the Z dimension.

    Returns:
    ndarray: The 3D points with Z-dimension added.
    """
    number_of_blobs = points.shape[0]
    middle_index = int((z_size - 1) / 2)
    z_half_range = int((number_of_blobs - 1) / 2 * z_spacing)

    indices = np.zeros(number_of_blobs, dtype=int)

    for ii in range(number_of_blobs):
        indices[ii] = middle_index + z_half_range - ii * z_spacing

    return np.hstack((indices.reshape(-1, 1), points))

def binary_kernel(operator_size, dim=2):
    """
    Generate a binary kernel for morphological operations.

    Parameters:
    operator_size (int): The size of the kernel.
    dim (int): The dimension of the kernel (2D or 3D).

    Returns:
    ndarray: The binary kernel.
    """
    if dim == 2:
        return disk(operator_size)
    elif dim == 3:
        return ball(operator_size)
    else:
        return None

def get_largest_regions_by_area(labels, num_regions=1):
    """
    Extract the largest regions by area from a labeled image.

    Parameters:
    labels (ndarray): A labeled image, typically from image segmentation.
    num_regions (int): Number of largest regions to extract.

    Returns:
    list: Region properties of the largest areas.
    """
    regions = regionprops(labels)
    sorted_regions = sorted(regions, key=lambda x: x.area, reverse=True)
    return sorted_regions[:num_regions]

def locate_blobs(image, number_of_blobs, source=1):
    """
    Locate significant blobs in an image using morphological operations.

    Parameters:
    image (ndarray): The input image.
    number_of_blobs (int): Number of blobs to identify.
    source (int): Determines the morphological operation (0 for dilation, otherwise opening).

    Returns:
    tuple: Centroids of identified blobs and average major axis length.
    """
    threshold = threshold_otsu(image)
    #if image.ndim == 3:
    #    threshold += 50
    binary_image = image > threshold

    if source == 0:
        binary_image = dilation(binary_image, binary_kernel(DILATION_KERNEL_SIZE, dim=image.ndim))
    else:
        #binary_image = opening(binary_image, binary_kernel(OPENING_KERNEL_SIZE, dim=image.ndim))
        pass
    
    import napari
    napari.view_image(binary_image)
    napari.run()

    labels = label(binary_image)
    regions = get_largest_regions_by_area(labels, number_of_blobs)

    centroids = np.array([region.centroid for region in regions])
    avg_major_axis_length = np.mean([region.major_axis_length for region in regions])
            
    return centroids, avg_major_axis_length

def find_closest_regions(napari_points, auto_points):
    """
    Match points from a user interface to the closest automatically located points.

    Parameters:
    napari_points (ndarray): Coordinates selected by the user.
    auto_points (ndarray): Automatically located coordinates.

    Returns:
    ndarray: Coordinates of the closest automatically located points to the user-selected points.
    """
    used_indices = set()
    ordered_points = []

    for point in napari_points:
        available_points = np.array([pt for ii, pt in enumerate(auto_points) if ii not in used_indices])
        tree = cKDTree(available_points)
        _, closest_idx = tree.query(point)
        closest_global_idx = [ii for ii in range(len(auto_points)) if ii not in used_indices][closest_idx]

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
    """
    Calculate the root mean square error (RMSE) after rotating a set of coordinates.

    Parameters:
    angle (float): Rotation angle in radians.
    reference_coordinates (ndarray): Reference coordinates.
    coordinates_to_be_rotated (ndarray): Coordinates to be rotated.

    Returns:
    float: RMSE between the reference and rotated coordinates.
    """
    rotation_matrix = create_rotation_matrix(angle)
    rotated_coordinates = np.dot(coordinates_to_be_rotated, rotation_matrix.T)
    return mean_squared_error(reference_coordinates, rotated_coordinates)

def find_transform(points_1, points_2):
    """
    Determine the transformation parameters (translation, scaling, rotation) between two sets of points.

    Parameters:
    points_1 (ndarray): First set of points.
    points_2 (ndarray): Second set of points.

    Returns:
    tuple: Center of mass for each set of points, scaling factor, and rotation angle.
    """
    center_of_mass_1 = np.mean(points_1, axis=0)
    center_of_mass_2 = np.mean(points_2, axis=0)

    centered_points_1 = points_1 - center_of_mass_1
    centered_points_2 = points_2 - center_of_mass_2

    norm_1 = np.linalg.norm(centered_points_1)
    norm_2 = np.linalg.norm(centered_points_2)

    scaling_factor = norm_2 / norm_1
    scaled_1 = centered_points_1 * scaling_factor

    result = minimize(calculate_rmse_after_rotation, 0, args=(scaled_1, centered_points_2), method="L-BFGS-B")
    if not result.success:
        raise ValueError("Optimization failed: " + result.message)

    angle = result.x[0]
    return center_of_mass_1, center_of_mass_2, scaling_factor, angle

def transform_coordinates(points_1, center_1, center_2, scaling_factor, angle):
    """
    Apply transformation (translation, scaling, rotation) to a set of coordinates.

    Parameters:
    points_1 (ndarray): Set of points to be transformed.
    center_1 (ndarray): Center of mass of the first set of points.
    center_2 (ndarray): Center of mass of the second set of points.
    scaling_factor (float): Scaling factor.
    angle (float): Rotation angle.

    Returns:
    ndarray: Transformed coordinates.
    """
    coordinates_centered = points_1 - center_1
    coordinates_scaled = coordinates_centered * scaling_factor
    rotation_matrix = create_rotation_matrix(-angle)
    coordinates_rotated = np.dot(coordinates_scaled, rotation_matrix.T)
    coordinates_transformed = coordinates_rotated + center_2

    return coordinates_transformed