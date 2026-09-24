# Machine Learning Specification — Hospital Readmission AI

> **Status:** Specification  
> **Framework:** Apache Spark MLlib (PySpark)  
> **Target Problem:** Binary Classification (30-Day Hospital Readmission)


---

## 1. Problem Formulation

The task is framed as a supervised binary classification problem:

$$\hat{y} \in \{0, 1\}$$

- **Target Label ($y = 1$):** Patient was readmitted to the hospital within 30 days of discharge (`<30`).
- **Negative Label ($y = 0$):** Patient was not readmitted or was readmitted after 30 days (`>30` or `NO`).

In addition to discrete classification, models will output calibrated posterior probabilities $P(y = 1 \mid \mathbf{x})$ representing the continuous patient readmission risk score ($0.0\%$ to $100.0\%$).

---

## 2. Planned ML Algorithms (Spark MLlib)

The pipeline will benchmark four distinct algorithmic paradigms:

| Model | Class / Implementation | Key Characteristics & Hyperparameters |
|---|---|---|
| **Logistic Regression** | `pyspark.ml.classification.LogisticRegression` | Linear baseline, highly interpretable, calibrated probabilities (`regParam`, `elasticNetParam`, `maxIter`). |
| **Decision Tree** | `pyspark.ml.classification.DecisionTreeClassifier` | Non-linear rule-based tree model (`maxDepth`, `maxBins`, `minInstancesPerNode`, `impurity`). |
| **Random Forest** | `pyspark.ml.classification.RandomForestClassifier` | Ensemble of bagged decision trees, robust against overfitting (`numTrees`, `maxDepth`, `featureSubsetStrategy`). |
| **Gradient Boosted Trees** | `pyspark.ml.classification.GBTClassifier` | Sequential boosting ensemble optimizing residual errors (`maxIter`, `stepSize`, `maxDepth`). |

---

## 3. Evaluation Metrics Suite

Each model will be evaluated across a comprehensive suite of performance, clinical utility, and operational metrics:

### 3.1 Discrimination & Classification Metrics
1. **F1-Score:** Harmonic mean of precision and recall (Primary selection metric).
2. **Recall (Sensitivity):** Proportion of actual 30-day readmissions correctly identified ($\frac{TP}{TP + FN}$).
3. **Precision (Positive Predictive Value):** Proportion of flagged patients who were genuinely readmitted ($\frac{TP}{TP + FP}$).
4. **Specificity (True Negative Rate):** Proportion of non-readmitted patients correctly identified ($\frac{TN}{TN + FP}$).
5. **Accuracy:** Overall proportion of correct predictions ($\frac{TP + TN}{TP + TN + FP + FN}$).
6. **AUC-ROC (Area Under ROC Curve):** Discrimination capability across all classification thresholds.
7. **Confusion Matrix:** Breakdown of True Positives, False Positives, True Negatives, and False Negatives.

### 3.2 Computational & Operational Benchmarks
1. **Training Time:** Elapsed wall-clock time (seconds) for pipeline fitting on the Spark cluster.
2. **Prediction / Inference Time:** Average latency (milliseconds) per 1,000 records during batch scoring.

---

## 4. Model Selection Strategy

- **Default Selection Metric:** **F1-Score** (to balance the precision-recall trade-off inherent in class-imbalanced healthcare data).
- **Configurability:** Model selection criterion will be configurable via `config/config.yaml` (options: `f1`, `recall`, `auc_roc`, `precision`, `accuracy`).
- **Tie-Breaking Rule:** In the event of matching primary scores, highest `AUC-ROC` followed by lowest `prediction_time` will determine the champion model.
- **Champion Artifact:** The winning model pipeline is automatically tagged and persisted in `models/champion/` for API serving.
