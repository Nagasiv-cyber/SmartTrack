"""
Week 1 milestone script (scenario S1: narrow road, no lane markings).
Run:   python week1_s1_drive.py --spawn 0 --length 200 --speed 6
"""

import argparse
import csv
import math

import carla


def speed_of(vehicle):
    v = vehicle.get_velocity()
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)  # metres per second


def build_route(carla_map, start_location, length_m, step_m=0.5):
    """Walk along the road from the start point, one waypoint every step_m metres."""
    wp = carla_map.get_waypoint(start_location)
    route = [wp]
    for _ in range(int(length_m / step_m)):
        nxt = route[-1].next(step_m)
        if not nxt:
            break
        route.append(nxt[0])
    return route


def pure_pursuit_steer(transform, target, wheelbase, lookahead, max_steer_rad):
    """Turn the wheels so the car's path arcs through the target point."""
    yaw = math.radians(transform.rotation.yaw)
    dx = target.x - transform.location.x
    dy = target.y - transform.location.y
    local_x = math.cos(-yaw) * dx - math.sin(-yaw) * dy
    local_y = math.sin(-yaw) * dx + math.cos(-yaw) * dy
    alpha = math.atan2(local_y, local_x)
    steer_rad = math.atan2(2.0 * wheelbase * math.sin(alpha), lookahead)
    return max(-1.0, min(1.0, steer_rad / max_steer_rad))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--spawn", type=int, default=0)
    parser.add_argument("--length", type=float, default=300.0)
    parser.add_argument("--speed", type=float, default=8.0)
    parser.add_argument("--lookahead", type=float, default=6.0)
    parser.add_argument("--out", default="s1_run.csv")
    args = parser.parse_args()

    client = carla.Client(args.host, args.port)
    client.set_timeout(30.0)

    maps = client.get_available_maps()
    town07 = [m for m in maps if m.endswith("Town07")]
    world = client.load_world(town07[0]) if town07 else client.get_world()
    print("Map:", world.get_map().name)

    original_settings = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    ego = None
    try:
        carla_map = world.get_map()
        spawn_points = carla_map.get_spawn_points()
        start = spawn_points[args.spawn % len(spawn_points)]

        blueprint = world.get_blueprint_library().find("vehicle.tesla.model3")
        ego = world.spawn_actor(blueprint, start)
        world.tick()

        physics = ego.get_physics_control()
        max_steer_rad = math.radians(physics.wheels[0].max_steer_angle)
        wheelbase = 2.9

        route = build_route(carla_map, start.location, args.length)
        print(f"Route: {len(route)} waypoints, about {2 * len(route)} m")

        spectator = world.get_spectator()
        idx = 0
        integral = 0.0
        max_ticks = int(4 * args.length / max(args.speed, 1.0) / settings.fixed_delta_seconds)

        with open(args.out, "w", newline="") as f:
            log = csv.writer(f)
            log.writerow(["tick", "x", "y", "yaw_deg", "speed_mps", "steer", "throttle", "brake"])

            for tick in range(max_ticks):
                tf = ego.get_transform()

                while idx < len(route) - 1 and \
                        route[idx].transform.location.distance(tf.location) < args.lookahead:
                    idx += 1
                target = route[idx].transform.location

                if idx == len(route) - 1 and target.distance(tf.location) < 3.0:
                    print(f"Route finished at tick {tick} ({tick * settings.fixed_delta_seconds:.1f} s)")
                    break

                steer = pure_pursuit_steer(tf, target, wheelbase, args.lookahead, max_steer_rad)

                error = args.speed - speed_of(ego)
                integral = max(-10.0, min(10.0, integral + error * 0.05))
                throttle = max(0.0, min(0.75, 0.3 * error + 0.1 * integral))
                brake = max(0.0, min(1.0, -0.3 * error)) if error < -1.0 else 0.0

                ego.apply_control(carla.VehicleControl(throttle=throttle, steer=steer, brake=brake))

                spectator.set_transform(carla.Transform(
                    tf.location + carla.Location(z=35), carla.Rotation(pitch=-90)))

                log.writerow([tick, round(tf.location.x, 3), round(tf.location.y, 3),
                              round(tf.rotation.yaw, 2), round(speed_of(ego), 3),
                              round(steer, 4), round(throttle, 3), round(brake, 3)])
                world.tick()
            else:
                print("Stopped: time limit reached before the end of the route")

        print("Log saved to", args.out)

    finally:
        if ego is not None:
            ego.destroy()
        world.apply_settings(original_settings)


if __name__ == "__main__":
    main()