"""
Scenario S2: a stalled car blocks our lane.
Modes:
  follow : blind road follower, ignores obstacles   -> expected to crash
  stop   : stop-only baseline, brakes and waits     -> expected to get stuck
Run from C:\carla-project with Town02 loaded:
  python sim\s2_stalled.py --mode follow
  python sim\s2_stalled.py --mode stop
"""
import argparse
import csv
import math

import carla

from week1_s1_drive import speed_of, build_route, pure_pursuit_steer


def ahead_of(transform, loc):
    """Where is loc relative to the car? Returns (metres ahead, metres to the side)."""
    yaw = math.radians(transform.rotation.yaw)
    dx = loc.x - transform.location.x
    dy = loc.y - transform.location.y
    forward = math.cos(yaw) * dx + math.sin(yaw) * dy
    side = -math.sin(yaw) * dx + math.cos(yaw) * dy
    return forward, side


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["follow", "stop"], default="follow")
    p.add_argument("--spawn", type=int, default=0)
    p.add_argument("--length", type=float, default=200.0)
    p.add_argument("--speed", type=float, default=6.0)
    p.add_argument("--lookahead", type=float, default=6.0)
    p.add_argument("--obstacle-at", type=float, default=80.0, help="metres along the route")
    p.add_argument("--stop-dist", type=float, default=12.0, help="stop mode: brake if closer than this")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    out = args.out or f"s2_{args.mode}.csv"

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

    actors = []
    collisions = []
    try:
        cmap = world.get_map()
        start = cmap.get_spawn_points()[args.spawn]
        bp_lib = world.get_blueprint_library()

        ego = world.spawn_actor(bp_lib.find("vehicle.tesla.model3"), start)
        actors.append(ego)

        # Place the stalled car on our route, obstacle-at metres ahead.
        route = build_route(cmap, start.location, args.length, step_m=0.5)
        obs_tf = route[min(int(args.obstacle_at / 0.5), len(route) - 1)].transform
        obs_tf.location.z += 0.3
        stalled = world.try_spawn_actor(bp_lib.find("vehicle.audi.a2"), obs_tf)
        if stalled is None:
            print("Could not place the stalled car; try another --obstacle-at value")
            return
        actors.append(stalled)
        stalled.apply_control(carla.VehicleControl(hand_brake=True))

        # Invisible bumper switch: records anything our car touches.
        sensor = world.spawn_actor(bp_lib.find("sensor.other.collision"),
                                   carla.Transform(), attach_to=ego)
        actors.append(sensor)
        sensor.listen(lambda event: collisions.append(event.other_actor.type_id))

        world.tick()
        max_steer = math.radians(ego.get_physics_control().wheels[0].max_steer_angle)
        spectator = world.get_spectator()
        idx, integral = 0, 0.0
        min_dist = float("inf")
        result = "TIMEOUT"
        tick = 0
        max_ticks = int(4 * args.length / args.speed / dt)

        with open(out, "w", newline="") as f:
            log = csv.writer(f)
            log.writerow(["tick", "x", "y", "speed_mps", "steer", "throttle", "brake", "dist_to_stalled"])

            for tick in range(max_ticks):
                tf = ego.get_transform()
                dist = tf.location.distance(stalled.get_location())
                min_dist = min(min_dist, dist)

                if collisions:
                    result = f"COLLISION with {collisions[0]}"
                    break

                while idx < len(route) - 1 and \
                        route[idx].transform.location.distance(tf.location) < args.lookahead:
                    idx += 1
                if idx == len(route) - 1 and route[idx].transform.location.distance(tf.location) < 3.0:
                    result = "FINISHED"
                    break

                steer = pure_pursuit_steer(tf, route[idx].transform.location, 2.9, args.lookahead, max_steer)
                error = args.speed - speed_of(ego)
                integral = max(-10.0, min(10.0, integral + error * dt))
                throttle = max(0.0, min(0.75, 0.3 * error + 0.1 * integral))
                brake = max(0.0, min(1.0, -0.3 * error)) if error < -1.0 else 0.0

                if args.mode == "stop":
                    forward, side = ahead_of(tf, stalled.get_location())
                    if 0 < forward < args.stop_dist and abs(side) < 2.5:
                        throttle, brake, integral = 0.0, 1.0, 0.0

                ego.apply_control(carla.VehicleControl(throttle=throttle, steer=steer, brake=brake))
                spectator.set_transform(carla.Transform(
                    tf.location + carla.Location(z=35), carla.Rotation(pitch=-90)))
                log.writerow([tick, round(tf.location.x, 3), round(tf.location.y, 3),
                              round(speed_of(ego), 3), round(steer, 4), round(throttle, 3),
                              round(brake, 3), round(dist, 3)])
                world.tick()

        if result == "TIMEOUT" and args.mode == "stop":
            result = "STUCK (waited behind the stalled car until time ran out)"
        print(f"Mode: {args.mode} | Result: {result} | Time: {tick * dt:.1f} s | "
              f"Closest centre-to-centre distance: {min_dist:.1f} m")
        print("Log saved to", out)

    finally:
        for a in reversed(actors):
            if a.type_id.startswith("sensor"):
                a.stop()
            a.destroy()
        world.apply_settings(original)


if __name__ == "__main__":
    main()