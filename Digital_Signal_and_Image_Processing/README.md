# Retinal Disease Analysis on the ODIR Dataset

Academic project for the course **Digital Signal and Image Processing** (*Elaborazione dei Segnali Digitali e delle Immagini*), MSc in Biomedical Engineering, Università Campus Bio-Medico di Roma, A.Y. 2024/2025. Exam session: February 2025.

The project has two parts, both based on colour fundus photographs from the **Ocular Disease Intelligent Recognition (ODIR)** dataset:

- **Task 1: feature extraction and statistical analysis.** Extract colour and texture features from retinal images and use statistical tests to find which features differ significantly between diseases.
- **Task 2: decision support system.** Train and compare two CNN classifiers for three eye diseases, validated with Nested K-Fold Cross-Validation.

---

## Dataset

- **Source:** [ODIR-5K on Kaggle](https://www.kaggle.com/datasets/andrewmvd/ocular-disease-recognition-odir5k) (`andrewmvd/ocular-disease-recognition-odir5k`)
- 6,392 fundus images (preprocessed version, 512×512 px), labelled into 8 classes: Normal (N), Diabetes (D), Glaucoma (G), Cataract (C), Age-related macular degeneration (A), Hypertension (H), Pathological myopia (M), Other (O).
- A table with patient age, sex and diagnostic keywords is also provided.
- The classes are strongly imbalanced, from 2,873 Normal images down to 128 Hypertension images.

The dataset is **not included** in this repository. The notebooks download it automatically with `kagglehub`.

---

## Task 1: Feature extraction and statistical analysis

**Pipeline:** pre-processing → feature extraction → statistical analysis → sample size estimation

1. **Pre-processing.** Segmentation of the fundus from the black background: grayscale threshold at 10, hole filling and morphological opening. Every feature is computed only inside this mask.
2. **Feature extraction.** 26 features per image:
   - **Colour:** R, G, B ratios and H, S, V ratios (OpenCV).
   - **Texture:** GLCM contrast, correlation, energy, homogeneity and entropy, each computed in 4 directions (0°, 45°, 90°, 135°) at distance 1 (scikit-image).
3. **Statistical analysis.**
   - **Normality:** Lilliefors test for each feature in each class. 49 distributions were normal and 159 were not.
   - **Multi-class comparison:** Kruskal–Wallis test. All 26 features showed significant differences across the 8 classes.
   - **Pairwise comparisons:** Welch's t-test when both distributions were normal (89 tests), otherwise Mann–Whitney U (639 tests). The p-values are shown as heatmaps.
   - Histograms and boxplots for each feature and class.
4. **Sample size estimation.** For the feature `glcm_contrast_pi/4`, the minimum number of images needed to detect a difference (confidence 95%, power 80%) was estimated for three class pairs:

| Pair | p-value | Required samples |
|---|---|---|
| D vs G | ≪ 0.001 | 82 |
| N vs A | < 0.05 | 881 |
| D vs A | > 0.05 | 3,862 |

**Main findings:** the H, S and V ratios separate Normal eyes from all pathological classes. GLCM entropy in the horizontal direction is highly discriminative for almost every pair of classes. The main limitation is class imbalance.

---

## Task 2: Decision support system (CNN classification)

**Problem:** 3-class classification of **Cataract (C)**, **AMD (A)** and **Glaucoma (G)**, a roughly balanced subset of 843 images.

- **Input:** RGB images resized to 128×128 and normalised to [0, 1].
- **Model 1, Sequential CNN (images only):** 3 convolutional blocks with 32, 64 and 128 filters plus max pooling, then Dense(128), Dropout(0.2) and a softmax output.
- **Model 2, Functional CNN (images + patient sex):** the same convolutional branch, concatenated with a small dense branch that takes the patient's sex as a second input.
- **Validation:** Nested K-Fold Cross-Validation with 4 outer folds and 3 inner folds.
  - Inner loop: grid search over batch size {16, 32, 64} and optimizer {Adam, SGD}.
  - Outer loop: the final model is trained with the best hyperparameters and evaluated on the held-out fold.
  - Early stopping and model checkpointing were used.
- **Metrics:** accuracy, precision, recall, F1-score (weighted), plus confusion matrices for each fold and in total.

### Results (mean over the 4 outer folds)

| Model | Accuracy | Precision | Recall | F1-score |
|---|---|---|---|---|
| Sequential CNN (images) | 0.740 | 0.760 | 0.718 | 0.736 |
| Functional CNN (images + sex) | 0.740 | 0.761 | 0.727 | 0.740 |

Adding the patient's sex did not meaningfully improve performance.

### Limitations and possible improvements
- Training accuracy (~0.85–0.93) is much higher than test accuracy (~0.74), which points to **overfitting**. Data augmentation or transfer learning from pre-trained networks would likely help.
- Early stopping and checkpointing monitor **training** accuracy rather than a validation metric.
- `KFold` was used instead of `StratifiedKFold`, so the class proportions can vary between folds.

---

## Repository structure

```
├── README.md
├── task1_feature_analysis.ipynb   # Task 1: features + statistical tests
├── task2_classification.ipynb     # Task 2: CNN models + nested CV
└── docs/
    └── report_task1.pdf           # Written report for Task 1 (in Italian)
```

## How to run

The notebooks were developed on **Google Colab** (Task 2 used a T4 GPU).

1. Open a notebook in Colab.
2. Run all cells. The dataset is downloaded automatically through `kagglehub`, which may ask for Kaggle credentials.

**Main libraries:** `numpy`, `pandas`, `opencv-python`, `scikit-image`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `scikit-learn`, `tensorflow`/`keras`, `kagglehub`, `tqdm`.

---

*Academic project developed at Università Campus Bio-Medico di Roma. Code comments and the report are in Italian.*
