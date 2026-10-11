import csv
import matplotlib.pyplot as plt


def load(path):
    t, v, d = [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            t.append(int(row["tick"]) * 0.05)
            v.append(float(row["speed_mps"]))
            d.append(float(row["dist_to_stalled"]))
    return t, v, d


runs = {
    "Blind follow (crashes)": "experiments/s2/s2_follow.csv",
    "Stop-only (gets stuck)": "experiments/s2/s2_stop.csv",
}

fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
for label, path in runs.items():
    t, v, d = load(path)
    ax[0].plot(t, v, label=label)
    ax[1].plot(t, d, label=label)

ax[0].set_title("Speed over time")
ax[0].set_xlabel("time (s)")
ax[0].set_ylabel("m/s")
ax[0].set_xlim(0, 40)
ax[0].legend()

ax[1].axhline(4.5, linestyle="--", color="gray", label="bumpers touching (about 4.5 m)")
ax[1].set_title("Distance to stalled car (centre to centre)")
ax[1].set_xlabel("time (s)")
ax[1].set_ylabel("m")
ax[1].set_xlim(0, 40)
ax[1].set_ylim(0, None)
ax[1].legend()

plt.suptitle("Scenario S2: both baselines fail")
plt.tight_layout()
plt.savefig("experiments/s2/s2_baselines.png", dpi=150)
print("Saved experiments/s2/s2_baselines.png")
plt.show()