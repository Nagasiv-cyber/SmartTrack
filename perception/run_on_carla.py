import glob

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import SegformerForSemanticSegmentation

model = SegformerForSemanticSegmentation.from_pretrained("perception/segformer_b0_iddlite").eval()
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
colors = np.array([[128, 64, 128], [244, 35, 232], [220, 20, 60], [0, 0, 142],
                   [250, 170, 30], [70, 70, 70], [70, 130, 180]], dtype=np.uint8)

rgbs = sorted(glob.glob("experiments/domain_gap/*_rgb.png"))
fig, ax = plt.subplots(len(rgbs), 3, figsize=(13, 3.4 * len(rgbs)), squeeze=False)
for row, path in enumerate(rgbs):
    photo = Image.open(path).convert("RGB").resize((320, 224), Image.Resampling.BILINEAR)
    x = (np.asarray(photo, dtype=np.float32) / 255.0 - MEAN) / STD
    x = torch.from_numpy(np.ascontiguousarray(x.transpose(2, 0, 1)))[None]
    with torch.no_grad():
        logits = model(pixel_values=x).logits
        pred = F.interpolate(logits, size=(224, 320), mode="bilinear",
                             align_corners=False).argmax(1)[0].numpy()
    color = np.zeros((224, 320, 3), dtype=np.uint8)
    for c in range(7):
        color[pred == c] = colors[c]
    truth = Image.open(path.replace("_rgb", "_seg")).convert("RGB").resize((320, 224))
    for col, (pic, title) in enumerate([(photo, "CARLA camera"),
                                        (truth, "CARLA ground truth (CARLA colours)"),
                                        (color, "IDD-Lite model prediction")]):
        ax[row, col].imshow(pic)
        ax[row, col].set_title(title)
        ax[row, col].axis("off")
plt.tight_layout()
plt.savefig("experiments/domain_gap/domain_gap.png", dpi=120)
print("Saved experiments/domain_gap/domain_gap.png")
plt.show()