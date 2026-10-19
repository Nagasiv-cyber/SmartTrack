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

## Test 2 - 19 Oct 2026 - S3 pedestrian crossing, 10 random runs (seed 0)

Random: trigger 15-30 m, walk speed 1.0-1.8 m/s, Town02

Blind follow: 4/10 collisions, 8/10 close calls (<3 m), completed runs about 25.2 s

Stop-only: 0/10 collisions, 0/10 close calls, mean 28.3 s

Collisions happen with trigger 19-24 m and slow walkers

## Run 2 - 19 Oct 2026 - Full IDD (Part I), 27 classes (animal separate)

Data: 6517 train / 476 tune (5% of drives, for epoch choice) / 981 val (scored once), 960x544, 512 crops

Model: SegFormer-B0; 20 epochs, batch 8, AdamW 2e-4, cosine, AMP, seed 0; Colab T4, 3.3 min/epoch

Result: VAL mIoU 55.9% (27 classes), 57.6% (official 26 classes); best tune 54.2% at epoch 20

Good: road 93.3, car 85.4, bus 82.5, autorickshaw 77.0

Weak: animal 12.9 (rare class), traffic light 1.9, bicycle 20.2, drivable fallback 60.2

Next: oversample animal images; maybe IDD Part II or SegFormer-B2

