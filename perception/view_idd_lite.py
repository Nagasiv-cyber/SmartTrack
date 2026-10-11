import glob
import os
import random
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from PIL import Image

root = "data/idd-lite"

# Semantic labels only (skip the *_inst_label.png instance files)
labels = sorted(p for p in glob.glob(f"{root}/gtFine/train/*/*_label.png") if "_inst_" not in p)
print("Semantic label files in train:", len(labels))

# Class shares, semantic labels only
counts = Counter()
for path in labels[:200]:
    values, n = np.unique(np.array(Image.open(path)), return_counts=True)
    for v, c in zip(values, n):
        counts[int(v)] += int(c)
total = sum(counts.values())
print("Class values (semantic labels only):")
for v in sorted(counts):
    print(f"  {v}: {100 * counts[v] / total:.1f}%")

# One distinct colour per class number
colors = np.array([
    [128, 64, 128],   # class 0 - purple
    [244, 35, 232],   # class 1 - pink
    [220, 20, 60],    # class 2 - red
    [0, 0, 142],      # class 3 - dark blue
    [250, 170, 30],   # class 4 - orange
    [70, 70, 70],     # class 5 - grey
    [70, 130, 180],   # class 6 - light blue
], dtype=np.uint8)

random.seed(0)
picks = random.sample(labels, 3)

fig, ax = plt.subplots(3, 2, figsize=(10, 10))
for row, lab_path in enumerate(picks):
    folder = os.path.dirname(lab_path).replace("gtFine", "leftImg8bit")
    stem = os.path.basename(lab_path).split("_")[0]
    img_path = glob.glob(os.path.join(folder, stem + "*"))[0]

    lab = np.array(Image.open(lab_path))
    color = np.zeros((*lab.shape, 3), dtype=np.uint8)   # 255 (ignore) stays black
    for c in range(7):
        color[lab == c] = colors[c]

    ax[row, 0].imshow(Image.open(img_path))
    ax[row, 0].set_title(os.path.basename(img_path))
    ax[row, 1].imshow(color)
    ax[row, 1].set_title("label (coloured by class number)")
    ax[row, 0].axis("off")
    ax[row, 1].axis("off")

fig.legend(handles=[Patch(color=colors[c] / 255, label=f"class {c}") for c in range(7)],
           loc="lower center", ncol=7)
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig("perception/idd_lite_examples.png", dpi=120)
print("Saved perception/idd_lite_examples.png")
plt.show()