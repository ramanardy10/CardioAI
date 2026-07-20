"""Shared results renderer for CardioAI prediction pages."""

import streamlit as st

from core import config, guidelines, history, reports
from core.model import load_artifacts, model_metrics, tuned_threshold, risk_timeline
from core.shap_engine import explain_patient
from ui import charts, theme


def run_and_render(patient, mode, show_meds=False, show_timeline=True,
                   audience="clinician"):
    """Predict, then render the full result surface for one patient."""
    model, params, metadata, _ = load_artifacts()
    tuned = tuned_threshold(metadata)
    metrics = model_metrics(metadata)

    ph = st.empty()
    with ph:
        theme.loader("Scoring patient and computing explanations")
    prob = float(model.predict_proba(
        __import__("core.model", fromlist=["transform"]).transform(patient, params)
    )[0][1])
    shap_df = explain_patient(patient)
    ph.empty()

    band, band_key = config.classify_risk(prob, tuned)
    top_factors = [f"{r.label} ({'+' if r.shap >= 0 else '-'}{abs(r.shap):.2f})"
                   for r in shap_df.head(3).itertuples()]
    history.add_prediction(mode, patient, prob, band, top_factors)

    # ---- headline ----
    left, right = st.columns([1, 1])
    with left:
        theme.card_open("Predicted risk", "pulse")
        st.plotly_chart(charts.risk_gauge(prob, tuned), use_container_width=True,
                        key=f"gauge_{mode}")
        st.markdown(theme.band_badge(band), unsafe_allow_html=True)
        st.markdown(
            f'<div class="cai-muted" style="margin-top:10px">Tuned threshold '
            f'<b>{tuned:.4f}</b> (targets {metrics["recall_target"]:.0%} recall). '
            f'Standard threshold 0.50. Model: {metrics["model_name"]}, '
            f'ROC-AUC {metrics["roc_auc"]:.2%}.</div>',
            unsafe_allow_html=True)
        theme.card_close()
    with right:
        theme.card_open("Why this score (interactive SHAP)", "sparkle")
        st.plotly_chart(charts.shap_waterfall(shap_df), use_container_width=True,
                        key=f"shap_{mode}")
        theme.card_close()

    # ---- interactive SHAP explorer ----
    with st.expander("Explore all factor contributions", expanded=False):
        n = st.slider("Factors to show", 4, min(20, len(shap_df)), 8,
                      key=f"shapn_{mode}")
        st.plotly_chart(charts.shap_waterfall(shap_df, n),
                        use_container_width=True, key=f"shapx_{mode}")
        st.dataframe(
            shap_df[["label", "value", "shap"]].rename(
                columns={"label": "Factor", "value": "Patient value",
                         "shap": "SHAP contribution"}),
            use_container_width=True, hide_index=True)

    # ---- risk timeline ----
    if show_timeline:
        tl = risk_timeline(patient)
        if tl is not None:
            theme.card_open("Risk timeline across age", "clock")
            st.plotly_chart(charts.timeline_chart(tl), use_container_width=True,
                            key=f"tl_{mode}")
            st.markdown('<div class="cai-muted">A counterfactual view: your other '
                        'answers are held constant while age varies. It shows how '
                        'the model weighs age, not a personal forecast.</div>',
                        unsafe_allow_html=True)
            theme.card_close()

    # ---- recommendations ----
    recs = guidelines.lifestyle_recommendations(patient)
    theme.card_open("Lifestyle recommendations (evidence-based)", "leaf")
    for r in recs:
        theme.rec_block(r["title"], r["advice"], r["reference"]["citation"])
    theme.card_close()

    meds = []
    if show_meds:
        meds = guidelines.medication_discussion()
        theme.card_open("Medication discussion points - clinician use only", "pill")
        st.markdown('<div class="cai-muted">Guideline anchors to inform the '
                    'clinical conversation. CardioAI does not recommend '
                    'prescribing decisions.</div>', unsafe_allow_html=True)
        for m in meds:
            theme.rec_block(m["topic"], m["point"], m["reference"]["citation"])
        theme.card_close()

    # ---- exports ----
    theme.card_open("Export", "download")
    c1, c2 = st.columns(2)
    if audience == "patient":
        pdf = reports.patient_pdf(patient, prob, band, tuned, recs)
        fname = "cardioai_patient_summary.pdf"
    else:
        pdf = reports.clinician_pdf(patient, prob, band, tuned, shap_df, recs,
                                    meds, metrics)
        fname = "cardioai_clinical_report.pdf"
    with c1:
        st.download_button("Download PDF report", pdf, fname, "application/pdf",
                           use_container_width=True, key=f"pdf_{mode}")
    with c2:
        csv = reports.df_to_csv_bytes(
            shap_df[["feature", "label", "value", "shap"]])
        st.download_button("Export factors (CSV)", csv,
                           "cardioai_factors.csv", "text/csv",
                           use_container_width=True, key=f"csv_{mode}")
    theme.card_close()

    return prob, band, shap_df
