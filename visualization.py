import matplotlib.pyplot as plt
from config import CMAP

def visualize_image(image, title='Image Viewer'):
    plt.figure()
    plt.imshow(image, cmap=CMAP)
    plt.title(title)
    plt.show()