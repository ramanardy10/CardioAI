"""Central configuration for CardioAI.

Single source of truth for app-wide constants, feature labels and risk-band
logic. No Streamlit imports here - keep this importable from anywhere.
"""

APP_NAME = "CardioAI"
APP_TAGLINE = "Heart disease risk prediction with explainable AI"
VERSION = "2.0.0"
INSTITUTION = "MSc Applied AI - Research Prototype"

# Fallbacks used only if metadata.json does not provide the values.
DEFAULT_TUNED_THRESHOLD = 0.1751
DEFAULT_STANDARD_THRESHOLD = 0.50
DEFAULT_ROC_AUC = 0.9387
DEFAULT_MODEL_NAME = "XGBoost"

# Dataset facts (CDC BRFSS 2020+2022 cross-wave enrichment, via Kaggle -
# Kamil Pytlak, "Indicators of Heart Disease").
DATASET_TOTAL = 469_440
DATASET_POSITIVES = 52_480
DATASET_SOURCE = (
    "CDC Behavioral Risk Factor Surveillance System (BRFSS), 2022 wave "
    "enriched with 2020 positive cases. Accessed via Kaggle "
    '(Kamil Pytlak, "Indicators of Heart Disease").'
)

ADMIN_PIN = "cardio2026"  # prototype only - not real authentication

DISCLAIMER = (
    "CardioAI is a research prototype developed for an MSc Applied AI "
    "dissertation. It is not a CE-marked medical device, has not been "
    "clinically validated, and must not be used to make medical decisions. "
    "Always consult a qualified clinician."
)

# ---------------------------------------------------------------------------
# Friendly labels & help text for known BRFSS columns. Unknown columns fall
# back to a prettified version of their raw name, so the UI never breaks if
# the artifact schema changes.
# ---------------------------------------------------------------------------
FRIENDLY_LABELS = {
    "BMI": "Body Mass Index (BMI)",
    "HeightInMeters": "Height (m)",
    "WeightInKilograms": "Weight (kg)",
    "SleepHours": "Average sleep per night (hours)",
    "PhysicalHealthDays": "Days of poor physical health (last 30)",
    "MentalHealthDays": "Days of poor mental health (last 30)",
    "AgeCategory": "Age group",
    "Sex": "Sex",
    "State": "US state (survey region)",
    "GeneralHealth": "Self-rated general health",
    "LastCheckupTime": "Time since last routine checkup",
    "PhysicalActivities": "Physical activity in past 30 days",
    "RemovedTeeth": "Teeth removed (dental health)",
    "HadAngina": "History of angina / coronary disease",
    "HadStroke": "History of stroke",
    "HadAsthma": "Asthma",
    "HadSkinCancer": "Skin cancer",
    "HadCOPD": "COPD",
    "HadDepressiveDisorder": "Depressive disorder",
    "HadKidneyDisease": "Kidney disease",
    "HadArthritis": "Arthritis",
    "HadDiabetes": "Diabetes",
    "DeafOrHardOfHearing": "Deaf or hard of hearing",
    "BlindOrVisionDifficulty": "Blindness / serious vision difficulty",
    "DifficultyConcentrating": "Difficulty concentrating",
    "DifficultyWalking": "Difficulty walking / climbing stairs",
    "DifficultyDressingBathing": "Difficulty dressing or bathing",
    "DifficultyErrands": "Difficulty doing errands alone",
    "SmokerStatus": "Smoking status",
    "ECigaretteUsage": "E-cigarette use",
    "ChestScan": "Ever had a chest CT scan",
    "RaceEthnicityCategory": "Race / ethnicity",
    "AlcoholDrinkers": "Alcohol consumption",
    "HIVTesting": "Ever tested for HIV",
    "FluVaxLast12": "Flu vaccine (last 12 months)",
    "PneumoVaxEver": "Pneumonia vaccine (ever)",
    "TetanusLast10Tdap": "Tetanus vaccine (last 10 years)",
    "HighRiskLastYear": "High-risk behaviours last year",
    "CovidPos": "Tested positive for COVID-19",
}

# Which features to surface in the simplified Patient Mode form.
PATIENT_CORE_FEATURES = [
    "AgeCategory", "Sex", "BMI", "GeneralHealth", "SmokerStatus",
    "PhysicalActivities", "SleepHours", "AlcoholDrinkers",
    "HadDiabetes", "HadAngina", "HadStroke", "DifficultyWalking",
]

# Grouping for the full clinical form.
CLINICAL_GROUPS = {
    "Demographics": ["AgeCategory", "Sex", "RaceEthnicityCategory", "State"],
    "Vitals & lifestyle": [
        "BMI", "HeightInMeters", "WeightInKilograms", "SleepHours",
        "SmokerStatus", "ECigaretteUsage", "AlcoholDrinkers",
        "PhysicalActivities",
    ],
    "General health": [
        "GeneralHealth", "PhysicalHealthDays", "MentalHealthDays",
        "LastCheckupTime", "RemovedTeeth", "ChestScan",
    ],
    "Medical history": [
        "HadAngina", "HadStroke", "HadDiabetes", "HadAsthma", "HadCOPD",
        "HadKidneyDisease", "HadArthritis", "HadSkinCancer",
        "HadDepressiveDisorder", "CovidPos",
    ],
    "Functional status": [
        "DifficultyWalking", "DifficultyConcentrating",
        "DifficultyDressingBathing", "DifficultyErrands",
        "DeafOrHardOfHearing", "BlindOrVisionDifficulty",
    ],
    "Preventive care": [
        "FluVaxLast12", "PneumoVaxEver", "TetanusLast10Tdap",
        "HIVTesting", "HighRiskLastYear",
    ],
}


def label_for(col: str) -> str:
    """Friendly label for a raw column name, with graceful fallback."""
    if col in FRIENDLY_LABELS:
        return FRIENDLY_LABELS[col]
    out = []
    for ch in col:
        if ch.isupper() and out and not out[-1].isspace():
            out.append(" ")
        out.append(ch)
    return "".join(out).strip().capitalize()


def classify_risk(prob: float, tuned: float, standard: float = 0.5):
    """Three-band classification anchored on the dissertation's dual
    operating points: tuned threshold (80% recall) and standard 0.5."""
    if prob >= standard:
        return "High", "high"
    if prob >= tuned:
        return "Elevated", "elevated"
    return "Low", "low"
