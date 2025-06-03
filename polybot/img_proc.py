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
    """Handles all S3 operations for image uploads using IAM role authentication"""
    
    def __init__(self):
        self.aws_region = os.getenv('AWS_REGION', 'us-west-2')
        self.bucket_name = os.getenv('AWS_DEV_S3_BUCKET')
        self.s3_client = None
        
        # Initialize S3 client - will automatically use IAM role
        self._initialize_s3_client()
    
    def _has_minimal_config(self) -> bool:
        """Check if we have at least region and bucket configured"""
        return all([
            self.aws_region,
            self.bucket_name
        ])
    
    def _initialize_s3_client(self) -> bool:
        """Initialize the S3 client using IAM role authentication"""
        try:
            if not self._has_minimal_config():
                logger.error("Missing required AWS configuration (region or bucket)")
                return False
            
            # Create S3 client - boto3 will automatically use IAM role when available
            logger.info("Initializing S3 client using IAM role authentication...")
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
            
            # Test S3 access by checking if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.success(f"✅ S3 client initialized successfully using IAM role! Region: {self.aws_region}, Bucket: {self.bucket_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                logger.error(f"❌ Access denied to S3 bucket '{self.bucket_name}'. Check IAM role permissions.")
            elif error_code == '404':
                logger.error(f"❌ S3 bucket '{self.bucket_name}' not found.")
            else:
                logger.error(f"❌ S3 client initialization failed: {error_code}")
            return False
        except NoCredentialsError:
            logger.error("❌ No AWS credentials found. Please ensure IAM role is attached to EC2 instance.")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {e}")
            return False
    
    def upload_file(self, local_path: Path, s3_key: Optional[str] = None) -> bool:
        """Upload a file to S3 using IAM role authentication"""
        if not self._has_minimal_config():
            logger.warning("⚠️ AWS configuration not available. Skipping S3 upload.")
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
                logger.error(f"❌ File does not exist: {local_path}")
                return False
            
            # Upload the file
            logger.info(f"📤 Uploading {local_path.name} ({local_path.stat().st_size} bytes) to S3...")
            
            self.s3_client.upload_file(
                str(local_path), 
                self.bucket_name, 
                s3_key
            )
            
            logger.success(f"✅ Successfully uploaded to S3: s3://{self.bucket_name}/{s3_key}")
            return True
                
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found - ensure IAM role is attached")
            return False
        except ClientError as e:
            logger.error(f"❌ AWS S3 error during upload: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error uploading to S3: {e}")
            return False


class Img:
    """Image processing class with S3 integration using IAM role authentication"""

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
            logger.info(f"📷 Image loaded: {self.path.name} ({len(self.data)}x{len(self.data[0]) if self.data else 0})")
            
        except Exception as e:
            logger.error(f"❌ Error loading image {path}: {e}")
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
            logger.info(f"💾 Image saved locally: {new_path}")
            
            # Upload to S3 if requested
            if auto_upload_s3:
                upload_success = self.s3_manager.upload_file(new_path)
                if upload_success:
                    logger.info("☁️ Image successfully uploaded to S3")
                else:
                    logger.warning("⚠️ S3 upload failed, but local save was successful")
            
            return new_path
            
        except Exception as e:
            logger.error(f"❌ Error saving image: {e}")
            raise

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
