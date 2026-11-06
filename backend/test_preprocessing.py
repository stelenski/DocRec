import matplotlib.pyplot as plt

from app.preprocessing.image_processor import ImagePreprocessor


processor = ImagePreprocessor(
    "test_images/sample.jpg"
)

original = processor.image

enhanced = processor.run(
    enhance=True
)

plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
plt.imshow(original)
plt.title("Original Image")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(enhanced)
plt.title("Enhanced Image")
plt.axis("off")

plt.tight_layout()
plt.show()

processor.save(
    "test_images/enhanced_sample.png"
)