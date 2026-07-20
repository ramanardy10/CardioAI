"""PDF and CSV export for CardioAI (fpdf2 - pure Python, cloud-safe)."""

import datetime as _dt

from fpdf import FPDF

from core import config

PLUM = (74, 25, 66)        # #4A1942 - dissertation brand colour
ROSE = (214, 69, 96)
INK = (35, 30, 40)
MUTE = (110, 100, 115)


def _latin(s: str) -> str:
    return str(s).encode("latin-1", "replace").decode("latin-1")


class _Report(FPDF):
    def __init__(self, title):
        super().__init__()
        self.title_text = title
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        self.set_fill_color(*PLUM)
        self.rect(0, 0, 210, 24, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 15)
        self.set_xy(12, 7)
        self.cell(0, 8, _latin(f"{config.APP_NAME}  |  {self.title_text}"))
        self.set_font("helvetica", "", 9)
        self.set_xy(12, 15)
        self.cell(0, 5, _latin(config.INSTITUTION))
        self.set_y(30)

    def footer(self):
        self.set_y(-14)
        self.set_font("helvetica", "I", 7.5)
        self.set_text_color(*MUTE)
        self.multi_cell(0, 3.6, _latin(config.DISCLAIMER))

    def h2(self, text):
        self.ln(2)
        self.set_font("helvetica", "B", 12)
        self.set_text_color(*PLUM)
        self.cell(0, 8, _latin(text), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*PLUM)
        self.line(self.get_x(), self.get_y(), 198, self.get_y())
        self.ln(2)

    def body(self, text, size=10):
        self.set_font("helvetica", "", size)
        self.set_text_color(*INK)
        self.multi_cell(0, 5, _latin(text))
        self.ln(1)

    def kv(self, key, value):
        key_w = 68
        self.set_font("helvetica", "B", 9.5)
        self.set_text_color(*INK)
        x, y = self.get_x(), self.get_y()
        self.multi_cell(key_w, 5.5, _latin(key))
        end_y = self.get_y()
        self.set_xy(x + key_w, y)
        self.set_font("helvetica", "", 9.5)
        avail = self.w - self.r_margin - (x + key_w)
        self.multi_cell(avail, 5.5, _latin(value))
        self.set_y(max(end_y, self.get_y()))


def _risk_block(pdf, prob, band, threshold):
    colour = {"Low": (34, 139, 94), "Elevated": (196, 138, 24),
              "High": ROSE}.get(band, INK)
    pdf.set_fill_color(*colour)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 11, _latin(f"  Predicted risk: {prob:.1%}   |   Band: {band}"),
             fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_text_color(*MUTE)
    pdf.set_font("helvetica", "I", 8.5)
    pdf.multi_cell(0, 4.2, _latin(
        f"Risk band uses the dissertation's tuned operating point "
        f"({threshold:.4f}, targeting 80% recall) alongside the standard 0.50 "
        f"threshold. Elevated = above tuned threshold; High = above 0.50."))
    pdf.ln(2)


def clinician_pdf(patient, prob, band, threshold, shap_df, recs, meds,
                  metrics) -> bytes:
    pdf = _Report("Clinical Risk Report")
    pdf.add_page()
    pdf.body(f"Generated: {_dt.datetime.now():%d %b %Y, %H:%M}    "
             f"Model: {metrics['model_name']} (ROC-AUC {metrics['roc_auc']:.2%})",
             size=9)
    _risk_block(pdf, prob, band, threshold)

    pdf.h2("Patient inputs")
    for k, v in patient.items():
        pdf.kv(config.label_for(k), str(v))

    pdf.h2("Top contributing factors (SHAP)")
    pdf.body("Positive values push risk up; negative values pull it down. "
             "Contributions are specific to this patient.", size=9)
    for _, row in shap_df.head(8).iterrows():
        sign = "+" if row["shap"] >= 0 else "-"
        pdf.kv(f"{row['label']} ({row['value']})",
               f"{sign}{abs(row['shap']):.3f}")

    pdf.h2("Guideline-anchored recommendations")
    for r in recs:
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(*INK)
        pdf.cell(0, 6, _latin("- " + r["title"]), new_x="LMARGIN", new_y="NEXT")
        pdf.body(r["advice"], size=9)
        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(*MUTE)
        pdf.multi_cell(0, 4, _latin("Ref: " + r["reference"]["citation"]))
        pdf.ln(1)

    if meds:
        pdf.h2("Medication discussion points (clinician use only)")
        pdf.body("Guideline anchors for the clinical conversation - not "
                 "prescribing recommendations.", size=9)
        for m in meds:
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(*INK)
            pdf.cell(0, 6, _latin("- " + m["topic"]), new_x="LMARGIN", new_y="NEXT")
            pdf.body(m["point"], size=9)
            pdf.set_font("helvetica", "I", 8)
            pdf.set_text_color(*MUTE)
            pdf.multi_cell(0, 4, _latin("Ref: " + m["reference"]["citation"]))
            pdf.ln(1)

    return bytes(pdf.output())


def patient_pdf(patient, prob, band, threshold, recs) -> bytes:
    pdf = _Report("Your Heart Health Summary")
    pdf.add_page()
    pdf.body(f"Generated: {_dt.datetime.now():%d %b %Y, %H:%M}", size=9)
    _risk_block(pdf, prob, band, threshold)

    pdf.h2("What this means")
    meaning = {
        "Low": ("Based on the answers you gave, the model places you in the "
                "lower-risk group. This is encouraging, but it is a "
                "statistical estimate - keep up healthy habits and routine "
                "checkups."),
        "Elevated": ("Based on your answers, the model places you above its "
                     "sensitive screening threshold. This does not mean you "
                     "have heart disease - it means a conversation with your "
                     "doctor about your heart health is worthwhile."),
        "High": ("Based on your answers, the model places you in its "
                 "higher-risk group. Please arrange a review with your "
                 "doctor, who can measure your actual risk factors properly. "
                 "This tool cannot diagnose any condition."),
    }
    pdf.body(meaning.get(band, ""))

    pdf.h2("Healthy habits that matter for you")
    for r in recs:
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(*INK)
        pdf.cell(0, 6, _latin("- " + r["title"]), new_x="LMARGIN", new_y="NEXT")
        pdf.body(r["advice"], size=9)

    pdf.h2("Your answers")
    for k, v in patient.items():
        pdf.kv(config.label_for(k), str(v))
    return bytes(pdf.output())


def df_to_csv_bytes(df) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
