from pathlib import Path
from matplotlib.image import imread, imsave
import numpy as np
import random


def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def blur(self, blur_level=16):
        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j - 1] - row[j]))

            self.data[i] = res

    def rotate(self):
        """
        Rotate the image by 90 degrees clockwise
        """
        # Get dimensions
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0

        # Create a new empty matrix with swapped dimensions
        rotated = [[0 for _ in range(height)] for _ in range(width)]

        # Fill the rotated matrix
        for i in range(height):
            for j in range(width):
                # For 90° clockwise rotation: (i,j) -> (j, height-1-i)
                rotated[j][height - 1 - i] = self.data[i][j]

        self.data = rotated

    def salt_n_pepper(self):
        """
        Add salt and pepper noise to the image
        Creates visible salt (white) and pepper (black) particles
        """
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0

        # Increase the probabilities to make particles more visible
        salt_prob = 0.2
        pepper_prob = 0.16

        # Apply salt and pepper noise
        for i in range(height):
            for j in range(width):
                # Generate random value for this pixel
                r = random.random()

                # Apply salt (white) - make particles more visible
                if r < salt_prob:
                    # Create small salt clusters (2x2 pixels when possible)
                    self.data[i][j] = 1.0
                    # Try to extend salt particle to adjacent pixels
                    if i + 1 < height and j + 1 < width and random.random() < 0.5:
                        self.data[i + 1][j] = 1.0
                        self.data[i][j + 1] = 1.0
                        self.data[i + 1][j + 1] = 1.0

                # Apply pepper (black) - make particles more visible
                elif r < salt_prob + pepper_prob:
                    # Create small pepper clusters (2x2 pixels when possible)
                    self.data[i][j] = 0.0
                    # Try to extend pepper particle to adjacent pixels
                    if i + 1 < height and j + 1 < width and random.random() < 0.5:
                        self.data[i + 1][j] = 0.0
                        self.data[i][j + 1] = 0.0
                        self.data[i + 1][j + 1] = 0.0

    def concat(self, other_img, direction='horizontal'):
        """
        Concatenate another image with this one, either horizontally or vertically
        """
        # Check that other_img is an Img object
        if not isinstance(other_img, Img):
            raise TypeError("other_img must be an Img object")

        # Get dimensions of both images
        height1 = len(self.data)
        width1 = len(self.data[0]) if height1 > 0 else 0

        height2 = len(other_img.data)
        width2 = len(other_img.data[0]) if height2 > 0 else 0

        if direction == 'horizontal':
            # For horizontal concatenation, we need to match heights
            min_height = min(height1, height2)

            # Create a new matrix for the result
            result = []

            # Concatenate rows up to the minimum height
            for i in range(min_height):
                result.append(self.data[i] + other_img.data[i])

        elif direction == 'vertical':
            # For vertical concatenation, we need to match widths
            # If widths don't match, we'll use the width of the first image

            # Create a new matrix for the result
            result = []

            # First add all rows from the first image
            for row in self.data:
                result.append(row[:])

            # Then add all rows from the second image
            for row in other_img.data:
                # Make sure the row matches the width of the first image
                if width1 > 0:
                    adjusted_row = row[:min(width1, len(row))]
                    # If the row is too short, pad it
                    if len(adjusted_row) < width1:
                        adjusted_row.extend([0] * (width1 - len(adjusted_row)))
                    result.append(adjusted_row)
        else:
            raise ValueError("Direction must be either 'horizontal' or 'vertical'")

        self.data = result

    def segment(self):
        """
        Segment the image into binary black and white format
        """
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0

        # First, find the average intensity of the image
        total = 0
        count = 0
        for i in range(height):
            for j in range(width):
                total += self.data[i][j]
                count += 1

        # Calculate adaptive threshold based on the average
        threshold = total / count if count > 0 else 0.5

        # Apply thresholding
        for i in range(height):
            for j in range(width):
                # Values above threshold become white (1.0)
                # Values below or equal to threshold become black (0.0)
                self.data[i][j] = 1.0 if self.data[i][j] > threshold else 0.0