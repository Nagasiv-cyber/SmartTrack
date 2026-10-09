\# SmartTrack



Agent-aware traversability and adaptive path planning for lane-free heterogeneous traffic on unstructured Indian roads (based on SIH26037).



\## Status

\- Week 1: CARLA 0.9.16 setup; pure pursuit steering + PI speed control on Town02 (scenario S1 baseline).



\## Run

1\. Start CARLA 0.9.16: `CarlaUE4.exe -quality-level=Low`

2\. `python sim\\week1\_s1\_drive.py --spawn 0 --length 200 --speed 6`

3\. `python sim\\plot\_s1.py`

