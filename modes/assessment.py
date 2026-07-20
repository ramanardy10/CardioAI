"""Assessment modes: Patient, Clinical, Research."""

import numpy as np
import pandas as pd
import streamlit as st

from core import config
from core.model import load_artifacts, model_metrics, tuned_threshold, transform
from ui import charts, forms, theme
from ui.results import run_and_render


def patient_mode():
    theme.hero("Your heart health check",
               "A quick, plain-language look at your heart disease risk factors.",
               "Patient mode")
    st.markdown('<div class="cai-muted">Answer a few questions about your health. '
                "This is a research tool, not a diagnosis - it helps you decide "
                "whether to talk to your doctor.</div>", unsafe_allow_html=True)
    st.write("")

    theme.card_open("About you", "user")
    patient = forms.patient_form(scope="patient", prefix="pat")
    theme.card_close()

    if st.button("Check my risk", type="primary", use_container_width=True):
        run_and_render(patient, "Patient", show_meds=False,
                       show_timeline=True, audience="patient")


def clinical_mode():
    theme.hero("Clinical decision support",
               "Full risk assessment with per-patient explanations and "
               "guideline-anchored discussion points.",
               "Clinical mode")
    _model_ribbon()

    theme.card_open("Patient assessment", "stethoscope")
    patient = forms.patient_form(scope="clinical", prefix="cli")
    theme.card_close()

    if st.button("Assess patient", type="primary", use_container_width=True):
        run_and_render(patient, "Clinical", show_meds=True,
                       show_timeline=True, audience="clinician")


def research_mode():
    theme.hero("Research workbench",
               "Batch scoring, cohort simulation and model transparency for "
               "evaluation.",
               "Research mode")
    _model_ribbon()

    tab1, tab2 = st.tabs(["Single case", "Cohort simulation"])

    with tab1:
        theme.card_open("Case inputs", "flask")
        patient = forms.patient_form(scope="research", prefix="res")
        theme.card_close()
        if st.button("Score case", type="primary", use_container_width=True):
            run_and_render(patient, "Research", show_meds=True,
                           show_timeline=True, audience="clinician")

    with tab2:
        _cohort_simulation()


def _model_ribbon():
    _, _, metadata, _ = load_artifacts()
    m = model_metrics(metadata)
    theme.metric_row([
        ("sparkle", m["model_name"], "Best model"),
        ("chart", f"{m['roc_auc']:.2%}", "ROC-AUC"),
        ("pulse", f"{m['threshold']:.4f}", "Tuned threshold"),
        ("shield", f"{m['recall_target']:.0%}", "Recall target"),
    ])
    st.write("")


def _cohort_simulation():
    theme.card_open("Simulate a synthetic cohort", "chart")
    st.markdown('<div class="cai-muted">Draws random patients from the training '
                "category distributions to illustrate score spread. Synthetic - "
                "for demonstration, not epidemiological inference.</div>",
                unsafe_allow_html=True)
    n = st.slider("Cohort size", 50, 1000, 300, 50, key="cohort_n")
    if st.button("Run simulation", type="primary"):
        model, params, metadata, _ = load_artifacts()
        tuned = tuned_threshold(metadata)
        rng = np.random.default_rng(7)
        probs, bands, rows = [], [], []
        ph = st.empty()
        with ph:
            theme.loader(f"Scoring {n} synthetic patients")
        for _ in range(n):
            p = {}
            for c in params["numeric_cols"]:
                mu = params["numeric_mean"][c]
                sd = params["numeric_scale"][c]
                p[c] = float(rng.normal(mu, sd))
            for c in params["categorical_cols"]:
                p[c] = str(rng.choice(params["categorical_categories"][c]))
            prob = float(model.predict_proba(transform(p, params))[0][1])
            band, _ = config.classify_risk(prob, tuned)
            probs.append(prob); bands.append(band)
            rows.append({**{k: p[k] for k in list(p)[:4]},
                         "risk": round(prob, 4), "band": band})
        ph.empty()

        c1, c2 = st.columns([3, 2])
        with c1:
            st.plotly_chart(charts.distribution_hist(probs, tuned),
                            use_container_width=True, key="cohort_hist")
        with c2:
            counts = pd.Series(bands).value_counts().to_dict()
            st.plotly_chart(charts.band_donut(counts),
                            use_container_width=True, key="cohort_donut")
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Export cohort (CSV)",
                           df.to_csv(index=False).encode(),
                           "cardioai_cohort.csv", "text/csv")
    theme.card_close()
