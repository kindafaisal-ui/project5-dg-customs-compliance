"""
LangSmith Dataset Creation & Monitoring Setup
Project 5 - Smart Document Automation: Dangerous Goods & Customs Clearance
"""

import os
import pandas as pd
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

# ── LangSmith configuration ───────────────────────────────
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"]    = "project5-dg-customs-compliance"
os.environ["LANGCHAIN_ENDPOINT"]   = os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"]    = os.getenv("LANGCHAIN_API_KEY", "")

# ── Load dataset ──────────────────────────────────────────
df = pd.read_csv("data/raw/shipments.csv")

def create_monitoring_dataset():
    """
    Creates a LangSmith dataset with both DG and customs documents
    for monitoring AI compliance checks.
    """
    ls_client = Client(
        api_url=os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com"),
        api_key=os.getenv("LANGCHAIN_API_KEY")
    )

    dataset_name = "DG-Customs-Compliance-Monitoring-Dataset"

    print("=" * 60)
    print("LangSmith Dataset Creation & Monitoring Setup")
    print("Covers: Dangerous Goods + Customs Clearance Documents")
    print("=" * 60)

    # Check if dataset exists
    datasets = list(ls_client.list_datasets())
    existing = [d for d in datasets if d.name == dataset_name]

    if existing:
        print(f"\nDataset '{dataset_name}' already exists!")
        dataset = existing[0]
    else:
        dataset = ls_client.create_dataset(
            dataset_name=dataset_name,
            description="Shipment documents for DG & Customs compliance monitoring — Project 5"
        )
        print(f"\nDataset '{dataset_name}' created!")

    print("\nAdding examples — both DG and Customs documents...")

    # DG documents — flagged
    dg_flagged = df[(df["is_dangerous_goods"] == "Yes") & (df["compliance_status"] == "Flagged")].head(3)

    # DG documents — human review
    dg_review = df[(df["is_dangerous_goods"] == "Yes") & (df["compliance_status"] == "Human review")].head(3)

    # Customs documents — flagged
    customs_flagged = df[(df["doc_category"] == "Customs") & (df["compliance_status"] == "Flagged")].head(2)

    # Customs documents — human review
    customs_review = df[(df["doc_category"] == "Customs") & (df["compliance_status"] == "Human review")].head(3)

    # Auto-approved baseline
    approved = df[df["compliance_status"] == "Auto-approved"].head(4)

    all_samples = pd.concat([dg_flagged, dg_review, customs_flagged, customs_review, approved])

    for _, row in all_samples.iterrows():
        ls_client.create_example(
            inputs={
                "doc_id":            row["doc_id"],
                "doc_type":          row["doc_type"],
                "doc_category":      row["doc_category"],
                "route":             row["route"],
                "dg_class":          str(row.get("dg_class", "")),
                "un_number":         str(row.get("un_number", "")),
                "compliance_status": row["compliance_status"],
                "error_detail":      str(row.get("error_detail", "")),
                "confidence_score":  float(row["confidence_score"]),
                "is_dangerous_goods": row["is_dangerous_goods"],
                "carrier":           row["carrier"],
            },
            outputs={
                "expected_status":   row["compliance_status"],
                "expected_action":   "Review and correct" if row["compliance_status"] != "Auto-approved" else "No action required",
                "risk_level":        "High" if row["compliance_status"] == "Flagged" else "Medium" if row["compliance_status"] == "Human review" else "Low",
                "doc_type_category": "Dangerous Goods" if row["is_dangerous_goods"] == "Yes" else "Customs/Transport"
            },
            dataset_id=dataset.id
        )

    print(f"\nAdded {len(all_samples)} examples:")
    print(f"  DG Flagged:        {len(dg_flagged)}")
    print(f"  DG Human Review:   {len(dg_review)}")
    print(f"  Customs Flagged:   {len(customs_flagged)}")
    print(f"  Customs Review:    {len(customs_review)}")
    print(f"  Auto-approved:     {len(approved)}")

    # Summary
    print("\n" + "=" * 60)
    print("Dataset Summary")
    print("=" * 60)
    print(f"Dataset name:       {dataset_name}")
    print(f"Total examples:     {len(all_samples)}")
    print(f"Dataset ID:         {dataset.id}")

    print(f"\nFull dataset breakdown:")
    print(f"  Total records:    {len(df)}")
    print(f"  DG documents:     {len(df[df['is_dangerous_goods']=='Yes'])}")
    print(f"  Customs docs:     {len(df[df['doc_category']=='Customs'])}")

    print(f"\nCompliance breakdown:")
    print(df["compliance_status"].value_counts().to_string())

    print(f"\nDoc type breakdown:")
    print(df["doc_type"].value_counts().to_string())

    print(f"\nAverage confidence: {df['confidence_score'].mean():.1f}%")
    print(f"Error rate:         {len(df[df['compliance_status']=='Flagged'])/len(df)*100:.1f}%")
    print(f"\nView at: https://eu.smith.langchain.com")
    print("=" * 60)

    return dataset

if __name__ == "__main__":
    create_monitoring_dataset()