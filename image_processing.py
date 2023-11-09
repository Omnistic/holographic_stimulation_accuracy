import numpy as np
from config import MIN_OPERATOR_SIZE, MAX_OPERATOR_SIZE
from skimage import io
from skimage.filters import median, threshold_otsu
from skimage.measure import regionprops, label
from skimage.morphology import disk, ball, closing, erosion, dilation

def read_image(image_path):
    return np.asarray(io.imread(image_path))

def binary_kernel(operator_size, dim=2):
    if dim == 2:
        return disk(operator_size)
    elif dim == 3:
        return ball(operator_size)
    else:
        return None

def locate_blobs(image, number_of_blobs):
    """
    Apply preprocessing to an image to detect a specific number of blobs and calculate the average major axis length.
    
    Parameters:
    image (ndarray): The input image to preprocess.
    number_of_blobs (int): The desired number of blobs to detect in the image.
    
    Returns:
    tuple: The detected regions, the disk size used, and the average major axis length of the blobs.
    """

    operator_size = MIN_OPERATOR_SIZE

    kernel = binary_kernel(operator_size, image.ndim)

    if kernel is None:
        return None

    processed_image = median(image, kernel)
    processed_image = processed_image > threshold_otsu(processed_image)

    return processed_image

    operator_size = 3

    # Preprocess the image
    if image.ndim == 2:
        preprocessed_image = median(image, disk(operator_size))
    else:
        preprocessed_image = median(image, ball(operator_size))
    thresh = threshold_otsu(preprocessed_image)
    preprocessed_image = preprocessed_image > thresh

    # Increase operator size until the desired number of blobs is detected
    while operator_size <= MAX_OPERATOR_SIZE:
        if image.ndim == 2:
            preprocessed_image = closing(preprocessed_image, disk(operator_size))
        if image.ndim == 3:
            preprocessed_image = erosion(preprocessed_image, ball(operator_size))
        else:
            return None

        labeled_image = label(preprocessed_image)
        regions = regionprops(labeled_image)

        if len(regions) == number_of_blobs:
            avg_major_axis_length = np.mean([region.major_axis_length for region in regions])
            return regions, operator_size, avg_major_axis_length
        
        operator_size += 1

    return None