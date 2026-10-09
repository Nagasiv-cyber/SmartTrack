import csv
import math
import matplotlib.pyplot as plt

ticks, xs, ys, speeds, steers = [], [], [], [], []
with open("s1_run.csv") as f:
    for row in csv.DictReader(f):
        ticks.append(int(row["tick"]) * 0.05)   # tick number -> seconds
        xs.append(float(row["x"]))
        ys.append(float(row["y"]))
        speeds.append(float(row["speed_mps"]))
        steers.append(float(row["steer"]))

# Distance actually driven = sum of small steps between logged points
dist = sum(math.dist((xs[i], ys[i]), (xs[i + 1], ys[i + 1])) for i in range(len(xs) - 1))
print(f"Duration: {ticks[-1]:.1f} s | Distance: {dist:.1f} m | "
      f"Mean speed: {sum(speeds) / len(speeds):.2f} m/s | Max |steer|: {max(abs(s) for s in steers):.2f}")

fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))

ax[0].plot(xs, ys, linewidth=2)
ax[0].plot(xs[0], ys[0], "go", label="start")
ax[0].plot(xs[-1], ys[-1], "rs", label="end")
ax[0].set_aspect("equal")
ax[0].invert_yaxis()   # CARLA's y axis points the other way from a normal graph
ax[0].set_title("Path seen from above (m)")
ax[0].legend()

ax[1].plot(ticks, speeds)
ax[1].axhline(6, linestyle="--", color="gray", label="target 6 m/s")
ax[1].set_title("Speed over time")
ax[1].set_xlabel("time (s)")
ax[1].set_ylabel("m/s")
ax[1].legend()

ax[2].plot(ticks, steers)
ax[2].axhline(0, color="gray", linewidth=0.8)
ax[2].set_title("Steering over time (-1 left, +1 right)")
ax[2].set_xlabel("time (s)")

plt.tight_layout()
plt.savefig("s1_run.png", dpi=150)
print("Saved s1_run.png")
plt.show()