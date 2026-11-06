
import cv2
import numpy as np

from PIL import Image, ImageOps
from pathlib import Path


class ImagePreprocessor:

    def __init__(self, image_path):

        self.image_path = Path(image_path)

        # Load image while preserving EXIF orientation
        pil_image = Image.open(self.image_path)
        pil_image = ImageOps.exif_transpose(pil_image)

        # Convert to RGB
        self.original = pil_image.convert("RGB")

        self.image = np.array(self.original)

        self.processed = self.image.copy()

    def resize_image(self, max_dimension=3000):

        height, width = self.processed.shape[:2]

        if max(height, width) > max_dimension:

            scale = max_dimension / max(height, width)

            self.processed = cv2.resize(
                self.processed,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_AREA
            )

        return self.processed

    def upscale_small_image(self, min_dimension=1200):

        height, width = self.processed.shape[:2]

        if min(height, width) < min_dimension:

            scale = min_dimension / min(height, width)

            # Avoid excessive upscaling
            scale = min(scale, 2.0)

            self.processed = cv2.resize(
                self.processed,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC
            )

        return self.processed

    def denoise(self):

        self.processed = cv2.fastNlMeansDenoisingColored(
            self.processed,
            None,
            5,
            5,
            7,
            21
        )

        return self.processed

    def enhance_contrast(self, clip_limit=2.0):

        lab = cv2.cvtColor(
            self.processed,
            cv2.COLOR_RGB2LAB
        )

        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=(8, 8)
        )

        enhanced_l = clahe.apply(l)

        enhanced = cv2.merge(
            (enhanced_l, a, b)
        )

        self.processed = cv2.cvtColor(
            enhanced,
            cv2.COLOR_LAB2RGB
        )

        return self.processed

    def sharpen(self):

        blurred = cv2.GaussianBlur(
            self.processed,
            (0, 0),
            2
        )

        self.processed = cv2.addWeighted(
            self.processed,
            1.5,
            blurred,
            -0.5,
            0
        )

        return self.processed

    def deskew(self):

        gray = cv2.cvtColor(
            self.processed,
            cv2.COLOR_RGB2GRAY
        )

        edges = cv2.Canny(gray, 50, 150)

        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )

        if lines is None:
            return self.processed

        angles = []

        for line in lines:

            x1, y1, x2, y2 = line[0]

            angle = np.degrees(
                np.arctan2(y2-y1, x2-x1)
            )

            if abs(angle) < 10:
                angles.append(angle)

        if not angles:
            return self.processed

        median_angle = float(np.median(angles))

        if abs(median_angle) < 0.3:
            return self.processed

        height, width = self.processed.shape[:2]

        center = (width // 2, height // 2)

        matrix = cv2.getRotationMatrix2D(
            center,
            median_angle,
            1.0
        )

        self.processed = cv2.warpAffine(
            self.processed,
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return self.processed

    def run(self, enhance=True):

        self.resize_image()

        self.upscale_small_image()

        if enhance:

            self.denoise()

            self.enhance_contrast()

            self.sharpen()

            self.deskew()

        return self.processed

    def save(self, output_path):

        Image.fromarray(
            self.processed
        ).save(
            output_path,
            format="PNG"
        )
