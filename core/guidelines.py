"""Evidence-based guidance content for CardioAI.

Lifestyle recommendations are mapped to the modifiable risk factors captured
by the model's input schema. Medication content is restricted to Clinical
Mode, framed strictly as guideline-anchored discussion points - CardioAI
never recommends prescribing decisions.

References are to the European Society of Cardiology (ESC) guideline corpus.
"""

ESC_REFERENCES = [
    {
        "id": "ESC-Prev-2021",
        "citation": ("Visseren, F.L.J. et al. (2021) '2021 ESC Guidelines on "
                     "cardiovascular disease prevention in clinical practice', "
                     "European Heart Journal, 42(34), pp. 3227-3337."),
        "doi": "10.1093/eurheartj/ehab484",
    },
    {
        "id": "SCORE2-2021",
        "citation": ("SCORE2 Working Group and ESC Cardiovascular Risk "
                     "Collaboration (2021) 'SCORE2 risk prediction algorithms: "
                     "new models to estimate 10-year risk of cardiovascular "
                     "disease in Europe', European Heart Journal, 42(25), "
                     "pp. 2439-2454."),
        "doi": "10.1093/eurheartj/ehab309",
    },
    {
        "id": "ESC-Diabetes-2023",
        "citation": ("Marx, N. et al. (2023) '2023 ESC Guidelines for the "
                     "management of cardiovascular disease in patients with "
                     "diabetes', European Heart Journal, 44(39), pp. 4043-4140."),
        "doi": "10.1093/eurheartj/ehad192",
    },
    {
        "id": "ESC-BP-2024",
        "citation": ("McEvoy, J.W. et al. (2024) '2024 ESC Guidelines for the "
                     "management of elevated blood pressure and hypertension', "
                     "European Heart Journal, 45(38), pp. 3912-4018."),
        "doi": "10.1093/eurheartj/ehae178",
    },
]


def _ref(rid):
    return next(r for r in ESC_REFERENCES if r["id"] == rid)


# ---------------------------------------------------------------------------
# Lifestyle recommendations, keyed by the input feature that triggers them.
# Each item: trigger(fn of patient dict) -> bool, title, advice, reference id.
# ---------------------------------------------------------------------------
def _is_yes(v):
    return str(v).strip().lower().startswith("yes")


LIFESTYLE_RULES = [
    {
        "feature": "SmokerStatus",
        "trigger": lambda p: "smoker" in str(p.get("SmokerStatus", "")).lower()
                             and "never" not in str(p.get("SmokerStatus", "")).lower(),
        "title": "Stop smoking",
        "advice": ("Smoking cessation is the single most effective lifestyle "
                   "change for cardiovascular risk. ESC guidance recommends "
                   "complete cessation of all tobacco use, with behavioural "
                   "support and, where appropriate, pharmacological aids "
                   "discussed with a clinician."),
        "ref": "ESC-Prev-2021",
    },
    {
        "feature": "BMI",
        "trigger": lambda p: _num(p.get("BMI")) is not None and _num(p["BMI"]) >= 25,
        "title": "Work towards a healthy weight",
        "advice": ("ESC prevention guidance recommends achieving and "
                   "maintaining a healthy weight (BMI 20-25 kg/m2) through "
                   "combined dietary change and physical activity, which "
                   "favourably affects blood pressure, lipids and glucose "
                   "metabolism."),
        "ref": "ESC-Prev-2021",
    },
    {
        "feature": "PhysicalActivities",
        "trigger": lambda p: str(p.get("PhysicalActivities", "")).lower().startswith("no"),
        "title": "Build regular physical activity",
        "advice": ("Aim for at least 150-300 minutes of moderate-intensity "
                   "aerobic activity per week (or 75-150 minutes vigorous), "
                   "as recommended for all adults in ESC prevention "
                   "guidelines. Any increase from a sedentary baseline is "
                   "beneficial."),
        "ref": "ESC-Prev-2021",
    },
    {
        "feature": "SleepHours",
        "trigger": lambda p: _num(p.get("SleepHours")) is not None
                             and (_num(p["SleepHours"]) < 6 or _num(p["SleepHours"]) > 9),
        "title": "Improve sleep habits",
        "advice": ("Both short and long habitual sleep are associated with "
                   "higher cardiovascular risk. Aim for a regular 7-9 hour "
                   "sleep pattern and raise persistent sleep problems (for "
                   "example possible sleep apnoea) with a clinician."),
        "ref": "ESC-Prev-2021",
    },
    {
        "feature": "AlcoholDrinkers",
        "trigger": lambda p: _is_yes(p.get("AlcoholDrinkers")),
        "title": "Keep alcohol low",
        "advice": ("ESC prevention guidance recommends restricting alcohol "
                   "to at most 100 g of pure alcohol per week; lower is "
                   "better for blood pressure and overall cardiovascular "
                   "risk."),
        "ref": "ESC-Prev-2021",
    },
    {
        "feature": "HadDiabetes",
        "trigger": lambda p: _is_yes(p.get("HadDiabetes")),
        "title": "Structured diabetes management",
        "advice": ("Diabetes substantially raises cardiovascular risk. ESC "
                   "guidance recommends structured management combining "
                   "glycaemic control, blood pressure and lipid management, "
                   "diet and activity, coordinated with your diabetes team."),
        "ref": "ESC-Diabetes-2023",
    },
    {
        "feature": "GeneralHealth",
        "trigger": lambda p: str(p.get("GeneralHealth", "")).lower() in ("fair", "poor"),
        "title": "Book a preventive health review",
        "advice": ("Self-rated fair or poor health is a strong marker of "
                   "underlying risk. A structured cardiovascular risk review "
                   "(blood pressure, lipids, glucose) with a clinician is "
                   "recommended so risk factors can be measured, not "
                   "estimated."),
        "ref": "SCORE2-2021",
    },
]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def lifestyle_recommendations(patient: dict):
    """Recommendations triggered by this patient's inputs, each with its ESC
    reference attached."""
    out = []
    for rule in LIFESTYLE_RULES:
        try:
            hit = rule["trigger"](patient)
        except Exception:
            hit = False
        if hit:
            out.append({**rule, "reference": _ref(rule["ref"])})
    if not out:
        out.append({
            "feature": None,
            "title": "Maintain current healthy habits",
            "advice": ("No modifiable lifestyle flags were raised by the "
                       "inputs provided. Continue regular activity, a "
                       "balanced diet, not smoking and routine checkups in "
                       "line with ESC prevention guidance."),
            "reference": _ref("ESC-Prev-2021"),
        })
    return out


