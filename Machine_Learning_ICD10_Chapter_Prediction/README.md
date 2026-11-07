# ICD-10 Chapter Prediction from Hospital Admission Data

Group project (3 students) for the **Machine Learning and Big Data Analytics** course, MSc in Biomedical Engineering, Università Campus Bio-Medico di Roma (exam session: July 2026).

The goal is to **automatically assign the ICD-10 macro-chapter** of a hospital admission from the patient's clinical profile: demographics, triage parameters and blood tests. The project compares **12 machine-learning pipelines** with a leakage-free **nested cross-validation**.

---

## Dataset
- **3,198 anonymised admissions** (ICU or emergency department), patients aged 18–91, with a mean age of 38 ± 15 years.
- **Four tables joined on `hadm_id`:**
  - `Demographic.csv` (7 features);
  - `Triage.csv` (8 features: vital signs, pain, acuity);
  - `BloodTest.csv` (11 blood parameters, recorded as time series);
  - `ICD_chapter.csv` (the target).
- **Target:** 3 macro-classes, **imbalanced**:

| Class | Share |
|---|---|
| V | 55.3% |
| XI | 24.3% |
| VI-X-XIII | 20.4% |

The CSV files are **not included** in this repository. The notebook asks for them to be uploaded at runtime, on Google Colab.

---

## Methods

### Pre-processing and feature engineering (26 → 113 features)
- **Blood-test time series** are turned into aggregate statistics: mean, first and last value, trend, min/max, standard deviation, number of measurements.
- **C-reactive protein** is turned into a binary present/absent indicator, because its missing values are not random (MNAR).
- **Numerical features:** mean imputation → Kruskal–Wallis filter (p < 0.001) → StandardScaler.
- **Categorical and binary features:** mode imputation → χ² filter (p < 0.001) → one-hot encoding.
- **No data leakage:** all pre-processing and selection steps are inside the scikit-learn pipeline, so they are fitted only on the training data of each fold.

### Preliminary statistical analysis
- **82 of 98** numerical features are significant (Kruskal–Wallis), and **14 of 15** categorical features are significant (χ²), both at p < 0.001.
- The most discriminative features are **pain**, **Calcium_min**, **admission_type**, and the number of white-blood-cell and MCV measurements.

### Models compared (12 pipelines)
- **Baseline:** Dummy classifier (most frequent class).
- **Logistic Regression** (Elastic Net) and **SVM** (RBF kernel, one-vs-one), each in 4 variants: base, statistical filter, LDA, and filter + LDA.
- **Decision Tree**, **Random Forest** (500 trees) and **XGBoost** (`multi:softprob`).

### Validation
- **Stratified 80/20 split** into training set and independent test set.
- **Nested cross-validation on the training set:** 5 outer folds for model selection, 3 inner folds for the hyperparameter grid search.
- **Selection metric:** **macro-F1**, which suits imbalanced classes.
- **Ablation study** on the best model, with different combinations of feature groups (demographics, triage, blood).

---

## Results

### Nested CV (macro-F1, mean ± std over 5 outer folds)
| Pipeline | Macro-F1 |
|---|---|
| **XGBoost** | **77.6% ± 1.2%** |
| LR + filter | 74.8% ± 0.8% |
| SVM RBF + filter + LDA | 74.8% ± 0.6% |
| SVM RBF (base) | 74.6% ± 1.9% |
| Random Forest | 73.3% ± 2.4% |
| Decision Tree | 69.0% ± 1.1% |
| Dummy (baseline) | 23.8% |

**Final XGBoost hyperparameters:** learning_rate 0.1, max_depth 4, subsample 0.8.

**Ablation study:** the **full feature set (113 features, 78.0% macro-F1)** scores better than any subset, so demographics, triage and blood tests carry complementary information.

### Independent test set (20%, 640 admissions)
| Metric | Value |
|---|---|
| Macro-F1 | **76.5%** |
| Weighted-F1 | 82.4% |
| Accuracy | 83.0% |
| Balanced accuracy | 76.0% |
| Cohen's κ | 0.71 |

| Class | Precision | Recall | F1 |
|---|---|---|---|
| V | 0.91 | 0.95 | 0.93 |
| VI-X-XIII | 0.65 | 0.53 | **0.58** |
| XI | 0.77 | 0.79 | 0.78 |

The test-set result (76.5%) is close to the nested-CV estimate (77.6%), which confirms that the validation procedure did not overestimate performance.

### Limitations and future work
- The **VI-X-XIII** group has the fewest samples and is clinically heterogeneous, since it merges three different chapters, so it is the hardest class to recognise.
- **Future work:** hierarchical classification, adding clinical text and comorbidities, interpretability methods such as SHAP, and external validation.

---

## Repository structure
```
├── icd10_chapter_prediction.ipynb   # Full pipeline: preprocessing, statistics, nested CV, ablation, test
└── docs/presentation.pptx           # Final presentation (in Italian)
```

## How to run
Open the notebook in **Google Colab** and run the cell. When prompted, upload the 4 CSV files.

**Libraries:** `pandas`, `numpy`, `scipy`, `scikit-learn`, `xgboost`, `matplotlib`.

---

*Group project developed with fellow students at Università Campus Bio-Medico di Roma. Code comments are in Italian.*
