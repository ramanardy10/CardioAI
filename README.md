# CardioAI

**Explainable heart disease risk prediction** — an MSc Applied AI research prototype.

XGBoost model (ROC-AUC ~93.9% on the real dissertation artifacts) trained on
cross-wave enriched CDC BRFSS data (2022 + 2020 positive cases), with per-patient
SHAP explanations, a decision threshold tuned for ~80% recall, evidence-based
lifestyle guidance, ESC-referenced clinical discussion points, and PDF/CSV export.

> **Not a medical device.** CardioAI is a research prototype. It is not CE-marked,
> not clinically validated, and must not be used for medical decisions.

---

## Features

| Area | What's included |
|------|-----------------|
| **Four modes** | Patient · Clinical · Research · Admin (PIN-gated) |
| **Explainability** | Per-patient SHAP (interactive), global feature importance |
| **Risk timeline** | Model risk across age groups, other inputs held constant |
| **Guidance** | Lifestyle recommendations + medication discussion (clinician only), all ESC-referenced |
| **Dashboards** | Analytics, risk distribution, population statistics, prediction history, audit logs |
| **Exports** | PDF report (patient + clinician), CSV factor/history/cohort export |
| **Design** | Dark/light mode, responsive, animated, accessible (focus states, reduced-motion), professional inline SVG icons |

---

## Deploy to Streamlit Community Cloud

1. Push this folder to a **public** GitHub repo (keep the folder structure intact).
2. Go to <https://share.streamlit.io> → **New app**.
3. Repository: your repo · Branch: `main` · **Main file path: `app.py`**
4. Click **Deploy**. First build takes a few minutes while dependencies install.

That's it — no database, secrets, or environment variables are required. Prediction
history and audit logs live in the browser session.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the Local URL it prints (usually <http://localhost:8501>).
Launch with `streamlit run app.py`, **not** the editor's Run button.

---

## Using your real model artifacts

This package ships with **demo artifacts** so it runs immediately. Replace them
with your trained dissertation artifacts in the `artifacts/` folder:

```
artifacts/
  best_model.pkl              # your trained XGBoost model (joblib.dump)
  preprocessor_params.json    # version-proof preprocessing params (see below)
  metadata.json               # optional: threshold + metrics
  shap_feature_importance.csv # optional: global SHAP export
```

### Why `preprocessor_params.json` instead of `preprocessor.pkl`

Pickled scikit-learn transformers break when the deployment's scikit-learn
version differs from the one they were saved under (this was the original app's
deploy bug). Instead, CardioAI rebuilds preprocessing deterministically from the
transformer's **learned parameters**, exported as JSON. This reproduces the
fitted pipeline's transform exactly and never breaks across versions.

Export it once from your training environment:

```python
import json
# `pre` is your fitted ColumnTransformer with:
#   ("num", Pipeline[SimpleImputer(median), StandardScaler], NUM_COLS)
#   ("cat", Pipeline[SimpleImputer(most_frequent), OneHotEncoder], CAT_COLS)
num_imp = pre.named_transformers_["num"].named_steps["imp"]
num_sc  = pre.named_transformers_["num"].named_steps["sc"]
cat_imp = pre.named_transformers_["cat"].named_steps["imp"]
cat_oh  = pre.named_transformers_["cat"].named_steps["oh"]

params = {
  "numeric_cols": NUM_COLS,
  "categorical_cols": CAT_COLS,
  "numeric_median": dict(zip(NUM_COLS, map(float, num_imp.statistics_))),
  "numeric_mean":   dict(zip(NUM_COLS, map(float, num_sc.mean_))),
  "numeric_scale":  dict(zip(NUM_COLS, map(float, num_sc.scale_))),
  "categorical_most_frequent": dict(zip(CAT_COLS, map(str, cat_imp.statistics_))),
  "categorical_categories": {c: [str(x) for x in cats]
                             for c, cats in zip(CAT_COLS, cat_oh.categories_)},
}
json.dump(params, open("artifacts/preprocessor_params.json", "w"), indent=2)
```

`metadata.json` (optional) is read for the threshold and metrics:

```json
{ "best_model": "XGBoost", "roc_auc": 0.9387,
  "tuned_threshold": 0.1751, "recall_target": 0.80 }
```

If any optional file is absent, CardioAI falls back to the dissertation values
(threshold 0.1751, ROC-AUC 93.87%) and the model's own gain-based importances.

To regenerate the demo set at any time: `python build_demo_artifacts.py`.

---

## Project structure

```
app.py                     Entry point: navigation, routing, theme
build_demo_artifacts.py    Generates demo artifacts (replace with real ones)
requirements.txt           Pinned dependencies
runtime.txt                Python version pin for Streamlit Cloud
.streamlit/config.toml     Theme + server config
core/
  config.py                Constants, labels, risk-band logic
  model.py                 Artifact loading, version-proof transform, prediction
  shap_engine.py           Per-patient + global SHAP
  guidelines.py            Lifestyle rules + ESC references + medication points
  history.py               Session history + audit log
  reports.py               PDF + CSV export
ui/
  theme.py                 Palette, CSS, SVG icons, animated components
  charts.py                Plotly figures
  forms.py                 Schema-driven input forms
  results.py               Shared results renderer
modes/
  assessment.py            Patient / Clinical / Research pages
  dashboards.py            Analytics / History / Guidelines / Admin pages
artifacts/                 Model files (demo included)
```

---

## Data & governance

- **Source:** CDC Behavioral Risk Factor Surveillance System (BRFSS), 2022 wave
  enriched with 2020 positive cases; accessed via Kaggle (Kamil Pytlak,
  *Indicators of Heart Disease*).
- **Storage:** no server-side database; assessments exist only in the browser
  session and are cleared on refresh.
- **Minimisation:** no names or identifiers are collected.

## Admin access

Admin mode is gated by a prototype PIN (`cardio2026`, set in `core/config.py`).
This is a demonstration gate, not real authentication — replace it before any
non-prototype use.
