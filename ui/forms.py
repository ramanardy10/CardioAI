"""Input-form builder for CardioAI.

Widgets are generated from the artifact schema (preprocessor_params.json), so
the form always matches whatever the model was actually trained on. Numeric
columns get sliders/number inputs; categoricals get select boxes with the
exact training categories.
"""

import streamlit as st

from core import config
from core.model import load_artifacts

# Sensible slider ranges for well-known numeric fields.
NUM_RANGES = {
    "BMI": (12.0, 65.0, 27.0, 0.5),
    "SleepHours": (2.0, 14.0, 7.0, 1.0),
    "PhysicalHealthDays": (0.0, 30.0, 0.0, 1.0),
    "MentalHealthDays": (0.0, 30.0, 0.0, 1.0),
    "HeightInMeters": (1.3, 2.2, 1.70, 0.01),
    "WeightInKilograms": (35.0, 200.0, 75.0, 1.0),
}


def _num_widget(col, params, key):
    lo, hi, default, step = NUM_RANGES.get(
        col, (0.0, 100.0, float(params["numeric_median"].get(col, 0.0)), 1.0))
    med = float(params["numeric_median"].get(col, default))
    default = min(max(med, lo), hi)
    return st.slider(config.label_for(col), lo, hi, default, step, key=key)


def _cat_widget(col, params, key):
    cats = params["categorical_categories"][col]
    default = params["categorical_most_frequent"].get(col, cats[0])
    idx = cats.index(default) if default in cats else 0
    return st.selectbox(config.label_for(col), cats, index=idx, key=key)


def _field(col, params, key):
    if col in params["numeric_cols"]:
        return _num_widget(col, params, key)
    if col in params["categorical_cols"]:
        return _cat_widget(col, params, key)
    return None


def patient_form(scope="patient", prefix="f"):
    """Render inputs and return a patient dict.

    scope='patient'  -> core simplified fields only
    scope='clinical' -> full grouped form (expanders)
    scope='research' -> full form, flat, plus a randomise helper
    """
    _, params, _, _ = load_artifacts()
    known = set(params["numeric_cols"]) | set(params["categorical_cols"])
    patient = {}

    if scope == "patient":
        fields = [c for c in config.PATIENT_CORE_FEATURES if c in known]
        cols = st.columns(2)
        for i, col in enumerate(fields):
            with cols[i % 2]:
                v = _field(col, params, f"{prefix}_{col}")
                if v is not None:
                    patient[col] = v
        # fill the rest silently with training defaults
        for col in known:
            patient.setdefault(
                col, params["numeric_median"].get(col)
                if col in params["numeric_cols"]
                else params["categorical_most_frequent"].get(col))
        return patient

    # clinical / research: grouped full form
    grouped = set()
    for group, cols in config.CLINICAL_GROUPS.items():
        present = [c for c in cols if c in known]
        if not present:
            continue
        with st.expander(group, expanded=(group == "Demographics")):
            grid = st.columns(2)
            for i, col in enumerate(present):
                with grid[i % 2]:
                    v = _field(col, params, f"{prefix}_{col}")
                    if v is not None:
                        patient[col] = v
                grouped.add(col)

    # any columns not covered by groups
    leftover = [c for c in known if c not in grouped]
    if leftover:
        with st.expander("Other inputs", expanded=False):
            grid = st.columns(2)
            for i, col in enumerate(leftover):
                with grid[i % 2]:
                    v = _field(col, params, f"{prefix}_{col}")
                    if v is not None:
                        patient[col] = v

    for col in known:
        patient.setdefault(
            col, params["numeric_median"].get(col)
            if col in params["numeric_cols"]
            else params["categorical_most_frequent"].get(col))
    return patient
