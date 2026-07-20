"""SHAP explainability for CardioAI.

Per-patient explanations via TreeExplainer, aggregated back to the original
clinical features (one-hot columns are summed per source feature) so the
output reads clinically rather than as encoder columns.
"""

import numpy as np
import pandas as pd
import shap
import streamlit as st

from core import config
from core.model import load_artifacts, transform, original_feature_of


@st.cache_resource(show_spinner=False)
def get_explainer():
    model, _, _, _ = load_artifacts()
    return shap.TreeExplainer(model)


def _to_positive_class(values):
    """Normalise SHAP output shapes (2D, 3D, list) to a 1D vector for the
    positive class of a single sample."""
    if isinstance(values, list):
        values = values[1] if len(values) > 1 else values[0]
    arr = np.asarray(values)
    if arr.ndim == 3:            # (n, features, classes)
        arr = arr[:, :, -1]
    return arr[0]


def explain_patient(patient: dict) -> pd.DataFrame:
    """Return per-original-feature SHAP contributions for one patient,
    sorted by absolute impact (descending)."""
    _, params, _, _ = load_artifacts()
    x = transform(patient, params)
    raw = _to_positive_class(get_explainer().shap_values(x))
    origin = original_feature_of(params)

    agg = {}
    for val, col in zip(raw, origin):
        agg[col] = agg.get(col, 0.0) + float(val)

    df = pd.DataFrame(
        [{"feature": c,
          "label": config.label_for(c),
          "value": str(patient.get(c, "(default)")),
          "shap": v} for c, v in agg.items()]
    )
    df["abs"] = df["shap"].abs()
    return df.sort_values("abs", ascending=False).reset_index(drop=True)


def global_importance() -> pd.DataFrame:
    """Global feature importance from the training-time SHAP export if
    available, otherwise from the model's own gain-based importances."""
    model, params, _, shap_csv = load_artifacts()
    if shap_csv is not None and len(shap_csv.columns) >= 2:
        df = shap_csv.copy()
        df.columns = ["feature", "importance"] + list(df.columns[2:])
    else:
        origin = original_feature_of(params)
        imp = getattr(model, "feature_importances_", None)
        if imp is None:
            return pd.DataFrame(columns=["feature", "importance", "label"])
        agg = {}
        for v, c in zip(imp, origin):
            agg[c] = agg.get(c, 0.0) + float(v)
        df = pd.DataFrame([{"feature": k, "importance": v} for k, v in agg.items()])
    df["label"] = df["feature"].map(config.label_for)
    return df.sort_values("importance", ascending=False).reset_index(drop=True)
