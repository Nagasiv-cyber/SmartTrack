# SmartTrack: Research Evidence (as of 29 October 2026)

This page separates **artifacts already checked into the repository** from plans and claims that still require validation. The latest experimental commits currently visible are from 19 October 2026.

## Experimental evidence index

| Component | Checked-in evidence | What the evidence supports |
| --- | --- | --- |
| S1 baseline driving | [S1 trajectory/control plot](../experiments/week1/s1_run.png), [time-series CSV](../experiments/week1/s1_run.csv), [controller source](../sim/week1_s1_drive.py) | A CARLA route-following baseline using pure-pursuit steering and PI speed control was implemented and logged. |
| S2 stalled vehicle | [Comparison plot](../experiments/s2/s2_baselines.png), [blind-follow log](../experiments/s2/s2_follow.csv), [stop-only log](../experiments/s2/s2_stop.csv), [scenario source](../sim/s2_stalled.py) | An illustrative baseline failure case: obstacle-ignorant following can collide; stop-only avoidance can get stuck behind a static obstacle. Not a multi-seed statistical result. |
| S3 pedestrian crossing | [Batch summary CSV](../experiments/s3/batch_summary.csv), [per-run logs](../experiments/s3/batch/), [batch script](../sim/batch_s3.py) | A small paired comparison of blind-follow and stop-only behavior under 10 generated crossing configurations. |
| IDD-Lite semantic segmentation | [Experiment log](../perception/experiment_log.md), [dataset example visualization](../perception/idd_lite_examples.png) | A reported SegFormer-B0 7-class validation mIoU of 67.2%. Dataset examples are not prediction-quality validation. |
| Full IDD semantic segmentation | [Experiment log](../perception/experiment_log.md), [conversion/preparation code](../perception/prepare_idd.py) | A reported SegFormer-B0 27-class validation mIoU of 55.9%, measured on a separate validation split. Training checkpoints and a full reproducibility package are not yet in this repository. |
| CARLA-to-IDD domain gap | [Qualitative comparison](../experiments/domain_gap/domain_gap.png), [RGB/segmentation captures](../experiments/domain_gap/), [inference script](../perception/run_on_carla.py) | Two saved CARLA camera views illustrate incorrect sidewalk predictions and other semantic confusion by the IDD-Lite model. This is qualitative evidence, not a quantified cross-domain benchmark. |
| BEV traversability cost map | [Cost-map visualization](../experiments/costmap/bev_costmap.png), [saved numerical map](../experiments/costmap/cost.npy), [construction script](../sim/bev_costmap.py) | A cost map was generated from **CARLA ground-truth semantic segmentation** (oracle labels), not the learned perception model. |
| A* path search | [Offline planned-path visualization](../experiments/costmap/astar_path.png), [planner code](../planner/astar_costmap.py) | An offline grid-based A* path can be planned on the saved cost map around a stalled car. Closed-loop vehicle execution of this route has **not** been demonstrated here. |

## S3 recorded comparison (19 October 2026)

Source: [experiments/s3/batch_summary.csv](../experiments/s3/batch_summary.csv) and [perception/experiment_log.md](../perception/experiment_log.md).

The batch generator uses seed **0** to generate 10 sets of pedestrian crossing parameters (trigger distance and walking speed), running both methods on the same parameter sets. The code does **not** establish 10 independent CARLA world seeds.

| Metric | Blind follow | Stop only |
| --- | ---: | ---: |
| Recorded crossing configurations | 10 | 10 |
| Runs with recorded collision | 4/10 | 0/10 |
| Close approaches: closest centre-to-centre distance < 3 m | 8/10 | 0/10 |
| Mean recorded time across all 10 runs | 19.2 s | 28.3 s |

**Interpretation:** Stop-only avoided recorded collisions in this small test, but is slower and cannot maneuver around a permanently stalled vehicle (S2). Blind-follow trial duration includes early-terminated collision runs, so comparing the above mean times does not measure a fair completion-speed tradeoff. Ten configurations are not enough to establish a general collision probability.

## Reported perception results

| Training run | Dataset | Classes | Split and scoring | Result |
| --- | --- | ---: | --- | --- |
| Run 1 (11 Oct) | IDD-Lite | 7 | Best epoch selected using validation (204 val images) | **67.2% validation mIoU** |
| Run 2 (19 Oct) | IDD Part I | 27 | 6,517 train / 476 tune / 981 validation; best epoch chosen on tune set | **55.9% validation mIoU** (57.6% under official 26-class grouping) |

Run 1's best-on-validation score should be treated as optimistic for research-paper reporting. Run 2 records stronger category-specific scores for road (93.3) and car (85.4), but weaker results for animal (12.9) and traffic light (1.9). These values are percentages reported in the experiment log and are not end-to-end driving metrics.

**Caution:** The two mIoU numbers use different datasets, labels, and evaluation setups; they must **not** be treated as a direct accuracy regression.

## Evidence gallery

### S1 route following
![CARLA S1 baseline trajectory, speed, and steering](../experiments/week1/s1_run.png)

### S2 baseline comparison
![S2 stalled vehicle: blind follow versus stop only](../experiments/s2/s2_baselines.png)

### CARLA-to-IDD domain gap
![CARLA RGB images, oracle segmentation, and learned IDD-Lite predictions](../experiments/domain_gap/domain_gap.png)

### Cost map from oracle labels
![CARLA BEV semantic segmentation and numerical traversability cost map](../experiments/costmap/bev_costmap.png)

### Offline A* plan
![A-star path over a cost map around a stalled car](../experiments/costmap/astar_path.png)

## Critical limitations and unfinished validation

- **Oracle versus learned labels:** The saved BEV cost-map demonstration relies on CARLA's perfect segmentation labels. It does not yet prove robustness with noisy real-world camera predictions.
- **Not yet a closed-loop A* policy:** The A* script plans offline on a recorded map. The repository does not show the vehicle following that planned path while reacting to moving agents.
- **Small scenario sample:** The S3 batch contains 10 paired crossing configurations only. No independent held-out evaluation or uncertainty intervals are documented yet.
- **Incomplete training reproducibility:** IDD-Lite/full IDD training logs are recorded, but pretrained/fine-tuned checkpoints and complete training notebooks/scripts are not currently tracked.
- **Domain shift:** Sidewalk pixels in the two recorded CARLA views were incorrectly classified as drivable by the IDD-Lite model. This is a key risk that must be addressed before model-in-the-loop planning.
- **Environment differences:** Scripts currently make different map assumptions. The S1 script may load Town07 automatically, while S2/S3 scripts operate on the currently loaded map and were documented using Town02. Check the actual map before replicating results.
- **No recorded final evaluation:** Cross-scenario collision-free completion, minimum gap, time-to-collision, braking, jerk, and planning latency have not yet been reported here using a unified reproducible evaluation runner.

The next technical milestones are tracked in [ROADMAP.md](ROADMAP.md).
