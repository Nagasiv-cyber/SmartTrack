r"""
Run scenario S3 many times with random variation and summarise the results.
Run from C:\carla-project with CARLA running and Town02 loaded:
  python sim\batch_s3.py --runs 10
"""
import argparse
import csv
import os
import random
import re
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument("--runs", type=int, default=10)
p.add_argument("--seed", type=int, default=0)
args = p.parse_args()

random.seed(args.seed)
os.makedirs("experiments/s3/batch", exist_ok=True)
pattern = re.compile(r"Result: (.*?) \| Time: ([\d.]+) s \| Closest.*?: ([\d.]+) m")
rows = []

for i in range(args.runs):
    trigger = round(random.uniform(15, 30), 1)
    walk = round(random.uniform(1.0, 1.8), 2)
    for mode in ["follow", "stop"]:
        out = f"experiments/s3/batch/run{i:02d}_{mode}.csv"
        cmd = [sys.executable, "sim/s3_crossing.py", "--mode", mode,
               "--trigger", str(trigger), "--walk-speed", str(walk), "--out", out]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"run {i} {mode} failed (exit {proc.returncode}):\n{proc.stderr}\n{proc.stdout}")
        m = pattern.search(proc.stdout)
        if not m:
            raise RuntimeError(f"run {i} {mode}: could not parse result:\n{proc.stdout}\n{proc.stderr}")
        result, time_s, dist = m.group(1), float(m.group(2)), float(m.group(3))
        rows.append([i, mode, trigger, walk, result, time_s, dist])
        print(f"run {i:2d} | {mode:6s} | trigger {trigger:4.1f} m | walk {walk:.2f} m/s | "
              f"{result:30s} | {time_s:5.1f} s | closest {dist:.1f} m")

with open("experiments/s3/batch_summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["run", "mode", "trigger_m", "walk_mps", "result", "time_s", "closest_m"])
    w.writerows(rows)

print("\nSummary (close call = closest centre-to-centre distance under 3 m)")
for mode in ["follow", "stop"]:
    r = [x for x in rows if x[1] == mode]
    if not r:
        continue
    crashes = sum("COLLISION" in x[4] for x in r)
    close = sum(x[6] < 3.0 for x in r)
    mean_t = sum(x[5] for x in r) / len(r)
    print(f"  {mode:6s}: {crashes}/{len(r)} collisions | {close}/{len(r)} close calls | "
          f"mean time {mean_t:.1f} s")
print("Saved experiments/s3/batch_summary.csv")