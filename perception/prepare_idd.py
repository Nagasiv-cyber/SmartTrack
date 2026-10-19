r"""
Convert full IDD (IDD 20k Part I) outline labels into level3Id label images,
and shrink images so the dataset fits in Google Drive.
Output uses IDD-Lite style names, so the Colab training code can be reused.
Run from C:\carla-project:
  set PYTHONPATH=C:\idd-public-code\helpers
  python perception\prepare_idd.py
"""
import glob
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

from PIL import Image, ImageDraw
from anue_labels import labels

SRC = "data/idd-full/IDD_Segmentation"
DST = "data/idd-small"
WIDTH = 960   # output width in pixels; height keeps the original shape

NAME2LEVEL3 = {l.name: l.level3Id for l in labels}
NAME2LEVEL3["animal"] = 26   # our change: keep animals separate from people


def convert(json_path):
    split, drive = json_path.replace("\\", "/").split("/")[-3:-1]
    stem = os.path.basename(json_path).split("_")[0]
    found = glob.glob(f"{SRC}/leftImg8bit/{split}/{drive}/{stem}_leftImg8bit.*")
    if not found:
        return "missing image"

    with open(json_path) as f:
        ann = json.load(f)
    w, h = ann["imgWidth"], ann["imgHeight"]

    # Start with 255 (= ignore) everywhere, then colour each outline with its class number
    lab = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(lab)
    for obj in ann["objects"]:
        if obj.get("deleted", 0):
            continue
        name = obj["label"]
        if name not in NAME2LEVEL3 and name.endswith("group"):
            name = name[:-5]
        if name not in NAME2LEVEL3:
            continue
        value = NAME2LEVEL3[name]
        poly = [tuple(p) for p in obj["polygon"]]
        if len(poly) < 3 or value < 0 or value > 255:
            continue
        draw.polygon(poly, fill=value)

    new_h = round(h * WIDTH / w)
    lab_dir = f"{DST}/gtFine/{split}/{drive}"
    img_dir = f"{DST}/leftImg8bit/{split}/{drive}"
    os.makedirs(lab_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)
    lab.resize((WIDTH, new_h), Image.Resampling.NEAREST).save(f"{lab_dir}/{stem}_label.png")
    Image.open(found[0]).convert("RGB").resize((WIDTH, new_h), Image.Resampling.BILINEAR) \
        .save(f"{img_dir}/{stem}_image.jpg", quality=90)
    return "ok"


if __name__ == "__main__":
    jsons = sorted(glob.glob(f"{SRC}/gtFine/*/*/*_gtFine_polygons.json"))
    print(len(jsons), "annotation files found")

    # Save the class list for reference (level3Id -> names)
    os.makedirs(DST, exist_ok=True)
    groups = {}
    for name, k in NAME2LEVEL3.items():
        if 0 <= k < 255:
            groups.setdefault(k, []).append(name)
    with open(f"{DST}/classes.txt", "w") as f:
        for k in sorted(groups):
            f.write(f"{k}: {', '.join(groups[k])}\n")
    print("Training classes:", len(groups), "(saved to", DST + "/classes.txt)")

    t0, done, problems = time.time(), 0, 0
    with ProcessPoolExecutor(max_workers=4) as ex:
        for result in ex.map(convert, jsons, chunksize=16):
            done += 1
            problems += result != "ok"
            if done % 500 == 0:
                print(f"{done}/{len(jsons)} done | problems {problems} | {time.time() - t0:.0f} s")
    print(f"Finished: {done} files, {problems} problems, {time.time() - t0:.0f} s")