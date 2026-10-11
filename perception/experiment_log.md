\# Experiment log



\## Run 1 - 11 Oct 2026 - IDD-Lite baseline

Model: SegFormer-B0 (nvidia/mit-b0 pretrained encoder)

Data: IDD-Lite, 7 classes, 1403 train / 204 val, resized to 320x224

Training: 30 epochs, batch 16, AdamW lr 2e-4, weight decay 0.01, cosine schedule, seed 0, horizontal flip

Hardware: Google Colab T4 GPU, about 17 s per epoch

Result: best val mIoU 67.2% (epoch 22); plateau from about epoch 14

Note: best epoch chosen on val - optimistic; fix for the paper



\## Test 1 - 11 Oct 2026 - Domain gap (IDD-Lite model on CARLA Town02)

2 views captured (CARLA crashed on the 3rd)

Works: road, parked car, pedestrian, sky, buildings

Fails: both sidewalks predicted as drivable; grass/house partly predicted as vehicle

Conclusion: main planner experiments use CARLA ground-truth segmentation (oracle);

model-in-the-loop runs report this gap honestly

