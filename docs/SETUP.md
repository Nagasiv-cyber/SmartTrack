# SmartTrack setup and reproduction

These instructions document the existing scripts and have **not** been validated in a new clean environment.

## Requirements

- Windows with CARLA simulator 0.9.16 installed separately
- A Python interpreter compatible with the CARLA 0.9.16 Python API
- Simulator client library installed in the **same Python environment** used to run the scripts
- Use the project root as the working directory

## Existing virtual environment (Windows Command Prompt)

```cmd
cd /d C:\carla-project
carla-env\Scripts\activate
python --version
python -m pip install -r requirements.txt
python -c "import numpy, scipy, matplotlib; print('Offline dependencies available')"
python -c "import carla; print('CARLA Python API available')"
```

If the CARLA import fails, install the CARLA **Python client API** compatible with your simulator and interpreter before running CARLA-dependent scripts. The zero-byte `CarlaUE4.exe` that used to appear in this repository was not the simulator. Run the simulator executable from your separate CARLA installation.

For perception inference, the existing `perception/run_on_carla.py` additionally requires `torch`, `transformers`, and a locally stored, compatible `perception/segformer_b0_iddlite` checkpoint. The checkpoint is **not** tracked.

## Running an existing offline planner demonstration

The repository already includes `experiments/costmap/cost.npy`, an example cost map. From the project root:

```cmd
python planner\astar_costmap.py
```

This reads the saved grid and writes `experiments/costmap/astar_path.png`. Running the command can overwrite the checked-in visualization; make a copy before regenerating.

## Running simulator examples

Start your local CARLA 0.9.16 installation. For the historical S2/S3 results, load **Town02** first. Verify the map before each run, since legacy scripts make different map assumptions.

```cmd
python sim\s2_stalled.py --mode follow --out experiments\s2\local_follow.csv
python sim\s2_stalled.py --mode stop --out experiments\s2\local_stop.csv
python sim\s3_crossing.py --mode stop --out experiments\s3\local_stop.csv
python sim\bev_costmap.py
```

The cost-map script uses CARLA oracle segmentation, not SegFormer predictions. The A* planner searches this cost map **offline** and is not connected to the car's steering control.

## Reproduction limits

- There is no packaged end-to-end training workflow for the reported IDD metrics yet.
- Test and tuning seeds must remain separate from held-out final evaluation seeds.
- Current CARLA scenarios are prototypes and should not be interpreted as deployment safety evidence.
- No full clean-environment reproduction or CARLA smoke test was performed as part of the documentation update.
