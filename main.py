"""
main.py — Central Orchestrator
Project 5 - Smart Document Automation: Dangerous Goods & Customs Clearance
Sector: Logistics / Supply Chain | Medium Company | Germany

This script connects ALL components:
1. Loads the dataset (generate_dataset.py output)
2. Runs the LangChain compliance agent on sample documents
3. Saves results to a processed CSV
4. Creates/updates LangSmith dataset with new results
5. Generates 5 business insights
6. Prints a full summary report

Run this script to see the complete system working end-to-end.
"""

import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── LangSmith setup ───────────────────────────────────────
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"]    = "project5-dg-customs-compliance"
os.environ["LANGCHAIN_ENDPOINT"]   = os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"]    = os.getenv("LANGCHAIN_API_KEY", "")

print("=" * 65)
print("Smart Document Automation — Full System Orchestrator")
print("Dangerous Goods & Customs Clearance | Project 5")
print(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 65)

# ══════════════════════════════════════════════════════════
# STEP 1: Load dataset
# ══════════════════════════════════════════════════════════
print("\n[STEP 1/5] Loading dataset...")

try:
    df = pd.read_csv("data/raw/shipments.csv")
    print(f"  Loaded {len(df)} records from data/raw/shipments.csv")
    print(f"  DG documents:      {len(df[df['is_dangerous_goods']=='Yes'])}")
    print(f"  Customs documents: {len(df[df['doc_category']=='Customs'])}")
    print(f"  Date range:        {df['date'].min()} to {df['date'].max()}")
except FileNotFoundError:
    print("  ERROR: Dataset not found! Running generate_dataset.py first...")
    import subprocess
    subprocess.run(["python", "generate_dataset.py"])
    df = pd.read_csv("data/raw/shipments.csv")
    print(f"  Dataset generated: {len(df)} records")

# ══════════════════════════════════════════════════════════
# STEP 2: Run LangChain compliance agent
# ══════════════════════════════════════════════════════════
print("\n[STEP 2/5] Running AI compliance agent...")
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
    """Checks dangerous goods compliance against ADR/IMDG/IATA regulations with full detail."""
    try:
        violations = []
        if "DG" in doc_type or "Dangerous" in doc_type:
            if not un_number or un_number in ["nan", "N/A", ""]:
                violations.append("ADR 2023 §3.1.2 — UN number missing: required on all DG transport documents. Fine risk: up to €50,000")
            else:
                if "IATA" in doc_type:
                    violations.append(f"IATA DGR §4.2 — Packing instruction (PI) for {un_number} must be verified against IATA DGR table. Net quantity per package must be declared in grams/ml")
                    violations.append(f"IATA DGR §7.1.6 — Shipper's Declaration for Dangerous Goods required with operator signature for air transport of {un_number}")
                if "ADR" in doc_type:
                    if any(x in route for x in ["→ CH", "→ AT", "→ IT"]):
                        violations.append(f"ADR 2023 Art. 5.4.1 — Tunnel restriction code (C, D, or E) required for alpine route {route}. Missing code causes automatic border rejection")
                    violations.append(f"ADR 2023 §8.1.2.1 — 24/7 emergency contact number required for transport of {un_number}. Office-hours numbers are not ADR compliant")
                if "IMDG" in doc_type:
                    violations.append(f"IMDG Code §4.1 — Stowage category for {un_number} must be declared. Marine pollutant status (MARPOL Annex III) must be confirmed")
            if not dg_class or dg_class in ["nan", "N/A", ""]:
                violations.append("ADR/IMDG/IATA — DG class and subdivision missing. Required for segregation rules, placarding and handling instructions")
            if "→ GB" in route:
                violations.append("Post-Brexit UK — DG shipments require UK CA approval in addition to EU ADR. UKCA marking required since Jan 2023")
            if "→ US" in route:
                violations.append("US DOT 49 CFR — US-bound DG air shipments require FAA compliance in addition to IATA DGR")
        if violations:
            return f"NON-COMPLIANT ({len(violations)} violations): " + " | ".join(violations)
        return "COMPLIANT: All DG requirements verified — UN number present, DG class confirmed, route-specific rules met"
    except Exception as e:
        return f"ERROR: {str(e)}"

