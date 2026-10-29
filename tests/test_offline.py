"""Offline regression checks. These do not start CARLA or control a vehicle."""
import csv
import math
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "sim"
sys.path.insert(0, str(SIM))

# CARLA is intentionally absent from GitHub-hosted CI. The tested pure functions
# only use transform / location attributes and do not require a simulator.
sys.modules.setdefault("carla", types.ModuleType("carla"))
from week1_s1_drive import pure_pursuit_steer  # noqa: E402
from s2_stalled import ahead_of  # noqa: E402


def vec(x, y):
    return types.SimpleNamespace(x=x, y=y)


def transform(x, y, yaw_degrees=0):
    return types.SimpleNamespace(
        location=vec(x, y),
        rotation=types.SimpleNamespace(yaw=yaw_degrees),
    )


class SteeringTests(unittest.TestCase):
    def test_center_target_has_zero_steer(self):
        self.assertAlmostEqual(
            pure_pursuit_steer(transform(0, 0), vec(10, 0), 2.9, 6, math.radians(35)),
            0,
            places=6,
        )

    def test_turn_direction_and_bounds(self):
        left = pure_pursuit_steer(transform(0, 0), vec(10, 3), 2.9, 6, math.radians(35))
        right = pure_pursuit_steer(transform(0, 0), vec(10, -3), 2.9, 6, math.radians(35))
        self.assertGreater(left, 0)
        self.assertLess(right, 0)
        self.assertAlmostEqual(left, -right, places=6)
        self.assertLessEqual(abs(left), 1)

    def test_ahead_of_at_zero_heading(self):
        forward, side = ahead_of(transform(2, 3), vec(12, 5))
        self.assertAlmostEqual(forward, 10)
        self.assertAlmostEqual(side, 2)

    def test_ahead_of_rotated_heading(self):
        forward, side = ahead_of(transform(0, 0, 90), vec(0, 10))
        self.assertAlmostEqual(forward, 10)
        self.assertAlmostEqual(side, 0, places=6)


class CheckedInExperimentTests(unittest.TestCase):
    def test_s3_csv_contains_paired_parameter_sets(self):
        path = ROOT / "experiments" / "s3" / "batch_summary.csv"
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 20)
        follow, stop = {}, {}
        for row in rows:
            target = follow if row["mode"] == "follow" else stop
            self.assertNotIn(row["run"], target)
            target[row["run"]] = row
        self.assertEqual(set(follow), set(stop))
        self.assertEqual(len(follow), 10)
        for key in follow:
            self.assertEqual(follow[key]["trigger_m"], stop[key]["trigger_m"])
            self.assertEqual(follow[key]["walk_mps"], stop[key]["walk_mps"])

        follow_collisions = sum("COLLISION" in row["result"] for row in follow.values())
        stop_collisions = sum("COLLISION" in row["result"] for row in stop.values())
        self.assertEqual((follow_collisions, stop_collisions), (4, 0))

    def test_saved_cost_grid_shape_and_values(self):
        import numpy as np

        grid = np.load(ROOT / "experiments" / "costmap" / "cost.npy", allow_pickle=False)
        self.assertEqual(grid.shape, (400, 400))
        self.assertTrue(np.all(np.isfinite(grid) | np.isinf(grid)))
        self.assertTrue(np.any(np.isfinite(grid)))
        self.assertTrue(np.any(np.isinf(grid)))
        self.assertTrue(np.all(grid[np.isfinite(grid)] >= 1.0))


if __name__ == "__main__":
    unittest.main()
