from pathlib import Path
import matplotlib
from matplotlib.image import imread, imsave
import numpy as np
import random
import boto3
import os


def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Constructor that loads and normalizes image to [0, 255] grayscale
        """
        self.path = Path(path)
        gray = rgb2gray(imread(path))

        # Normalize to [0, 255] for test compatibility
        if gray.max() <= 1.0:
            gray = gray * 255.0

        self.data = gray.tolist()

    def save_img(self):
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, np.array(self.data) / 255.0, cmap='gray')  # Normalize for saving

        # Check if we have AWS credentials before attempting to upload
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION')
        bucket_name = os.getenv('AWS_DEV_S3_BUCKET')

        # Only attempt to upload if we have all required AWS credentials
        if aws_access_key and aws_secret_key and aws_region and bucket_name:
            try:
                # Initialize S3 client
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )

                # Upload the file
                object_name = new_path.name  # Use just the file name for S3 key
                s3.upload_file(str(new_path), bucket_name, object_name)
                print(f"Uploaded {object_name} to S3 bucket {bucket_name}")
            except Exception as e:
                print(f"Error uploading to S3: {e}")
        else:
            print("Skipping S3 upload - AWS credentials not configured")

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
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0
        rotated = [[0 for _ in range(height)] for _ in range(width)]
        for i in range(height):
            for j in range(width):
                rotated[j][height - 1 - i] = self.data[i][j]
        self.data = rotated

    def salt_n_pepper(self):
        """
        Add salt (255) and pepper (0) noise to the image
        """
        arr = np.array(self.data, dtype=float)
        height, width = arr.shape
        total_pixels = height * width

        num_salt = int(total_pixels * 0.15)
        num_pepper = int(total_pixels * 0.15)

        random.seed(42)
        all_indices = [(i, j) for i in range(height) for j in range(width)]
        random.shuffle(all_indices)

        for i, j in all_indices[:num_salt]:
            arr[i, j] = 255.0  # Salt

        for i, j in all_indices[num_salt:num_salt + num_pepper]:
            arr[i, j] = 0.0  # Pepper

        self.data = arr.tolist()

    def concat(self, other_img, direction='horizontal'):
        if not isinstance(other_img, Img):
            raise TypeError("other_img must be an Img object")

        height1 = len(self.data)
        width1 = len(self.data[0]) if height1 > 0 else 0

        height2 = len(other_img.data)
        width2 = len(other_img.data[0]) if height2 > 0 else 0

        if direction == 'horizontal':
            min_height = min(height1, height2)
            result = []
            for i in range(min_height):
                result.append(self.data[i] + other_img.data[i])

        elif direction == 'vertical':
            result = []
            for row in self.data:
                result.append(row[:])
            for row in other_img.data:
                adjusted_row = row[:min(width1, len(row))]
                if len(adjusted_row) < width1:
                    adjusted_row.extend([0.0] * (width1 - len(adjusted_row)))
                result.append(adjusted_row)
        else:
            raise ValueError("Direction must be either 'horizontal' or 'vertical'")

        self.data = result

    def segment(self):
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0

        total = 0
        count = 0
        for i in range(height):
            for j in range(width):
                total += self.data[i][j]
                count += 1

        threshold = total / count if count > 0 else 127.5

        for i in range(height):
            for j in range(width):
                self.data[i][j] = 255.0 if self.data[i][j] > threshold else 0.0
