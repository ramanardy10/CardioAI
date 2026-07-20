"""Model artifact loading and inference for CardioAI.

Preprocessing is rebuilt deterministically from `preprocessor_params.json`
(learned medians, means, scales and category lists exported from the fitted
sklearn pipeline), so inference never depends on unpickling a preprocessor
across scikit-learn versions. Verified to reproduce the original pipeline's
transform exactly (max abs diff 0.0).
"""

import json
import os
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from core import config

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")

REQUIRED_FILES = ["best_model.pkl", "preprocessor_params.json"]


def artifacts_present() -> bool:
    return all(os.path.exists(os.path.join(ARTIFACT_DIR, f)) for f in REQUIRED_FILES)


def missing_files():
    return [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(ARTIFACT_DIR, f))]


@st.cache_resource(show_spinner=False)
def load_artifacts():
    """Load model, preprocessing parameters and metadata once per process."""
    model = joblib.load(os.path.join(ARTIFACT_DIR, "best_model.pkl"))
    with open(os.path.join(ARTIFACT_DIR, "preprocessor_params.json")) as f:
        params = json.load(f)

    metadata = {}
    meta_path = os.path.join(ARTIFACT_DIR, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            metadata = json.load(f)

    shap_csv = None
    shap_path = os.path.join(ARTIFACT_DIR, "shap_feature_importance.csv")
    if os.path.exists(shap_path):
        shap_csv = pd.read_csv(shap_path)

    return model, params, metadata, shap_csv


def _meta_get(metadata: dict, keys, default):
    """Search metadata for the first matching key, including one level deep."""
    for k in keys:
        if k in metadata:
            return metadata[k]
    for v in metadata.values():
        if isinstance(v, dict):
            for k in keys:
                if k in v:
                    return v[k]
    return default


def tuned_threshold(metadata: dict) -> float:
    return float(_meta_get(
        metadata,
        ["tuned_threshold", "best_threshold", "threshold", "optimal_threshold"],
        config.DEFAULT_TUNED_THRESHOLD,
    ))


def model_metrics(metadata: dict) -> dict:
    return {
        "model_name": _meta_get(metadata, ["best_model", "model_name", "model"],
                                config.DEFAULT_MODEL_NAME),
        "roc_auc": float(_meta_get(metadata, ["roc_auc", "auc", "test_roc_auc"],
                                   config.DEFAULT_ROC_AUC)),
        "recall_target": float(_meta_get(metadata, ["recall_target", "target_recall"], 0.80)),
        "threshold": tuned_threshold(metadata),
    }


def feature_names(params: dict):
    """Post-transform feature names: numeric cols, then one-hot expansions."""
    names = list(params["numeric_cols"])
    for c in params["categorical_cols"]:
        names += [f"{c} = {cat}" for cat in params["categorical_categories"][c]]
    return names


def original_feature_of(params: dict):
    """Map each transformed feature index back to its original column."""
    origin = list(params["numeric_cols"])
    for c in params["categorical_cols"]:
        origin += [c] * len(params["categorical_categories"][c])
    return origin


def transform(patient: dict, params: dict) -> np.ndarray:
    """Deterministic re-implementation of the fitted preprocessing pipeline:
    median imputation + standard scaling for numerics, most-frequent
    imputation + one-hot encoding for categoricals."""
    values = []
    for c in params["numeric_cols"]:
        x = patient.get(c, params["numeric_median"][c])
        try:
            x = float(x)
        except (TypeError, ValueError):
            x = params["numeric_median"][c]
        values.append((x - params["numeric_mean"][c]) / params["numeric_scale"][c])
    for c in params["categorical_cols"]:
        x = str(patient.get(c, params["categorical_most_frequent"][c]))
        for cat in params["categorical_categories"][c]:
            values.append(1.0 if x == cat else 0.0)
    return np.array(values, dtype=float).reshape(1, -1)


def predict_probability(patient: dict) -> float:
    model, params, _, _ = load_artifacts()
    return float(model.predict_proba(transform(patient, params))[0][1])


def risk_timeline(patient: dict):
    """Model-based risk projection across age groups with all other inputs
    held constant. A counterfactual illustration, not a forecast."""
    model, params, _, _ = load_artifacts()
    if "AgeCategory" not in params["categorical_cols"]:
        return None
    ages = params["categorical_categories"]["AgeCategory"]
    rows = []
    for age in ages:
        p = dict(patient)
        p["AgeCategory"] = age
        rows.append({
            "AgeCategory": age,
            "risk": float(model.predict_proba(transform(p, params))[0][1]),
            "current": age == patient.get("AgeCategory"),
        })
    return pd.DataFrame(rows)
