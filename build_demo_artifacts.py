"""Build schema-compatible DEMO artifacts so the app runs out of the box.

This trains a small XGBoost model on synthetic BRFSS-shaped data and exports:
  artifacts/best_model.pkl
  artifacts/preprocessor_params.json   (version-proof, no pickle)
  artifacts/metadata.json
  artifacts/shap_feature_importance.csv

REPLACE THESE with your real dissertation artifacts before submission.
The app reads whatever is in artifacts/, so your real files drop straight in
as long as preprocessor_params.json follows the same structure (see README).
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

import joblib

RNG = np.random.default_rng(42)
ART = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ART, exist_ok=True)

AGE = ["Age 18 to 24", "Age 25 to 29", "Age 30 to 34", "Age 35 to 39",
       "Age 40 to 44", "Age 45 to 49", "Age 50 to 54", "Age 55 to 59",
       "Age 60 to 64", "Age 65 to 69", "Age 70 to 74", "Age 75 to 79",
       "Age 80 or older"]
GENH = ["Excellent", "Very good", "Good", "Fair", "Poor"]
SMOKE = ["Never smoked", "Former smoker",
         "Current smoker - now smokes some days",
         "Current smoker - now smokes every day"]
YN = ["No", "Yes"]

NUM = ["BMI", "SleepHours", "PhysicalHealthDays", "MentalHealthDays"]
CAT = ["AgeCategory", "Sex", "GeneralHealth", "SmokerStatus",
       "PhysicalActivities", "AlcoholDrinkers", "HadDiabetes",
       "HadAngina", "HadStroke", "DifficultyWalking"]

N = 6000
age_idx = RNG.integers(0, len(AGE), N)
df = pd.DataFrame({
    "BMI": np.clip(RNG.normal(28, 6, N), 14, 60).round(1),
    "SleepHours": np.clip(RNG.normal(7, 1.4, N), 2, 14).round(0),
    "PhysicalHealthDays": RNG.integers(0, 31, N),
    "MentalHealthDays": RNG.integers(0, 31, N),
    "AgeCategory": [AGE[i] for i in age_idx],
    "Sex": RNG.choice(["Female", "Male"], N),
    "GeneralHealth": RNG.choice(GENH, N, p=[.15, .3, .3, .18, .07]),
    "SmokerStatus": RNG.choice(SMOKE, N, p=[.55, .25, .1, .1]),
    "PhysicalActivities": RNG.choice(YN, N, p=[.25, .75]),
    "AlcoholDrinkers": RNG.choice(YN, N, p=[.45, .55]),
    "HadDiabetes": RNG.choice(YN, N, p=[.86, .14]),
    "HadAngina": RNG.choice(YN, N, p=[.94, .06]),
    "HadStroke": RNG.choice(YN, N, p=[.96, .04]),
    "DifficultyWalking": RNG.choice(YN, N, p=[.83, .17]),
})

# Latent risk driven by clinically sensible factors -> class imbalance.
logit = (
    -4.2
    + 0.09 * (df["BMI"] - 28)
    + 0.16 * age_idx
    + 1.7 * (df["HadAngina"] == "Yes")
    + 1.2 * (df["HadStroke"] == "Yes")
    + 0.9 * (df["HadDiabetes"] == "Yes")
    + 0.7 * df["SmokerStatus"].str.contains("Current").astype(int)
    + 0.6 * (df["DifficultyWalking"] == "Yes")
    + 0.5 * (df["GeneralHealth"].isin(["Fair", "Poor"]))
    - 0.3 * (df["PhysicalActivities"] == "Yes")
)
p = 1 / (1 + np.exp(-logit))
y = (RNG.random(N) < p).astype(int)
print(f"positives: {y.mean():.1%}")

pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                      ("sc", StandardScaler())]), NUM),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                      ("oh", OneHotEncoder(handle_unknown="ignore"))]), CAT),
])
X = pre.fit_transform(df)
model = XGBClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.08,
    scale_pos_weight=(y == 0).sum() / max((y == 1).sum(), 1),
    subsample=0.9, colsample_bytree=0.9, eval_metric="auc",
    random_state=42,
)
model.fit(X, y)
joblib.dump(model, os.path.join(ART, "best_model.pkl"))

# ---- version-proof preprocessor params ----
num_imp = pre.named_transformers_["num"].named_steps["imp"]
num_sc = pre.named_transformers_["num"].named_steps["sc"]
cat_imp = pre.named_transformers_["cat"].named_steps["imp"]
cat_oh = pre.named_transformers_["cat"].named_steps["oh"]

params = {
    "numeric_cols": NUM,
    "categorical_cols": CAT,
    "numeric_median": {c: float(v) for c, v in zip(NUM, num_imp.statistics_)},
    "numeric_mean": {c: float(v) for c, v in zip(NUM, num_sc.mean_)},
    "numeric_scale": {c: float(v) for c, v in zip(NUM, num_sc.scale_)},
    "categorical_most_frequent": {c: str(v) for c, v in zip(CAT, cat_imp.statistics_)},
    "categorical_categories": {c: [str(x) for x in cats]
                               for c, cats in zip(CAT, cat_oh.categories_)},
}
with open(os.path.join(ART, "preprocessor_params.json"), "w") as f:
    json.dump(params, f, indent=2)

# verify JSON transform == pipeline transform
def json_transform(row):
    v = []
    for c in NUM:
        v.append((float(row[c]) - params["numeric_mean"][c]) / params["numeric_scale"][c])
    for c in CAT:
        for cat in params["categorical_categories"][c]:
            v.append(1.0 if str(row[c]) == cat else 0.0)
    return np.array(v)

diff = np.abs(json_transform(df.iloc[0]) - X[0].toarray().ravel()
              if hasattr(X, "toarray") else json_transform(df.iloc[0]) - X[0]).max()
print(f"max abs transform diff: {diff:.2e}")

# threshold for 80% recall
from sklearn.metrics import roc_auc_score, precision_recall_curve
prob = model.predict_proba(X)[:, 1]
auc = roc_auc_score(y, prob)
prec, rec, thr = precision_recall_curve(y, prob)
idx = np.argmin(np.abs(rec[:-1] - 0.80))
tuned = float(thr[idx])
print(f"AUC {auc:.4f}  tuned threshold {tuned:.4f}")

with open(os.path.join(ART, "metadata.json"), "w") as f:
    json.dump({
        "best_model": "XGBoost",
        "roc_auc": round(float(auc), 4),
        "tuned_threshold": round(tuned, 4),
        "recall_target": 0.80,
        "note": "DEMO artifacts - replace with real dissertation artifacts.",
    }, f, indent=2)

# global SHAP importance export
import shap
expl = shap.TreeExplainer(model)
sv = expl.shap_values(X[:800] if not hasattr(X, "toarray") else X[:800].toarray())
sv = np.asarray(sv)
if sv.ndim == 3:
    sv = sv[:, :, -1]
names = list(NUM)
for c in CAT:
    names += [c] * len(params["categorical_categories"][c])
imp = np.abs(sv).mean(0)
agg = {}
for v, c in zip(imp, names):
    agg[c] = agg.get(c, 0.0) + float(v)
pd.DataFrame(sorted(agg.items(), key=lambda kv: -kv[1]),
             columns=["feature", "mean_abs_shap"]).to_csv(
    os.path.join(ART, "shap_feature_importance.csv"), index=False)

print("Demo artifacts written to", ART)
