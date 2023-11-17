# Configuration File for Display and Image Processing Parameters

# Display Parameters
# ------------------

# Default colormap for visualizations.
# This is used to map normalized data values to colors in visualizations.
CMAP = 'gray'

# Colorblind-friendly color palette.
# This palette is designed to be easily distinguishable for individuals with color vision deficiencies.
# Each color is represented in hexadecimal format.
COLOR_PALETTE = [
    '#e69f00',  # Orange: bright and clear for visibility
    '#56b4e9',  # Sky Blue: light and soothing
    '#009e73',  # Bluish Green: distinct yet pleasant
    '#f0e442',  # Yellow: vibrant and eye-catching
    '#0072b2',  # Blue: standard and universally recognizable
    '#d55e00',  # Vermilion: a mix of red and orange
    '#cc79a7',  # Reddish Purple: a unique and distinct choice
    '#FFFFFF',  # White: classic and versatile
]

# Image Processing Parameters
# ---------------------------

# Median filter kernel size.
# This value determines the size of the kernel used for the median filtering operation,
# which is used to reduce noise in images.
MEDIAN_KERNEL_SIZE = 3

# Morphological opening kernel size.
# Defines the size for the structuring element used in morphological opening,
# which helps in removing small objects or details from an image.
OPENING_KERNEL_SIZE = 3

# Morphological dilation kernel size.
# Determines the size of the kernel used for morphological dilation,
# which is utilized to increase the size of brighter areas in an image,
# thereby enhancing prominent features.
DILATION_KERNEL_SIZE = 10
