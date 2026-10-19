r"""
Planner step 2 (offline): find the cheapest path on the saved cost map using A*.
Run from C:\carla-project (CARLA not needed):  python planner\astar_costmap.py
"""
import heapq
import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import distance_transform_edt

M_PER_PX, SIZE, AHEAD = 0.073, 400, 12.0   # must match bev_costmap.py
CAR_HALF_WIDTH = 1.1   # metres
MARGIN = 0.5           # extra safety gap, metres
SOFT = 1.5             # beyond the margin, cost rises gently over this distance (metres)

cost = np.load("experiments/costmap/cost.npy")
ego_r, ego_c = int(SIZE / 2 + AHEAD / M_PER_PX), SIZE // 2

# 1. Our own car is not an obstacle: clear its footprint (about 5.0 m x 2.4 m)
hl, hw = int(2.5 / M_PER_PX), int(1.2 / M_PER_PX)
cost[ego_r - hl:ego_r + hl, ego_c - hw:ego_c + hw] = 1.0

# 2. Safety margin: keep the car's centre away from anything forbidden
blocked = np.isinf(cost)
dist_m = distance_transform_edt(~blocked) * M_PER_PX   # metres to the nearest forbidden cell
hard = CAR_HALF_WIDTH + MARGIN
plan = cost.copy()
plan[dist_m < hard] = np.inf
near = (dist_m >= hard) & (dist_m < hard + SOFT)
plan[near] += 10.0 * (1 - (dist_m[near] - hard) / SOFT)   # closer = costlier

# 3. A*: from our car to the top edge of the map, moving to any of 8 neighbours
moves = [(-1, 0, 1.0), (-1, -1, 1.414), (-1, 1, 1.414), (0, -1, 1.0),
         (0, 1, 1.0), (1, 0, 1.0), (1, -1, 1.414), (1, 1, 1.414)]
start = (ego_r, ego_c)
best, parent = {start: 0.0}, {start: None}
queue = [(float(ego_r), 0.0, start)]   # (estimate, cost so far, cell)
goal = None
while queue:
    _, g, (r, c) = heapq.heappop(queue)
    if g > best.get((r, c), math.inf):
        continue
    if r == 0:
        goal = (r, c)
        break
    for dr, dc, step in moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE and not np.isinf(plan[nr, nc]):
            ng = g + step * plan[nr, nc]
            if ng < best.get((nr, nc), math.inf):
                best[(nr, nc)] = ng
                parent[(nr, nc)] = (r, c)
                heapq.heappush(queue, (ng + nr, ng, (nr, nc)))   # estimate = cost so far + rows left

if goal is None:
    print("No path found - everything ahead is blocked")
    raise SystemExit

path = []
cell = goal
while cell is not None:
    path.append(cell)
    cell = parent[cell]
path.reverse()
rows, cols = np.array(path).T

length = sum(math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)) * M_PER_PX
on_sidewalk = np.mean(cost[rows, cols] == 50.0) * 100
print(f"Path found: {length:.1f} m long, {on_sidewalk:.0f}% of it on sidewalk")
print(f"Closest approach to anything forbidden: {dist_m[rows, cols].min():.2f} m (car centre)")

shown = np.where(np.isinf(plan), np.nan, plan)
cm = plt.get_cmap("viridis").copy()
cm.set_bad("black")
plt.figure(figsize=(6, 6))
plt.imshow(shown, cmap=cm)
plt.plot(cols, rows, "r-", linewidth=2, label="planned path")
plt.plot(ego_c, ego_r, "r^", markersize=12)
plt.title("A* path around the stalled car (black = forbidden incl. safety margin)")
plt.legend(loc="lower left")
plt.axis("off")
plt.tight_layout()
plt.savefig("experiments/costmap/astar_path.png", dpi=110)
print("Saved experiments/costmap/astar_path.png")
plt.show()