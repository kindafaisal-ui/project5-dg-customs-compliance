import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

# ── Config ────────────────────────────────────────────────
NUM_RECORDS = 500
START_DATE  = datetime(2026, 1, 1)
END_DATE    = datetime(2026, 3, 19)

# ── Reference data ────────────────────────────────────────
DOC_TYPES = {
    "Customs Export Declaration": 0.35,
    "DG Declaration (ADR)":       0.18,
    "DG Declaration (IMDG)":      0.10,
    "DG Declaration (IATA)":      0.07,
    "CMR Waybill":                0.18,
    "Commercial Invoice":         0.07,
    "EUR.1 Certificate":          0.05,
}

ROUTES = [
    "DE → PL", "DE → FR", "DE → NL", "DE → CN",
    "DE → TR", "DE → US", "DE → CH", "DE → IT",
    "DE → GB", "DE → JP",
]

DG_CLASSES = ["Class 2 (Gases)", "Class 3 (Flammable liquids)",
              "Class 4 (Flammable solids)", "Class 6 (Toxic)",
              "Class 8 (Corrosive)", "Class 9 (Misc dangerous)"]

ERROR_TYPES = [
    "UN number mismatch",
    "Invalid HS code",
    "Missing packing group",
    "Incorrect consignee address",
    "Wrong DG class",
    "Missing emergency contact",
    "Invalid EORI number",
    "Quantity mismatch",
]

CARRIERS = ["DHL Freight", "DB Schenker", "Rhenus", "Kuehne+Nagel", "DSV"]

# ── Helpers ───────────────────────────────────────────────
def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days),
                             hours=random.randint(0, 23),
                             minutes=random.randint(0, 59))

def processing_time(doc_type, is_manual_baseline=False):
    """Seconds. Manual baseline = 480-720s. AI = 20-90s."""
    if is_manual_baseline:
        return round(random.uniform(480, 720))
    base = {"Customs Export Declaration": 45,
            "DG Declaration (ADR)": 60,
            "DG Declaration (IMDG)": 65,
            "DG Declaration (IATA)": 55,
            "CMR Waybill": 30,
            "Commercial Invoice": 25,
            "EUR.1 Certificate": 35}.get(doc_type, 40)
    return round(random.gauss(base, 10))

def confidence_score(doc_type):
    """AI confidence 0-100. DG docs slightly harder."""
    is_dg = "DG" in doc_type
    mean = 88 if is_dg else 93
    score = round(random.gauss(mean, 7), 1)
    return max(50.0, min(100.0, score))

def compliance_status(conf, doc_type):
    if conf >= 90:
        return "Auto-approved"
    elif conf >= 75:
        return "Human review"
    else:
        return "Flagged"

def error_detail(status, doc_type):
    if status == "Flagged":
        if "DG" in doc_type:
            return random.choice(ERROR_TYPES[:3] + ERROR_TYPES[4:6])
        return random.choice(ERROR_TYPES[1:4] + ERROR_TYPES[6:])
    elif status == "Human review":
        return random.choice(ERROR_TYPES) if random.random() < 0.4 else ""
    return ""

def dg_class(doc_type):
    if "DG" in doc_type:
        return random.choice(DG_CLASSES)
    return ""

def un_number(doc_type):
    if "DG" in doc_type:
        return f"UN{random.randint(1000, 3500)}"
    return ""

# ── Generate records ──────────────────────────────────────
doc_type_choices = random.choices(
    list(DOC_TYPES.keys()),
    weights=list(DOC_TYPES.values()),
    k=NUM_RECORDS
)

records = []
for i, doc_type in enumerate(doc_type_choices):
    doc_id    = f"DOC-{5000 + i}"
    date      = random_date(START_DATE, END_DATE)
    week      = date.isocalendar()[1]
    month     = date.strftime("%B")
    route     = random.choice(ROUTES)
    carrier   = random.choice(CARRIERS)
    proc_time = processing_time(doc_type)
    conf      = confidence_score(doc_type)
    status    = compliance_status(conf, doc_type)
    error     = error_detail(status, doc_type)
    dg_cls    = dg_class(doc_type)
    un_num    = un_number(doc_type)
    manual_t  = processing_time(doc_type, is_manual_baseline=True)
    time_saved = manual_t - proc_time

    records.append({
        "doc_id":                  doc_id,
        "date":                    date.strftime("%Y-%m-%d"),
        "time":                    date.strftime("%H:%M"),
        "week_number":             week,
        "month":                   month,
        "doc_type":                doc_type,
        "route":                   route,
        "carrier":                 carrier,
        "processing_time_seconds": proc_time,
        "manual_baseline_seconds": manual_t,
        "time_saved_seconds":      time_saved,
        "confidence_score":        conf,
        "compliance_status":       status,
        "error_detail":            error,
        "dg_class":                dg_cls,
        "un_number":               un_num,
        "is_dangerous_goods":      "Yes" if "DG" in doc_type else "No",
        "customs_hold":            "Yes" if status == "Flagged" and random.random() < 0.4 else "No",
    })

df = pd.DataFrame(records)

# ── Derived columns ───────────────────────────────────────
df["processing_time_minutes"] = (df["processing_time_seconds"] / 60).round(2)
df["confidence_band"] = pd.cut(
    df["confidence_score"],
    bins=[0, 75, 85, 95, 100],
    labels=["<75% (Flagged)", "75-85% (Review)", "85-95% (Good)", "95-100% (Excellent)"]
)
df["doc_category"] = df["doc_type"].apply(
    lambda x: "Dangerous Goods" if "DG" in x else
              "Customs" if "Customs" in x or "EUR" in x else
              "Transport" if "CMR" in x else "Finance"
)

# ── Save ──────────────────────────────────────────────────
os.makedirs("data/raw", exist_ok=True)
output_path = "data/raw/shipments.csv"
df.to_csv(output_path, index=False)

# ── Summary ───────────────────────────────────────────────
print("=" * 50)
print("Dataset generated successfully!")
print(f"Records:     {len(df)}")
print(f"Output:      {output_path}")
print(f"Date range:  {df['date'].min()} to {df['date'].max()}")
print("=" * 50)
print("\nCompliance status breakdown:")
print(df["compliance_status"].value_counts().to_string())
print("\nDoc type breakdown:")
print(df["doc_type"].value_counts().to_string())
print("\nAverage processing time (AI):", round(df["processing_time_seconds"].mean()), "seconds")
print("Average confidence score:    ", round(df["confidence_score"].mean(), 1), "%")
print(f"Error rate:                   {round(len(df[df['compliance_status']=='Flagged'])/len(df)*100,1)}%")