import os
import numpy as np

from PIL import Image, ImageDraw


def format_photo(path: os.PathLike | str):
    """ resizes the image and makes it round """
    # --------------------------- make image round ---------------------------
    # Open the input image as numpy array, convert to RGB
    img = Image.open(path).convert("RGB")
    np_image = np.array(img)
    # Create same size alpha layer with circle
    alpha = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(alpha)
    draw.pieslice(((0, 0), img.size), 0, 360, fill=255)
    # Convert alpha Image to numpy array
    np_alpha = np.array(alpha)
    # Add alpha layer to RGB
    np_image = np.dstack((np_image, np_alpha))
    # --------------------------- resize image ---------------------------
    img = Image.fromarray(np_image)
    img.thumbnail((64, 64), Image.Resampling.LANCZOS)
    path = ".".join(path.split(".")[:-1]) + ".png"
    img.save(path, "png")


def check_size(path: os.PathLike | str) -> bool:
    """ :return: True if size is valid, otherwise False """
    img = Image.open(path)
    if img.size[0] >= 64 <= img.size[1]:
        return True
    return False


if __name__ == '__main__':
    pass
