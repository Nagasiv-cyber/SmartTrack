r"""
Capture RGB + ground-truth segmentation images from CARLA for the domain-gap test.
Run from C:\carla-project with CARLA running:  python sim\capture_camera.py
"""
import os
import queue

import carla

OUT = "experiments/domain_gap"
SPAWNS = [0, 5, 10]


def latest(q):
    item = q.get(timeout=10)
    while not q.empty():
        item = q.get()
    return item


def main():
    client = carla.Client("localhost", 2000)
    client.set_timeout(30.0)
    world = client.get_world()
    print("Map:", world.get_map().name)
    os.makedirs(OUT, exist_ok=True)

    original = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    bp = world.get_blueprint_library()
    cmap = world.get_map()
    spawn_points = cmap.get_spawn_points()
    actors = []
    try:
        ego = world.spawn_actor(bp.find("vehicle.tesla.model3"), spawn_points[SPAWNS[0]])
        actors.append(ego)

        cam_tf = carla.Transform(carla.Location(x=1.5, z=2.4))
        rgb_bp = bp.find("sensor.camera.rgb")
        seg_bp = bp.find("sensor.camera.semantic_segmentation")
        for b in (rgb_bp, seg_bp):
            b.set_attribute("image_size_x", "320")
            b.set_attribute("image_size_y", "224")
            b.set_attribute("fov", "90")
        rgb = world.spawn_actor(rgb_bp, cam_tf, attach_to=ego)
        seg = world.spawn_actor(seg_bp, cam_tf, attach_to=ego)
        actors += [rgb, seg]
        q_rgb, q_seg = queue.Queue(), queue.Queue()
        rgb.listen(q_rgb.put)
        seg.listen(q_seg.put)

        for n, idx in enumerate(SPAWNS):
            start = spawn_points[idx]
            ego.set_transform(start)

            # Put a parked car 15 m ahead and a pedestrian 10 m ahead, off to the side
            wp = cmap.get_waypoint(start.location)
            extras = []
            ahead = wp.next(15.0)
            if ahead:
                tf = ahead[0].transform
                tf.location.z += 0.3
                car = world.try_spawn_actor(bp.find("vehicle.audi.a2"), tf)
                if car:
                    extras.append(car)
            ahead = wp.next(10.0)
            if ahead:
                tf = ahead[0].transform
                right = tf.get_right_vector()
                tf.location += carla.Location(x=right.x * 2.5, y=right.y * 2.5, z=1.0)
                walker = world.try_spawn_actor(bp.filter("walker.pedestrian.*")[0], tf)
                if walker:
                    extras.append(walker)

            for _ in range(30):          # let everything settle
                world.tick()
            img_rgb, img_seg = latest(q_rgb), latest(q_seg)
            img_rgb.save_to_disk(f"{OUT}/view{n}_rgb.png")
            img_seg.save_to_disk(f"{OUT}/view{n}_seg.png", carla.ColorConverter.CityScapesPalette)
            print(f"Saved view {n} (spawn {idx}) with {len(extras)} extra actors")
            for a in extras:
                a.destroy()
    finally:
        for a in reversed(actors):
            if a.type_id.startswith("sensor"):
                a.stop()
            a.destroy()
        world.apply_settings(original)


if __name__ == "__main__":
    main()