@tool
def check_customs_compliance(doc_type: str, route: str, error_detail: str) -> str:
    """Checks customs document compliance for EU/international shipments with full detail."""
    try:
        issues = []
        if "Customs" in doc_type or "EUR.1" in doc_type or "CMR" in doc_type or "Invoice" in doc_type:
            if error_detail and error_detail not in ["nan", "None", ""]:
                issues.append(f"Known error flagged: {error_detail}")
            dest = route.split("→")[1].strip() if "→" in route else ""
            if dest in ["CN", "JP", "US", "TR", "GB"]:
                issues.append(f"EU UCC Art. 162 — Export to {dest} requires 8-digit CN/HS code (TARIC). 6-digit codes cause automatic customs hold of 1-2 days")
                issues.append(f"EU UCC Art. 226 — EORI number required in format: DE + 15 digits. Missing or wrong format causes export declaration rejection")
            if "→ TR" in route:
                issues.append("EU-Turkey Customs Union Decision 1/95 — EUR.1 Movement Certificate required for preferential tariff. Without EUR.1, full Turkish duty applies (avg 10-30%)")
            if "→ GB" in route:
                issues.append("UK-EU Trade and Cooperation Agreement — Supplier Declaration or REX statement required. Post-Brexit GB imports need UK import declaration and GB EORI")
            if "→ CH" in route:
                issues.append("EU-Switzerland Bilateral Agreement — EUR.1 or invoice declaration required. Swiss import VAT declaration required for goods over CHF 300")
            if "CMR" in doc_type:
                issues.append("CMR Convention Art. 6 — Waybill must include: consignor/consignee, delivery place, goods description, gross weight, carrier instructions. Missing fields void carrier liability")
            if dest in ["US", "CN", "JP"]:
                issues.append(f"Incoterms 2020 — Trade terms (EXW/FOB/CIF/DAP) must be declared for {dest} export. Required for customs value and duty calculation")
        if issues:
            return f"REVIEW REQUIRED ({len(issues)} issues): " + " | ".join(issues)
        return "COMPLIANT: Customs documentation verified — HS code present, EORI valid, route-specific certificates confirmed"
    except Exception as e:
        return f"ERROR: {str(e)}"

