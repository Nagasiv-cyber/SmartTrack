# SmartTrack research roadmap

_Updated 29 October 2026. Planned work is not presented as completed._

## Already documented in this repository

- S1: CARLA baseline using pure-pursuit steering and PI speed control, with logged trajectory/speed/steering.
- S2: stopped-vehicle scenario and blind-follow/stop-only comparison.
- S3: pedestrian crossing scenario and 10 paired configurations of blind-follow vs stop-only, with per-run CSV logs.
- Perception: IDD-Lite and full-IDD SegFormer-B0 recorded experiment metrics; two-view CARLA domain-gap demonstration.
- Planner: semantic-cost-map construction using CARLA oracle labels and an **offline** A* route visualization.

See [EVIDENCE.md](EVIDENCE.md) for results, links, and caveats.

## Next milestones (not completed)

1. **Reproducibility and map consistency:** standardize CARLA version/map selection, environmental dependencies, script paths, and logging.
2. **Baseline evaluation:** define scenario success and collision metrics, closest separation, TTC, braking, jerk, planning latency, and consistent results files.
3. **Closed-loop implementation:** connect planning output to a drivable route-following controller; include failure and recovery handling.
4. **Model-in-the-loop evaluation:** replace CARLA oracle labels with learned camera predictions in a controlled experiment, reporting segmentation/domain-shift failures honestly.
5. **Controlled experiments:** development/tuning seeds 0–29; hold out seeds 100–149 until the planned week-11 final freeze. Use reproducible paired scenarios and uncertainty intervals.
6. **Research communication:** document hardware/software, methods and limitations; add a short demo and an updated research summary once the behavior has been recorded and validated.

## Before making this repository public

- Review files and history for private data, credentials, datasets, or large assets that cannot be redistributed.
- Keep raw IDD images and model checkpoints out of git unless licensing and sizes have been checked.
- Verify any command on the machine with CARLA installed before labelling it as tested.
- Record an approximately 40-second demo that shows the *actual* state of the project, including an offline path-planning visualization if closed-loop driving is not ready.
