r"""
Scenario S3: a pedestrian crosses the road in front of the car.
Modes:
  follow : blind road follower   -> expected to hit the pedestrian
  stop   : stop-only baseline     -> brakes hard, waits, then continues
Run from C:\carla-project with Town02 loaded:
  python sim\s3_crossing.py --mode follow
  python sim\s3_crossing.py --mode stop
"""
import argparse
import csv
import math

import carla

from week1_s1_drive import speed_of, build_route, pure_pursuit_steer
from s2_stalled import ahead_of


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["follow", "stop"], default="follow")
    p.add_argument("--spawn", type=int, default=0)
    p.add_argument("--length", type=float, default=150.0)
    p.add_argument("--speed", type=float, default=6.0)
    p.add_argument("--lookahead", type=float, default=6.0)
    p.add_argument("--cross-at", type=float, default=60.0, help="metres along the route")
    p.add_argument("--trigger", type=float, default=25.0, help="pedestrian starts when car is this close")
    p.add_argument("--walk-speed", type=float, default=1.4)
    p.add_argument("--stop-dist", type=float, default=12.0)
    p.add_argument("--out", default=None)
    args = p.parse_args()
    out = args.out or f"s3_{args.mode}.csv"

    client = carla.Client("localhost", 2000)
    client.set_timeout(30.0)
    world = client.get_world()
    print("Map:", world.get_map().name)

    original = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)
    dt = settings.fixed_delta_seconds

    actors, collisions = [], []
    try:
        cmap = world.get_map()
        start = cmap.get_spawn_points()[args.spawn]
        bp_lib = world.get_blueprint_library()
        ego = world.spawn_actor(bp_lib.find("vehicle.tesla.model3"), start)
        actors.append(ego)

        # Place the pedestrian 4 m to the right of our lane, cross-at metres ahead
        route = build_route(cmap, start.location, args.length, step_m=0.5)
        cross_tf = route[min(int(args.cross_at / 0.5), len(route) - 1)].transform
        right = cross_tf.get_right_vector()
        walker_tf = carla.Transform(
            cross_tf.location + carla.Location(x=right.x * 4.0, y=right.y * 4.0, z=1.0),
            cross_tf.rotation)
        walker = world.try_spawn_actor(bp_lib.filter("walker.pedestrian.*")[0], walker_tf)
        if walker is None:
            print("Could not place the pedestrian; try another --cross-at value")
            return
        actors.append(walker)
        cross_dir = carla.Vector3D(x=-right.x, y=-right.y, z=0.0)   # walk right to left

        sensor = world.spawn_actor(bp_lib.find("sensor.other.collision"),
                                   carla.Transform(), attach_to=ego)
        actors.append(sensor)
        sensor.listen(lambda event: collisions.append(event.other_actor.type_id))

        world.tick()
        max_steer = math.radians(ego.get_physics_control().wheels[0].max_steer_angle)
        spectator = world.get_spectator()
        idx, integral, walking = 0, 0.0, False
        min_dist = float("inf")
        result, tick = "TIMEOUT", 0
        max_ticks = int(4 * args.length / args.speed / dt)

        with open(out, "w", newline="") as f:
            log = csv.writer(f)
            log.writerow(["tick", "x", "y", "speed_mps", "steer", "throttle",
                          "brake", "dist_to_pedestrian", "walking"])

            for tick in range(max_ticks):
                tf = ego.get_transform()
                dist = tf.location.distance(walker.get_location())
                min_dist = min(min_dist, dist)

                # Pedestrian steps out when the car gets close
                if not walking and dist < args.trigger:
                    walker.apply_control(carla.WalkerControl(direction=cross_dir,
                                                             speed=args.walk_speed))
                    walking = True

                if collisions:
                    result = f"COLLISION with {collisions[0]}"
                    break

                while idx < len(route) - 1 and \
                        route[idx].transform.location.distance(tf.location) < args.lookahead:
                    idx += 1
                if idx == len(route) - 1 and route[idx].transform.location.distance(tf.location) < 3.0:
                    result = "FINISHED"
                    break

                steer = pure_pursuit_steer(tf, route[idx].transform.location, 2.9,
                                           args.lookahead, max_steer)
                error = args.speed - speed_of(ego)
                integral = max(-10.0, min(10.0, integral + error * dt))
                throttle = max(0.0, min(0.75, 0.3 * error + 0.1 * integral))
                brake = max(0.0, min(1.0, -0.3 * error)) if error < -1.0 else 0.0

                if args.mode == "stop":
                    forward, side = ahead_of(tf, walker.get_location())
                    if 0 < forward < args.stop_dist and abs(side) < 2.5:
                        throttle, brake, integral = 0.0, 1.0, 0.0

                ego.apply_control(carla.VehicleControl(throttle=throttle, steer=steer, brake=brake))

                # Chase camera: 8 m behind, 5 m up
                back = tf.get_forward_vector()
                spectator.set_transform(carla.Transform(
                    tf.location + carla.Location(x=-8 * back.x, y=-8 * back.y, z=5),
                    carla.Rotation(pitch=-15, yaw=tf.rotation.yaw)))

                log.writerow([tick, round(tf.location.x, 3), round(tf.location.y, 3),
                              round(speed_of(ego), 3), round(steer, 4), round(throttle, 3),
                              round(brake, 3), round(dist, 3), int(walking)])
                world.tick()

        print(f"Mode: {args.mode} | Result: {result} | Time: {tick * dt:.1f} s | "
              f"Closest centre-to-centre distance to pedestrian: {min_dist:.1f} m")
        print("Log saved to", out)

    finally:
        for a in reversed(actors):
            if a.type_id.startswith("sensor"):
                a.stop()
            a.destroy()
        world.apply_settings(original)


if __name__ == "__main__":
    main()