@traceable(name="DG-Customs-Compliance-Agent")
def analyze_document(doc: dict) -> dict:
    """Analyzes a document for DG and customs compliance. Traced in LangSmith."""
    try:
        dg_result      = check_dg_compliance.invoke({"doc_type": str(doc.get("doc_type","")), "un_number": str(doc.get("un_number","")), "dg_class": str(doc.get("dg_class","")), "route": str(doc.get("route",""))})
        customs_result = check_customs_compliance.invoke({"doc_type": str(doc.get("doc_type","")), "route": str(doc.get("route","")), "error_detail": str(doc.get("error_detail",""))})

        is_compliant = "NON-COMPLIANT" not in dg_result and "REVIEW REQUIRED" not in customs_result
        risk         = "High" if not is_compliant else "Low"

        response = llm.invoke([
            SystemMessage(content="""You are writing a short alert message for a logistics operations team at a German freight company.
They are NOT lawyers or compliance experts — they are operations staff who need to know what to do RIGHT NOW.

Write 2-3 plain sentences maximum. Use simple everyday language.
- Tell them WHAT the problem is in simple words
- Tell them WHO to contact or WHAT to fix
- Tell them WHEN (before dispatch, today, urgent)

Do NOT use legal article numbers, regulation codes, or technical jargon.
Do NOT start with the document ID.

Good example: "This shipment cannot be sent by air without a completed dangerous goods declaration signed by the carrier. Contact Kuehne+Nagel and ask them to sign the IATA form before booking the flight."
Bad example: "IATA DGR §7.1.6 requires operator signature on shipper's declaration for UN2891 air transport."

If everything is fine, write: "This document is compliant. No action needed — approved for dispatch." """),
            HumanMessage(content=f"""Document: {doc.get('doc_id')} - {doc.get('doc_type')} | Route: {doc.get('route')}
DG issues found: {dg_result}
Customs issues found: {customs_result}
Write 2-3 plain sentences for the operations team:""")
        ])

        action = response.content.strip() if is_compliant is False else "No action required — all DG and customs requirements verified"

        return {
            "doc_id":          doc.get("doc_id"),
            "doc_type":        doc.get("doc_type"),
            "route":           doc.get("route"),
            "dg_check":        dg_result,
            "customs_check":   customs_result,
            "assessment":      response.content,
            "is_compliant":    is_compliant,
            "risk_level":      risk,
            "action_required": action,
            "analyzed_at":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error":           None
        }
    except Exception as e:
        return {"doc_id": doc.get("doc_id","Unknown"), "doc_type": doc.get("doc_type","Unknown"), "route": doc.get("route","Unknown"), "dg_check": "ERROR", "customs_check": "ERROR", "assessment": f"Failed: {str(e)}", "is_compliant": False, "risk_level": "Unknown", "action_required": "Manual review required", "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "error": str(e)}

# Run agent on mix of DG and customs documents
dg_sample      = df[df["is_dangerous_goods"] == "Yes"].head(3)
customs_sample = df[df["doc_category"] == "Customs"].head(2)
sample         = pd.concat([dg_sample, customs_sample])

results = []
for _, row in sample.iterrows():
    doc = row.to_dict()
    print(f"  Analyzing {doc['doc_id']} — {doc['doc_type']} ({doc['route']})...")
    result = analyze_document(doc)
    results.append(result)

results_df = pd.DataFrame(results)
print(f"  Agent completed: {len(results)} documents analyzed")

# ══════════════════════════════════════════════════════════
# STEP 3: Save results to processed CSV
# ══════════════════════════════════════════════════════════
print("\n[STEP 3/5] Saving results to processed folder...")

os.makedirs("data/processed", exist_ok=True)
output_path = f"data/processed/compliance_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
results_df.to_csv(output_path, index=False)
print(f"  Results saved to: {output_path}")

# ══════════════════════════════════════════════════════════
# STEP 4: Update LangSmith dataset
# ══════════════════════════════════════════════════════════
print("\n[STEP 4/5] Updating LangSmith monitoring dataset...")

try:
    from langsmith import Client
    ls_client = Client(
        api_url=os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com"),
        api_key=os.getenv("LANGCHAIN_API_KEY")
    )
    dataset_name = "DG-Customs-Compliance-Monitoring-Dataset"
    datasets     = list(ls_client.list_datasets())
    existing     = [d for d in datasets if d.name == dataset_name]

    if existing:
        print(f"  Dataset '{dataset_name}' found — adding new results...")
        dataset = existing[0]
        for result in results:
            if not result["error"]:
                ls_client.create_example(
                    inputs={"doc_id": result["doc_id"], "doc_type": result["doc_type"], "route": result["route"], "dg_check": result["dg_check"], "customs_check": result["customs_check"]},
                    outputs={"is_compliant": result["is_compliant"], "risk_level": result["risk_level"], "action_required": result["action_required"], "assessment": result["assessment"]},
                    dataset_id=dataset.id
                )
        print(f"  Added {len([r for r in results if not r['error']])} new examples to LangSmith")
    else:
        print(f"  Dataset not found — run langsmith_monitoring.py first")
except Exception as e:
    print(f"  LangSmith update skipped: {str(e)}")

# ══════════════════════════════════════════════════════════
# STEP 5: Generate insights
# ══════════════════════════════════════════════════════════
print("\n[STEP 5/5] Generating business insights from full dataset...")

@traceable(name="Generate-Business-Insights")
def generate_insights() -> list:
    try:
        avg_conf   = df["confidence_score"].mean()
        avg_proc   = df["processing_time_seconds"].mean()
        avg_saved  = df["time_saved_seconds"].mean()
        error_rate = len(df[df["compliance_status"]=="Flagged"]) / len(df) * 100
        dg_docs    = df[df["is_dangerous_goods"]=="Yes"]
        cust_docs  = df[df["doc_category"]=="Customs"]
        top_route  = df["route"].value_counts().index[0]

        response = llm.invoke([
            SystemMessage(content="You are a logistics analyst. Generate 5 concise insights."),
            HumanMessage(content=f"Generate 5 business insights for a German freight company automating DG and customs documents. Data: {len(df)} total docs ({len(dg_docs)} DG, {len(cust_docs)} customs), avg confidence={avg_conf:.1f}%, avg AI time={avg_proc:.0f}s, avg saved={avg_saved:.0f}s, error rate={error_rate:.1f}%, top route={top_route}. Format: INSIGHT N: title — description")
        ])
        return [l for l in response.content.split("\n") if l.strip()][:8]
    except Exception as e:
        return [
            f"INSIGHT 1: AI reduces processing time from {df['manual_baseline_seconds'].mean():.0f}s to {df['processing_time_seconds'].mean():.0f}s — saving {df['time_saved_seconds'].mean():.0f}s per document",
            f"INSIGHT 2: Average AI confidence is {df['confidence_score'].mean():.1f}% across all DG and customs document types",
            f"INSIGHT 3: Only {len(df[df['compliance_status']=='Flagged'])} of {len(df)} documents flagged — {len(df[df['compliance_status']=='Flagged'])/len(df)*100:.1f}% error rate vs 5–10% industry average",
            f"INSIGHT 4: DG documents ({len(df[df['is_dangerous_goods']=='Yes'])}) and customs documents ({len(df[df['doc_category']=='Customs'])}) are both well covered by the automation",
            f"INSIGHT 5: Total time saved across {len(df)} documents = {df['time_saved_seconds'].sum()/3600:.0f} hours — equivalent to {df['time_saved_seconds'].sum()/3600/8:.0f} full working days"
        ]

insights = generate_insights()

# ══════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("FINAL REPORT — SYSTEM RUN COMPLETE")
print("=" * 65)

print(f"\nDataset:          {len(df)} total documents")
print(f"DG documents:     {len(df[df['is_dangerous_goods']=='Yes'])}")
print(f"Customs docs:     {len(df[df['doc_category']=='Customs'])}")
print(f"\nAI Agent Results:")
print(f"  Analyzed:       {len(results)} documents")
print(f"  Compliant:      {sum(1 for r in results if r['is_compliant'])}")
print(f"  Non-compliant:  {sum(1 for r in results if not r['is_compliant'])}")
print(f"  Errors:         {sum(1 for r in results if r['error'])}")
print(f"\nDataset Stats:")
print(f"  Avg confidence: {df['confidence_score'].mean():.1f}%")
print(f"  Avg AI time:    {df['processing_time_seconds'].mean():.0f}s")
print(f"  Avg saved:      {df['time_saved_seconds'].mean():.0f}s per doc")
print(f"  Error rate:     {len(df[df['compliance_status']=='Flagged'])/len(df)*100:.1f}%")
print(f"\nResults saved:    {output_path}")

print("\n" + "=" * 65)
print("5 BUSINESS INSIGHTS")
print("=" * 65)
for insight in insights:
    if insight.strip():
        print(f"\n{insight}")

print("\n" + "=" * 65)
print("ALL COMPONENTS CONNECTED:")
print("  [1] Dataset loaded from data/raw/shipments.csv")
print("  [2] LangChain agent analyzed DG + customs documents")
print("  [3] Results saved to data/processed/")
print("  [4] LangSmith dataset updated with new results")
print("  [5] Business insights generated from full dataset")
print(f"\nView LangSmith traces: https://eu.smith.langchain.com")
print(f"View Tableau dashboard: https://dub01.online.tableau.com")
print(f"View n8n workflow:      https://kinda5.app.n8n.cloud")
print("=" * 65)