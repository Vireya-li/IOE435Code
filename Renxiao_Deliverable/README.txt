IOE 435 Final Project — Group 11 (K-Grams Fair)
Technical Lead: Renxiao Li
================================================

FOLDER STRUCTURE
----------------
Renxiao_Deliverable/
├── Code/
│   ├── StepViz.py          — Real-time step visualization GUI (kid-friendly)
│   ├── analyze_gait_data.py — Offline analysis: reads CSVs, generates figures
│   ├── UDPHandler.py        — UDP receiver for IMU data (course-provided)
│   ├── DataUnpacker.py      — Binary packet parser (course-provided)
│   └── DataLogger.py        — CSV data logger (course-provided)
├── Data/
│   ├── *_20Ft_Pause_T1.csv      — Walking with pause, trial 1
│   ├── *_20Ft_Pause_T2.csv      — Walking with pause, trial 2
│   ├── *_20ft_Skipping_T1.csv   — Skipping, trial 1
│   ├── *_20ft_HighKnees_T1.csv  — High knees, trial 1
│   └── *_20ft_HighKnees_T2.csv  — High knees, trial 2
├── Figures/
│   ├── fig1_walking_steps.png       — Walking waveform + step markers
│   ├── fig2_activity_comparison.png — Walking vs Skipping vs High Knees
│   ├── fig3_zoomed_steps.png        — Zoomed in with Step 1,2,3,4 labels
│   ├── fig4_accl_vs_gyro.png       — Accelerometer vs Gyroscope comparison
│   └── fig5_repeatability.png       — Same movement twice (repeatability)
└── README.txt (this file)


HOW TO RUN
----------
Prerequisites:
    pip install PyQt6 pyqtgraph numpy pandas scipy matplotlib

1) Real-time GUI (with IMU sensor connected via WiFi):
    cd Code
    python StepViz.py

2) Real-time GUI (demo mode, no hardware needed):
    cd Code
    python StepViz.py --demo

3) Regenerate all figures from CSV data:
    cd Code
    python analyze_gait_data.py
    (outputs to ../Figures/)


SENSOR SETUP
------------
- Sensor: ICM-20948 IMU on Raspberry Pi Pico W
- Placement: Ankle (lateral side), secured with Velcro strap
- Communication: WiFi UDP, port 64346, ~100 Hz sampling rate
- Data fields: timestamp, 3-axis accelerometer (g), 3-axis gyroscope (deg/s),
  3-axis magnetometer (uT), temperature (C)


STEP DETECTION METHOD
---------------------
- Signal: Gyroscope Z-axis angular velocity
- Method: Peak detection on |gyro_z|
- Threshold: 60-120 deg/s (adjustable per activity)
- Cooldown: 350 ms minimum between steps (prevents double-counting)
- Implementation: scipy.signal.find_peaks (offline), custom detector (real-time)


DATA COLLECTION
---------------
- Date: March 31, 2026 (in-class Workshop 1)
- Location: University of Michigan
- Activities: Walking 20ft with pause, Skipping 20ft, High Knees 20ft
- Each activity recorded 1-2 trials
- Sensor mounted on ankle
