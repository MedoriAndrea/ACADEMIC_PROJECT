# Comparative Kinematic Analysis: Human Hand vs. Robolimb Prosthesis

Group project (**Group 7**, 4 students) for the **Bioengineering and Biomechanics of Human Movement** course (*Bioingegneria e Biomeccanica del Movimento Umano*), MSc in Biomedical Engineering, Università Campus Bio-Medico di Roma, A.Y. 2025/2026 (May–Jun 2026).

We compared the **index-finger kinematics** of 3 human subjects with those of the commercial **Robolimb** prosthetic hand. Using an RGB camera and coloured markers, we measured the **range of motion (RoM) of the MCP joint**, the **trajectory of the fingertip (TIP)**, and 11 kinematic features in two motor tasks. We then ran an adaptive non-parametric statistical analysis.

---

## Experimental setup
- **Camera:** standard RGB webcam, 640×480 at 30 fps, with intrinsic calibration (`calib_data*.npz`). Subject–camera distance about 29 cm, hand in the frontal plane, diffuse lighting and a uniform background.
- **Markers:** 5 coloured markers on the CMC, MCP, PIP, DIP and TIP of the index finger. They are segmented by colour (YCbCr thresholding) and tracked with a **Kalman filter** for robustness to noise.
- **Tasks:**
  1. **Free flexion–extension** (`LIBERA`): from full extension to active flexion, 25 repetitions per subject.
  2. **Two-finger pinch** (`BIDIGITALE`): grasping a coffee cup (d ≈ 5–6 cm). The constraint imposed by the object changes the motor strategy.
- **Robolimb:** driven with programmed `GRASP` and `REST` commands over **UDP**.

## Acquisition GUI (Python, PyQt6)
`Codice_finale.py` with `gui_finale_prese.ui` is a single application for the whole experiment:
- **Acquisition tab:**
  - human or robot mode, subject, trial and grasp type;
  - camera control and recording;
  - colour thresholding (choice of colour space and per-channel thresholds);
  - marker detection, tracking and labelling.
- **Real-time views:**
  - camera frame and segmentation mask;
  - live MCP, PIP and DIP angles;
  - reconstructed finger skeleton;
  - TIP position and velocity.
- **Communication tab:**
  - UDP IP and port settings;
  - messages associated with each grasp;
  - manual or automatic `REST`/`GRASP` commands sent to the robotic hand.
- **Object detection (optional):** YOLOv8 recognises the object in the frame and automatically chooses the grasp command.
- **Database tab:**
  - automatic organisation of sessions and trials;
  - export to CSV and JSON for each trial (`angles.csv`, `markers_px.csv`, `tip_kinematics.csv`, `events.json`, `config.json`).

## Data processing and analysis (MATLAB)
Run the scripts in this order:
1. `ESTRAZIONE.m` reads every trial from `data/` (Human and Robot, each subject and task) and builds `dataset_biomeccanico_elaborato.mat`.
   - **Local reference frame:** the origin is at the index MCP, the X axis runs from CMC to MCP. The TIP trajectory is **normalised by the subject's index-finger length**, which makes humans and robot comparable.
   - **Filtering:** 2nd-order Butterworth, fc = 5 Hz, at fs = 30 Hz.
   - **Active window:** onset and offset are set by an adaptive threshold at 5% of the trial's maximum velocity. Trials with too few active samples are discarded.
2. `FEAT_EXTRACTION.m` extracts **11 features** per trial and removes outlier trials, meaning those with at least 3 features beyond 1.5×IQR:
   - **Spatial:** MCP RoM, normalised path length, linearity index, bounding-box area.
   - **Temporal and velocity:** peak velocity, movement time, time at the 95% plateau.
   - **Smoothness and shape:** SPARC, velocity-profile efficiency (V_mean/V_max), skewness, FWHM of the velocity bell.
3. `ANALISI_CORRELAZIONI.m` removes **redundant features** by Spearman correlation: if |R| > 0.85 in both conditions, one of the two features is dropped.
4. `ANALISI_STATISTICA.m` / `ANALISI_STAT_COMPATTA.m` apply an **adaptive non-parametric protocol**:
   - Shapiro–Wilk normality test (`swtest.m`);
   - Kruskal–Wallis among the human subjects;
   - if the humans are homogeneous, a pooled **Mann–Whitney U** test humans vs. robot; otherwise **one Mann–Whitney test per subject** against the robot.
   - The p-values are shown as heatmaps.
5. `BOXPLOT_PLOT.m` and `PLOT.m` produce the box plots and the trajectories, absolute (cm) and normalised, for both tasks.

---

## Main results
- **MCP RoM depends on the task:**
  - in the **free** task, the Robolimb differs significantly from every subject (p ≤ 0.001);
  - in the **pinch** task, there is no significant difference for 2 subjects out of 3 (S02 p = 0.753, S03 p = 0.153). The cup forces a stiffer grasp that matches the prosthesis's intrinsic RoM.
- **What matches the human hand:** the prosthesis moves straight to the target (linearity) with an efficient velocity profile.
- **Dynamic limits:** there is a systematic gap in peak velocity, movement time and FWHM, and a drop in **smoothness (SPARC)** in the precision grasp. This points to an intrinsic limitation of rigid actuation, not to an error in the setup.
- **Free task:** humans trace wide, variable arcs, while the Robolimb follows a narrow, rigid arc.

---

## Repository structure
```
├── code/
│   ├── Codice_finale.py, gui_finale_prese.ui   # Acquisition GUI
│   ├── calib_data.npz, calib_data_videoc.npz   # Camera calibration
│   ├── detector.py, coco.yaml                  # YOLO object-detection test
│   ├── Sender.py, Receiver.py                  # UDP communication tests
│   ├── ESTRAZIONE.m … PLOT.m, swtest.m         # MATLAB analysis pipeline
│   ├── *.mat                                   # Intermediate datasets and feature tables
│   └── data/{Human,Robot}/<subject>_<task>/trial_*/   # Raw acquisitions (CSV/JSON)
├── results/*.fig                               # Box plots and TIP trajectories
└── docs/presentation.pptx                      # Final presentation (in Italian)
```

## How to run
- **GUI:** Python 3 with `PyQt6`, `opencv-python`, `numpy`, `filterpy`, `pyqtgraph` and `matplotlib`; `ultralytics` is optional, for YOLO. Run `python Codice_finale.py` from the `code/` folder. The YOLOv8 weights (`yolov8s.pt`) are not included: Ultralytics downloads them automatically.
- **Analysis:** MATLAB with the Statistics and Signal Processing toolboxes. Run the scripts from the `code/` folder in the order above.

---

*Group project developed with fellow students at Università Campus Bio-Medico di Roma. Code comments and the presentation are in Italian.*
