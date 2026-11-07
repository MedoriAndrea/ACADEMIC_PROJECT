# Real-Time Movement Recognition from Smartphone Inertial Signals (MATLAB/Simulink)

Group project (**Group 3**) for the **Automation** course, MSc in Biomedical Engineering, Università Campus Bio-Medico di Roma (Dec 2025 – Feb 2026).

The system recognises **two dance steps** (`passo1`, `passo2`) from the **accelerometer and gyroscope of a smartphone**, and also detects when the person is standing still (`fermo`). The phone streams its sensors to **Simulink**. The full pipeline (filtering → event windowing → feature extraction → PCA → classifier) was first developed offline in MATLAB and then rebuilt to run **online**, sample by sample. The model shows the recognised movement live as an image.

---

## Pipeline

```
Smartphone IMU (acc + gyro, 200 Hz) ──► Simulink (Android sensor blocks)
        │
        ▼
1. Acquisition ─► 2. Filtering + windowing ─► 3. Feature extraction (162)
                                                     │
                       6. Online Simulink model ◄─ 5. Classifiers ◄─ 4. PCA (43 PCs, 95% variance)
```

The folders are numbered in pipeline order.

### 1. Signal acquisition (`1_acquisizione_segnale/`)
- `Circuito_Simulink_acquisizione.slx`: Simulink model with the **Android Accelerometer and Gyroscope blocks**. The phone is connected through ADB over Wi-Fi (`Script_wifi.m`), and the 6 signals (acc x/y/z, gyro x/y/z) are logged to the workspace.
- `creazione_dataset.m`: adds each recording, with its label and subject ID, to `dataset.mat`. There are **100 recordings** from **9 participants**.

### 2. Filtering and event windowing (`2_filtraggio_finestratura/`)
- **DC removal:** the mean of each channel is subtracted, which also removes gravity.
- **Band-pass Butterworth filter:** 2nd order, 0.021–25 Hz at Fs = 200 Hz, applied with zero-phase `filtfilt`. The low cut-off was chosen as the one that **maximised the average SNR** over the whole dataset.
- **PCA on the 6 channels:** used to choose the dominant axis for event detection, which turned out to be acc x.
- **Threshold-based windowing** (`detect_event_window.m`): when |acc x| > 1.7, a window is cut from 200 samples before the trigger to 570 after it. Each repetition of a step becomes one sample, for **1,000 windows** in total (`dataset_completo.mat`).

### 3. Feature extraction (`3_feature_extraction/`)
**162 features** per window:
- **Time domain**, per channel: mean, median, variance, standard deviation, max, min, peak-to-peak, energy, RMS, crest factor.
- **Frequency domain**, per channel: FFT with a Hann window, peak magnitude and frequency, spectral centroid and spread, and others.
- **Time-frequency**, per channel: STFT (Hamming window, 256 samples, 75% overlap), total energy, dominant frequency, statistics of spectral variance and spectral flux.
- **Multi-axis**, for the accelerometer and the gyroscope: covariance and correlation between axes, and signal magnitude.

### 4. PCA (`4_PCA/`)
- The features are standardised (z-score), then PCA keeps the components that explain **95% of the variance**, which gives **43 PCs**.
- `pca_params.mat` (μ, σ and the loadings) is saved so the online model can apply exactly the same transformation.
- Scree plot, cumulative variance, and 2D/3D score plots.

### 5. Machine learning (`5_machine_learning/`)
Binary classification of `passo1` vs `passo2` on the 43 PCs, with a stratified 80/20 hold-out split:
- **Boosted decision trees** (`ML_albero.m`): LogitBoost ensemble with a grid search over the number of learning cycles, learning rate and maximum splits, using 3-fold cross-validation. Best values: 500 cycles, learning rate 0.1, 7 maximum splits.
- **SVM** (`SVM.m`): RBF and linear kernels, with a grid search over kernel scale and box constraint using 5-fold stratified cross-validation. The best model is chosen on the test set and exported with `saveLearnerForCoder`.
- **Metrics:** accuracy, precision, recall, F1-score and the confusion matrix.

### 6. Online recognition (`6_online/`)
`Circuito_Online_Definitivo.slx` runs the whole pipeline **in real time** with MATLAB Function blocks that support code generation (`%#codegen`):
1. **Online band-pass filter:** sample by sample, keeping the filter states between steps.
2. **Online windowing:** a circular pre-trigger buffer of 200 samples, threshold detection, collection of the post-trigger samples (770-sample window), and a refractory period so the same step doesn't trigger twice.
3. **Feature extraction:** the same 162 features as offline.
4. **PCA projection** with the saved parameters.
5. **SVM prediction:** `loadLearnerForCoder`.
6. **Label hold:** the last label is kept on screen. If no step is detected for 2 s, the state switches to **`fermo`** (still).
7. **Video display:** shows an image of the recognised movement (`passo1.png`, `passo2.png` or `fermo.png`).

---

## Limitations
- The train/test split is done **on windows, not on participants**. Repetitions from the same person can end up in both sets, so the test performance is probably optimistic. A *leave-one-subject-out* validation would give a more realistic estimate.
- PCA is fitted on the whole dataset before the split.
- The trigger threshold (1.7) and the window length are fixed and were tuned on these recordings.

---

## How to run
- **Requirements:** MATLAB/Simulink with Signal Processing, Statistics and Machine Learning, and *Simulink Support Package for Android Devices* for the live phone sensors.
- **Offline:** run the scripts in folders 2 → 5 in order. Each folder already contains the `.mat` files it needs.
- **Online:** connect the phone with `Script_wifi.m` (set your own ADB path and the phone's IP address), then open and run `6_online/Circuito_Online_Definitivo.slx`.

---

*Group project developed with fellow students at Università Campus Bio-Medico di Roma. Code comments are in Italian.*