# ---------------------------------------------------------------------------
# Medication discussion points - Clinical Mode only. Deliberately general:
# drug classes and guideline anchors, no doses, no individual prescribing.
# ---------------------------------------------------------------------------
MEDICATION_DISCUSSION = [
    {
        "topic": "Formal risk scoring before therapy decisions",
        "point": ("CardioAI's output is a machine-learning estimate from "
                  "self-reported survey-style data. Before any treatment "
                  "decision, quantify risk with a validated clinical tool "
                  "(SCORE2 / SCORE2-OP) using measured blood pressure and "
                  "lipids."),
        "ref": "SCORE2-2021",
    },
    {
        "topic": "Lipid-lowering therapy",
        "point": ("For patients at high or very high cardiovascular risk, ESC "
                  "prevention guidelines set stepwise LDL-C goals and support "
                  "statin-based therapy, with intensification (ezetimibe, "
                  "PCSK9 inhibitors) where goals are not met. Eligibility "
                  "depends on formally scored risk, not on this model's "
                  "probability."),
        "ref": "ESC-Prev-2021",
    },
    {
        "topic": "Blood pressure management",
        "point": ("Where elevated blood pressure is confirmed by proper "
                  "measurement, the 2024 ESC guidelines describe treatment "
                  "thresholds and combination-therapy strategies. Survey "
                  "inputs used by this model do not include measured BP, so "
                  "measurement is a prerequisite."),
        "ref": "ESC-BP-2024",
    },
    {
        "topic": "Diabetes with cardiovascular risk",
        "point": ("In patients with type 2 diabetes and established "
                  "cardiovascular disease or high risk, ESC 2023 guidance "
                  "prioritises agents with proven cardiovascular benefit "
                  "(SGLT2 inhibitors, GLP-1 receptor agonists) independent "
                  "of glycaemic control considerations."),
        "ref": "ESC-Diabetes-2023",
    },
    {
        "topic": "Antiplatelet therapy",
        "point": ("Antiplatelet therapy is guideline-supported for secondary "
                  "prevention; in primary prevention it is not routine and "
                  "requires individual assessment of ischaemic versus "
                  "bleeding risk per ESC prevention guidance."),
        "ref": "ESC-Prev-2021",
    },
]


def medication_discussion():
    return [{**m, "reference": _ref(m["ref"])} for m in MEDICATION_DISCUSSION]
