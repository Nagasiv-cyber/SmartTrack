import glob
from collections import Counter

import numpy as np
from PIL import Image

root = "data/idd-lite"

# 1. How many images and labels are in each split?
for split in ["train", "val", "test"]:
    imgs = glob.glob(f"{root}/leftImg8bit/{split}/*/*")
    labels = glob.glob(f"{root}/gtFine/{split}/*/*")
    print(f"{split}: {len(imgs)} images, {len(labels)} label files")

# 2. What do the label files look like?
labels = sorted(glob.glob(f"{root}/gtFine/train/*/*.png"))
if not labels:
    print("No .png label files found - send me the output of: dir data\\idd-lite\\gtFine\\train\\0")
    raise SystemExit

first = Image.open(labels[0])
print("Example label file:", labels[0])
print("Label image size:", first.size, "| mode:", first.mode, "| array shape:", np.array(first).shape)

# 3. Which class numbers appear, and how much of the image does each cover?
counts = Counter()
for path in labels[:100]:
    arr = np.array(Image.open(path))
    values, n = np.unique(arr, return_counts=True)
    for v, c in zip(values, n):
        counts[int(v)] += int(c)

total = sum(counts.values())
print("Class values found in 100 label images (value: share of pixels):")
for v in sorted(counts):
    print(f"  {v}: {100 * counts[v] / total:.1f}%")