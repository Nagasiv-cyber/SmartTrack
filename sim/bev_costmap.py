r"""
Planner step 1: see the world as a cost map.
A perfect segmentation camera 40 m above the car looks straight down (bird's-eye view).
Each pixel's CARLA class becomes a driving cost.
Run from C:\carla-project with Town02 loaded:  python sim\bev_costmap.py
"""
import math
import os
import queue

import carla
import matplotlib.pyplot as plt
import numpy as np

from week1_s1_drive import build_route

OUT = "experiments/costmap"
SIZE, FOV, HEIGHT, AHEAD = 400, 40.0, 40.0, 12.0   # pixels, degrees, metres, metres
M_PER_PX = 2 * HEIGHT * math.tan(math.radians(FOV / 2)) / SIZE

# CARLA semantic tag -> driving cost. Anything not listed is forbidden (infinite cost).
COST = {1: 1.0, 24: 1.0,     # road, road line: cheap
        10: 5.0, 25: 5.0,     # terrain, ground: drivable fallback (soft)
        2: 50.0}              # sidewalk: very costly

TAG_NAMES = {0: "unlabeled", 1: "road", 2: "sidewalk", 3: "building", 4: "wall", 5: "fence",
             6: "pole", 7: "traffic light", 8: "traffic sign", 9: "vegetation", 10: "terrain",
             11: "sky", 12: "pedestrian", 13: "rider", 14: "car", 15: "truck", 16: "bus",
             17: "train", 18: "motorcycle", 19: "bicycle", 20: "static", 21: "dynamic",
             22: "other", 23: "water", 24: "road line", 25: "ground", 26: "bridge",
             27: "rail track", 28: "guard rail"}


def main():
    client = carla.Client("localhost", 2000)
    client.set_timeout(30.0)
    world = client.get_world()
    print("Map:", world.get_map().name, "| metres per pixel:", round(M_PER_PX, 3))
    os.makedirs(OUT, exist_ok=True)

    original = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    bp = world.get_blueprint_library()
    cmap = world.get_map()
    actors = []
    try:
        start = cmap.get_spawn_points()[0]
        ego = world.spawn_actor(bp.find("vehicle.tesla.model3"), start)
        actors.append(ego)

        # Stalled car 20 m ahead in our lane (same idea as S2)
        route = build_route(cmap, start.location, 40, step_m=0.5)
        tf = route[40].transform
        tf.location.z += 0.3
        stalled = world.try_spawn_actor(bp.find("vehicle.audi.a2"), tf)
        if stalled:
            actors.append(stalled)

        # Downward-looking perfect segmentation camera, centred 12 m ahead of the car
        cam_bp = bp.find("sensor.camera.semantic_segmentation")
        cam_bp.set_attribute("image_size_x", str(SIZE))
        cam_bp.set_attribute("image_size_y", str(SIZE))
        cam_bp.set_attribute("fov", str(FOV))
        cam_tf = carla.Transform(carla.Location(x=AHEAD, z=HEIGHT), carla.Rotation(pitch=-90))
        cam = world.spawn_actor(cam_bp, cam_tf, attach_to=ego)
        actors.append(cam)
        q = queue.Queue()
        cam.listen(q.put)

        for _ in range(30):
            world.tick()
        img = q.get(timeout=10)
        while not q.empty():
            img = q.get()

        # The class tag of each pixel is stored in the red channel (index 2 of BGRA)
        tags = np.frombuffer(img.raw_data, dtype=np.uint8).reshape(SIZE, SIZE, 4)[:, :, 2].copy()
        cost = np.full(tags.shape, np.inf)
        for tag, c in COST.items():
            cost[tags == tag] = c
        np.save(f"{OUT}/cost.npy", cost)

        print("What the camera sees (class: share of pixels):")
        values, counts = np.unique(tags, return_counts=True)
        for v, n in zip(values, counts):
            label = COST.get(int(v), "forbidden")
            print(f"  {int(v):2d} {TAG_NAMES.get(int(v), '?'):13s} {100 * n / tags.size:5.1f}%  cost {label}")

        # Coloured version for the picture
        img.convert(carla.ColorConverter.CityScapesPalette)
        colour = np.frombuffer(img.raw_data, dtype=np.uint8).reshape(SIZE, SIZE, 4)[:, :, 2::-1]

        ego_row = SIZE / 2 + AHEAD / M_PER_PX
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))
        ax[0].imshow(colour)
        ax[0].set_title("Bird's-eye view: CARLA perfect labels")
        shown = np.where(np.isinf(cost), np.nan, cost)
        cm = plt.get_cmap("viridis").copy()
        cm.set_bad("black")
        im = ax[1].imshow(shown, cmap=cm)
        ax[1].set_title("Cost map (black = forbidden)")
        fig.colorbar(im, ax=ax[1], fraction=0.046)
        for a in ax:
            a.plot(SIZE / 2, ego_row, "r^", markersize=12)
            a.axis("off")
        plt.tight_layout()
        plt.savefig(f"{OUT}/bev_costmap.png", dpi=110)
        print("Saved", f"{OUT}/bev_costmap.png")
        plt.show()
    finally:
        for a in reversed(actors):
            if a.type_id.startswith("sensor"):
                a.stop()
            a.destroy()
        world.apply_settings(original)


if __name__ == "__main__":
    main()