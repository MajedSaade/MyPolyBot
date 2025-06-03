from pathlib import Path
import matplotlib
from matplotlib.image import imread, imsave
import numpy as np
import random
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
from loguru import logger
from datetime import datetime
from typing import Optional, Tuple


def rgb2gray(rgb):
    """Convert RGB image to grayscale"""
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class S3Manager:
    """Handles all S3 operations for image uploads"""
    
    def __init__(self):
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-west-2')
        self.bucket_name = os.getenv('AWS_DEV_S3_BUCKET')  # Only use dev bucket
        self.s3_client = None
        
        # Initialize S3 client if credentials are available
        if self._has_credentials():
            self._initialize_s3_client()
    
    def _has_credentials(self) -> bool:
        """Check if all required AWS credentials are available"""
        return all([
            self.aws_access_key,
            self.aws_secret_key,
            self.aws_region,
            self.bucket_name
        ])
    
    def _initialize_s3_client(self) -> bool:
        """Initialize the S3 client with credentials"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            logger.info(f"S3 client initialized for region: {self.aws_region}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            return False
    
    def upload_file(self, local_path: Path, s3_key: Optional[str] = None) -> bool:
        """Upload a file to S3"""
        if not self._has_credentials():
            logger.warning("AWS credentials not available. Skipping S3 upload.")
            self._log_missing_credentials()
            return False
        
        if not self.s3_client:
            if not self._initialize_s3_client():
                return False
        
        try:
            # Generate S3 key if not provided
            if s3_key is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                s3_key = f"processed_images/{timestamp}_{local_path.name}"
            
            # Check file exists
            if not local_path.exists():
                logger.error(f"File does not exist: {local_path}")
                return False
            
            # Check if file already exists in S3
            if self._file_exists_in_s3(s3_key):
                logger.warning(f"File already exists in S3: {s3_key}")
                # Generate unique key
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                s3_key = f"processed_images/{timestamp}_{local_path.name}"
            
            # Upload the file
            logger.info(f"Uploading {local_path.name} ({local_path.stat().st_size} bytes) to S3 bucket {self.bucket_name}")
            
            self.s3_client.upload_file(
                str(local_path), 
                self.bucket_name, 
                s3_key
            )
            
            # Verify upload
            if self._verify_upload(s3_key):
                logger.success(f"Successfully uploaded {local_path.name} to S3: s3://{self.bucket_name}/{s3_key}")
                return True
            else:
                logger.error(f"Upload verification failed for {s3_key}")
                return False
                
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False
        except ClientError as e:
            logger.error(f"AWS S3 error during upload: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _file_exists_in_s3(self, s3_key: str) -> bool:
        """Check if a file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking if file exists in S3: {e}")
                return False
    
    def _verify_upload(self, s3_key: str) -> bool:
        """Verify that the file was successfully uploaded to S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Upload verified: {s3_key}, Size: {response['ContentLength']} bytes")
            return True
        except Exception as e:
            logger.error(f"Failed to verify upload: {e}")
            return False
    
    def _log_missing_credentials(self):
        """Log which AWS credentials are missing"""
        missing = []
        if not self.aws_access_key:
            missing.append("AWS_ACCESS_KEY_ID")
        if not self.aws_secret_key:
            missing.append("AWS_SECRET_ACCESS_KEY")
        if not self.aws_region:
            missing.append("AWS_REGION")
        if not self.bucket_name:
            missing.append("AWS_DEV_S3_BUCKET")
        
        logger.warning(f"Missing AWS environment variables: {', '.join(missing)}")


class Img:
    """Image processing class with S3 integration"""

    def __init__(self, path):
        """
        Constructor that loads and normalizes image to [0, 255] grayscale
        """
        self.path = Path(path)
        self.s3_manager = S3Manager()
        
        # Load and convert image to grayscale
        try:
            gray = rgb2gray(imread(path))
            
            # Normalize to [0, 255] for test compatibility
            if gray.max() <= 1.0:
                gray = gray * 255.0
            
            self.data = gray.tolist()
            logger.info(f"Image loaded: {self.path.name} ({len(self.data)}x{len(self.data[0]) if self.data else 0})")
            
        except Exception as e:
            logger.error(f"Error loading image {path}: {e}")
            raise

    def save_img(self, auto_upload_s3: bool = True, custom_suffix: str = "_filtered") -> Path:
        """
        Save the processed image locally and optionally upload to S3
        
        Args:
            auto_upload_s3: Whether to automatically upload to S3
            custom_suffix: Custom suffix for the saved file
        
        Returns:
            Path to the saved file
        """
        # Generate new file path
        new_path = self.path.with_name(self.path.stem + custom_suffix + self.path.suffix)
        
        try:
            # Save image locally
            imsave(new_path, np.array(self.data) / 255.0, cmap='gray')
            
            logger.info(f"Image saved locally: {new_path}")
            logger.info(f"Absolute path: {os.path.abspath(new_path)}")
            logger.info(f"File size: {os.path.getsize(new_path)} bytes")
            
            # Upload to S3 if requested
            if auto_upload_s3:
                upload_success = self.s3_manager.upload_file(new_path)
                if upload_success:
                    logger.info("Image successfully uploaded to S3")
                else:
                    logger.warning("S3 upload failed, but local save was successful")
            
            return new_path
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            raise

    def blur(self, blur_level: int = 16) -> 'Img':
        """
        Apply blur filter to the image
        
        Args:
            blur_level: Size of the blur kernel (higher = more blur)
        
        Returns:
            Self for method chaining
        """
        if blur_level <= 0:
            logger.warning("Blur level must be positive, skipping blur")
            return self
            
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0
        
        if height < blur_level or width < blur_level:
            logger.warning(f"Image too small for blur level {blur_level}, skipping blur")
            return self
        
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
        logger.info(f"Blur filter applied with level {blur_level}")
        return self

    def contour(self) -> 'Img':
        """
        Apply contour detection (edge detection) to the image
        
        Returns:
            Self for method chaining
        """
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j - 1] - row[j]))
            self.data[i] = res
        
        logger.info("Contour filter applied")
        return self

    def rotate(self) -> 'Img':
        """
        Rotate the image 90 degrees clockwise
        
        Returns:
            Self for method chaining
        """
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0
        
        if height == 0 or width == 0:
            logger.warning("Cannot rotate empty image")
            return self
        
        rotated = [[0 for _ in range(height)] for _ in range(width)]
        for i in range(height):
            for j in range(width):
                rotated[j][height - 1 - i] = self.data[i][j]
        
        self.data = rotated
        logger.info("Image rotated 90 degrees clockwise")
        return self

    def salt_n_pepper(self, noise_level: float = 0.15) -> 'Img':
        """
        Add salt (255) and pepper (0) noise to the image
        
        Args:
            noise_level: Proportion of pixels to affect (0.0 to 1.0)
        
        Returns:
            Self for method chaining
        """
        if not (0.0 <= noise_level <= 1.0):
            logger.warning("Noise level must be between 0.0 and 1.0")
            noise_level = 0.15
        
        arr = np.array(self.data, dtype=float)
        height, width = arr.shape
        total_pixels = height * width

        num_salt = int(total_pixels * noise_level)
        num_pepper = int(total_pixels * noise_level)

        random.seed(42)  # For reproducible results
        all_indices = [(i, j) for i in range(height) for j in range(width)]
        random.shuffle(all_indices)

        # Add salt noise
        for i, j in all_indices[:num_salt]:
            arr[i, j] = 255.0

        # Add pepper noise
        for i, j in all_indices[num_salt:num_salt + num_pepper]:
            arr[i, j] = 0.0

        self.data = arr.tolist()
        logger.info(f"Salt and pepper noise applied with level {noise_level}")
        return self

    def concat(self, other_img: 'Img', direction: str = 'horizontal') -> 'Img':
        """
        Concatenate this image with another image
        
        Args:
            other_img: Another Img object to concatenate with
            direction: 'horizontal' or 'vertical'
        
        Returns:
            Self for method chaining
        """
        if not isinstance(other_img, Img):
            raise TypeError("other_img must be an Img object")

        height1 = len(self.data)
        width1 = len(self.data[0]) if height1 > 0 else 0

        height2 = len(other_img.data)
        width2 = len(other_img.data[0]) if height2 > 0 else 0

        if direction == 'horizontal':
            if height1 == 0 or height2 == 0:
                logger.warning("Cannot concatenate horizontally with empty images")
                return self
                
            min_height = min(height1, height2)
            result = []
            for i in range(min_height):
                result.append(self.data[i] + other_img.data[i])

        elif direction == 'vertical':
            if width1 == 0 and width2 == 0:
                logger.warning("Cannot concatenate vertically with empty images")
                return self
                
            result = []
            # Add first image
            for row in self.data:
                result.append(row[:])
            
            # Add second image, adjusting width if necessary
            target_width = width1 if width1 > 0 else width2
            for row in other_img.data:
                adjusted_row = row[:min(target_width, len(row))]
                if len(adjusted_row) < target_width:
                    adjusted_row.extend([0.0] * (target_width - len(adjusted_row)))
                result.append(adjusted_row)
        else:
            raise ValueError("Direction must be either 'horizontal' or 'vertical'")

        self.data = result
        logger.info(f"Image concatenated {direction}ly")
        return self

    def segment(self, threshold: Optional[float] = None) -> 'Img':
        """
        Apply binary segmentation to the image
        
        Args:
            threshold: Custom threshold value. If None, uses image mean.
        
        Returns:
            Self for method chaining
        """
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0

        if height == 0 or width == 0:
            logger.warning("Cannot segment empty image")
            return self

        # Calculate threshold if not provided
        if threshold is None:
            total = 0
            count = 0
            for i in range(height):
                for j in range(width):
                    total += self.data[i][j]
                    count += 1

            threshold = total / count if count > 0 else 127.5

        # Apply segmentation
        for i in range(height):
            for j in range(width):
                self.data[i][j] = 255.0 if self.data[i][j] > threshold else 0.0

        logger.info(f"Image segmented with threshold {threshold:.2f}")
        return self

    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get image dimensions
        
        Returns:
            Tuple of (height, width)
        """
        height = len(self.data)
        width = len(self.data[0]) if height > 0 else 0
        return height, width

    def get_stats(self) -> dict:
        """
        Get basic statistics about the image
        
        Returns:
            Dictionary with min, max, mean values
        """
        if not self.data:
            return {"min": 0, "max": 0, "mean": 0, "pixels": 0}
        
        flat_data = [pixel for row in self.data for pixel in row]
        
        return {
            "min": min(flat_data),
            "max": max(flat_data),
            "mean": sum(flat_data) / len(flat_data),
            "pixels": len(flat_data)
        }

    def reset(self):
        """Reset image to original state"""
        try:
            gray = rgb2gray(imread(self.path))
            if gray.max() <= 1.0:
                gray = gray * 255.0
            self.data = gray.tolist()
            logger.info("Image reset to original state")
        except Exception as e:
            logger.error(f"Error resetting image: {e}")

    def apply_multiple_filters(self, filters: list, auto_upload_each: bool = False) -> 'Img':
        """
        Apply multiple filters in sequence
        
        Args:
            filters: List of tuples (filter_name, kwargs)
            auto_upload_each: Whether to upload to S3 after each filter
        
        Returns:
            Self for method chaining
        """
        for i, (filter_name, kwargs) in enumerate(filters):
            if hasattr(self, filter_name):
                logger.info(f"Applying filter {i+1}/{len(filters)}: {filter_name}")
                getattr(self, filter_name)(**kwargs)
                
                if auto_upload_each:
                    temp_path = self.save_img(custom_suffix=f"_step_{i+1}_{filter_name}")
                    logger.info(f"Intermediate result saved and uploaded: {temp_path.name}")
            else:
                logger.error(f"Unknown filter: {filter_name}")
        
        return self