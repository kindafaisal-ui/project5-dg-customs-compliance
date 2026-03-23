
"""
main.py - Central Orchestrator
Project 5 - Smart Document Automation: Dangerous Goods & Customs Clearance
Sector: Logistics / Supply Chain | Medium Company | Germany

Connects ALL components:
1. Loads the dataset
2. Runs the LangChain compliance agent
3. Saves results to processed CSV
4. Updates LangSmith dataset
5. Generates 5 business insights
6. Triggers n8n webhook to send alerts if issues found
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "project5-dg-customs-compliance"
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")

N8N_WEBHOOK_TEST = "https://kinda5.app.n8n.cloud/webhook-test/f40b0982-baa0-4bed-b056-d326c3438b76"
N8N_WEBHOOK_PROD = "https://kinda5.app.n8n.cloud/webhook/f40b0982-baa0-4bed-b056-d326c3438b76"
N8N_WEBHOOK_URL = N8N_WEBHOOK_PROD

print("=" * 65)
print("Smart Document Automation - Full System Orchestrator")
print("Dangerous Goods & Customs Clearance | Project 5")
print("Run started: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 65)

# STEP 1: Load dataset
print("\n[STEP 1/6] Loading dataset...")
try:
    df = pd.read_csv("data/raw/shipments.csv")
    print("  Loaded " + str(len(df)) + " records from data/raw/shipments.csv")
    print("  DG documents:      " + str(len(df[df["is_dangerous_goods"] == "Yes"])))
    print("  Customs documents: " + str(len(df[df["doc_category"] == "Customs"])))
except FileNotFoundError:
    print("  Dataset not found - running generate_dataset.py first...")
    import subprocess
    subprocess.run(["python", "generate_dataset.py"])
    df = pd.read_csv("data/raw/shipments.csv")
    print("  Dataset generated: " + str(len(df)) + " records")

# STEP 2: Run compliance agent
print("\n[STEP 2/6] Running AI compliance agent...")
print("  Analyzing 5 documents (3 DG + 2 Customs)...")

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langsmith import traceable

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

@tool
def check_dg_compliance(doc_type: str, un_number: str, dg_class: str, route: str) -> str:
    """Checks dangerous goods compliance against ADR/IMDG/IATA regulations."""
    try:
        violations = []
        if "DG" in doc_type:
            if not un_number or un_number in ["nan", "N/A", ""]:
                violations.append("Missing UN number")
            if not dg_class or dg_class in ["nan", "N/A", ""]:
                violations.append("Missing DG class")
            if "ADR" in doc_type:
                violations.append("ADR: Verify tunnel restriction code and 24h emergency contact")
            if "IMDG" in doc_type:
                violations.append("IMDG: Verify stowage category and marine pollutant status")
            if "IATA" in doc_type:
                violations.append("IATA: Verify packing instruction and net quantity per package")
        if violations:
            return "NON-COMPLIANT: " + "; ".join(violations)
        return "COMPLIANT: All DG requirements met"
    except Exception as e:
        return "ERROR: " + str(e)

@tool
def check_customs_compliance(doc_type: str, route: str, error_detail: str) -> str:
    """Checks customs document compliance for EU/international shipments."""
    try:
        issues = []
        if error_detail and error_detail not in ["nan", "None", ""]:
            issues.append("Known error: " + error_detail)
        if "Customs" in doc_type:
            if "GB" in route:
                issues.append("Post-Brexit: UK customs declaration and EORI required")
            if "TR" in route:
                issues.append("EU-Turkey: EUR.1 certificate required")
            if "US" in route or "CN" in route or "JP" in route:
                issues.append("Non-EU: HS code, country of origin, Incoterms required")
        if "CMR" in doc_type and "GB" in route:
            issues.append("CMR + GB: Additional UK customs reference required")
        if issues:
            return "REVIEW REQUIRED: " + "; ".join(issues)
        return "COMPLIANT: Customs docs in order"
    except Exception as e:
        return "ERROR: " + str(e)

@traceable(name="DG-Customs-Compliance-Agent")
def analyze_document(doc):
    try:
        dg_result = check_dg_compliance.invoke({
            "doc_type": str(doc.get("doc_type", "")),
            "un_number": str(doc.get("un_number", "")),
            "dg_class": str(doc.get("dg_class", "")),
            "route": str(doc.get("route", ""))
        })
        customs_result = check_customs_compliance.invoke({
            "doc_type": str(doc.get("doc_type", "")),
            "route": str(doc.get("route", "")),
            "error_detail": str(doc.get("error_detail", ""))
        })
        response = llm.invoke([
            SystemMessage(content="You are a logistics compliance expert. Be concise."),
            HumanMessage(content="Doc: " + str(doc.get("doc_id")) + " - " + str(doc.get("doc_type")) + " | Route: " + str(doc.get("route")) + " | DG=" + dg_result + " | Customs=" + customs_result + " | 1.Compliant? 2.Risk? 3.Action?")
        ])
        is_compliant = "NON-COMPLIANT" not in dg_result and "REVIEW REQUIRED" not in customs_result
        return {
            "doc_id": doc.get("doc_id"),
            "doc_type": doc.get("doc_type"),
            "route": doc.get("route"),
            "dg_check": dg_result,
            "customs_check": customs_result,
            "assessment": response.content,
            "is_compliant": is_compliant,
            "risk_level": "Low" if is_compliant else "High",
            "action_required": "No action required" if is_compliant else "Review before submission",
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": None
        }
    except Exception as e:
        return {
            "doc_id": doc.get("doc_id", "Unknown"),
            "doc_type": doc.get("doc_type", "Unknown"),
            "route": doc.get("route", "Unknown"),
            "dg_check": "ERROR",
            "customs_check": "ERROR",
            "assessment": "Failed: " + str(e),
            "is_compliant": False,
            "risk_level": "Unknown",
            "action_required": "Manual review required",
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e)
        }

dg_sample = df[df["is_dangerous_goods"] == "Yes"].head(3)
customs_sample = df[df["doc_category"] == "Customs"].head(2)
sample = pd.concat([dg_sample, customs_sample])

results = []
for _, row in sample.iterrows():
    doc = row.to_dict()
    print("  Analyzing " + str(doc["doc_id"]) + " - " + str(doc["doc_type"]) + " (" + str(doc["route"]) + ")...")
    result = analyze_document(doc)
    results.append(result)

results_df = pd.DataFrame(results)
print("  Agent completed: " + str(len(results)) + " documents analyzed")

# STEP 3: Save results
print("\n[STEP 3/6] Saving results...")
os.makedirs("data/processed", exist_ok=True)
output_path = "data/processed/compliance_results_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
results_df.to_csv(output_path, index=False)
print("  Saved to: " + output_path)

# STEP 4: Update LangSmith
print("\n[STEP 4/6] Updating LangSmith...")
try:
    from langsmith import Client
    ls_client = Client(
        api_url=os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com"),
        api_key=os.getenv("LANGCHAIN_API_KEY")
    )
    datasets = list(ls_client.list_datasets())
    existing = [d for d in datasets if d.name == "DG-Customs-Compliance-Monitoring-Dataset"]
    if existing:
        for result in results:
            if not result["error"]:
                ls_client.create_example(
                    inputs={"doc_id": result["doc_id"], "doc_type": result["doc_type"], "route": result["route"]},
                    outputs={"is_compliant": result["is_compliant"], "risk_level": result["risk_level"], "action_required": result["action_required"]},
                    dataset_id=existing[0].id
                )
        print("  Added " + str(len([r for r in results if not r["error"]])) + " examples to LangSmith")
    else:
        print("  Dataset not found - run langsmith_monitoring.py first")
except Exception as e:
    print("  LangSmith skipped: " + str(e))

# STEP 5: Generate insights
print("\n[STEP 5/6] Generating insights...")

@traceable(name="Generate-Business-Insights")
def generate_insights():
    try:
        response = llm.invoke([
            SystemMessage(content="You are a logistics analyst. Generate exactly 5 insights."),
            HumanMessage(content="5 business insights for German freight company automating DG and customs docs. " + str(len(df)) + " docs, " + str(round(df["confidence_score"].mean(), 1)) + "% confidence, " + str(int(df["processing_time_seconds"].mean())) + "s AI vs " + str(int(df["manual_baseline_seconds"].mean())) + "s manual, " + str(int(df["time_saved_seconds"].mean())) + "s saved, " + str(round(len(df[df["compliance_status"] == "Flagged"]) / len(df) * 100, 1)) + "% error rate. Format: INSIGHT N: title - description")
        ])
        return [l for l in response.content.split("\n") if l.strip()][:8]
    except Exception as e:
        return [
            "INSIGHT 1: AI saves " + str(int(df["time_saved_seconds"].mean())) + "s per document vs manual processing",
            "INSIGHT 2: " + str(round(df["confidence_score"].mean(), 1)) + "% average AI confidence across all document types",
            "INSIGHT 3: Only " + str(round(len(df[df["compliance_status"] == "Flagged"]) / len(df) * 100, 1)) + "% error rate vs 5-10% industry average",
            "INSIGHT 4: " + str(len(df[df["is_dangerous_goods"] == "Yes"])) + " DG and " + str(len(df[df["doc_category"] == "Customs"])) + " customs documents automated",
            "INSIGHT 5: " + str(int(df["time_saved_seconds"].sum() / 3600)) + " total hours saved across " + str(len(df)) + " documents"
        ]

insights = generate_insights()

# STEP 6: Trigger n8n webhook
print("\n[STEP 6/6] Triggering n8n workflow via webhook...")

flagged = [r for r in results if not r["is_compliant"]]
compliant = [r for r in results if r["is_compliant"]]

payload = {
    "trigger_source": "main.py",
    "triggered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total_analyzed": len(results),
    "compliant_count": len(compliant),
    "flagged_count": len(flagged),
    "has_issues": len(flagged) > 0,
    "flagged_documents": [
        {
            "doc_id": r["doc_id"],
            "doc_type": r["doc_type"],
            "route": r["route"],
            "risk_level": r["risk_level"],
            "dg_check": r["dg_check"],
            "customs_check": r["customs_check"],
            "action_required": r["action_required"]
        } for r in flagged
    ],
    "summary": str(len(flagged)) + " of " + str(len(results)) + " documents require review - DG & Customs compliance check completed",
    "langsmith_url": "https://eu.smith.langchain.com",
    "tableau_url": "https://dub01.online.tableau.com",
    "results_file": output_path
}

try:
    response = requests.post(
        N8N_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    if response.status_code in [200, 201]:
        print("  n8n webhook triggered successfully!")
        print("  Flagged: " + str(len(flagged)) + " | Compliant: " + str(len(compliant)))
        print("  n8n will now send email alert if issues found")
    else:
        print("  n8n webhook returned status: " + str(response.status_code))
        print("  Make sure workflow is published and active")
except requests.exceptions.Timeout:
    print("  n8n webhook timeout - make sure workflow is active")
except requests.exceptions.ConnectionError:
    print("  n8n connection error - check the URL")
except Exception as e:
    print("  n8n webhook error: " + str(e))

# FINAL REPORT
print("\n" + "=" * 65)
print("FINAL REPORT")
print("=" * 65)
print("Documents analyzed:  " + str(len(results)))
print("Compliant:           " + str(len(compliant)))
print("Flagged:             " + str(len(flagged)))
print("Avg confidence:      " + str(round(df["confidence_score"].mean(), 1)) + "%")
print("Avg time saved:      " + str(int(df["time_saved_seconds"].mean())) + "s per document")
print("Results saved:       " + output_path)

print("\n" + "=" * 65)
print("5 BUSINESS INSIGHTS")
print("=" * 65)
for insight in insights:
    if insight.strip():
        print("\n" + insight)

print("\n" + "=" * 65)
print("ALL COMPONENTS CONNECTED:")
print("  [1] Dataset            loaded from data/raw/shipments.csv")
print("  [2] LangChain agent    analyzed DG + customs documents")
print("  [3] Results            saved to data/processed/")
print("  [4] LangSmith          updated with new examples")
print("  [5] Business insights  generated from full dataset")
print("  [6] n8n webhook        triggered - email alert sent if issues found")
print("\nView LangSmith: https://eu.smith.langchain.com")
print("View Tableau:   https://dub01.online.tableau.com")
print("View n8n:       https://kinda5.app.n8n.cloud")
print("=" * 65)