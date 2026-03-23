"""
AI Compliance Agent — OpenAI + LangSmith
Project 5 - Smart Document Automation: Dangerous Goods & Customs Clearance
Sector: Logistics / Supply Chain | Medium Company | Germany
"""

import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from langsmith import traceable, Client
from langsmith.wrappers import wrap_openai

load_dotenv()

# ── LangSmith setup ───────────────────────────────────────
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"]    = "project5-dg-customs-compliance"
os.environ["LANGCHAIN_ENDPOINT"]   = os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"]    = os.getenv("LANGCHAIN_API_KEY", "")

# ── OpenAI client wrapped with LangSmith tracing ─────────
client = wrap_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

# ── Load dataset ──────────────────────────────────────────
try:
    df = pd.read_csv("data/raw/shipments.csv")
    print(f"Dataset loaded: {len(df)} records")
except FileNotFoundError:
    print("ERROR: data/raw/shipments.csv not found. Run generate_dataset.py first.")
    exit(1)

# ── Agent function — covers BOTH DG and Customs ───────────
@traceable(name="DG-Customs-Compliance-Agent")
def analyze_document(doc: dict) -> dict:
    """
    Analyzes a shipment document for BOTH:
    - Dangerous Goods (DG) compliance: ADR / IMDG / IATA DGR
    - Customs Clearance compliance: EU UCC / CMR / EUR.1 / HS codes
    Every call is traced in LangSmith for full transparency.
    """
    try:
        doc_type = str(doc.get("doc_type", ""))
        route    = str(doc.get("route", ""))
        is_dg    = doc.get("is_dangerous_goods", "No") == "Yes"

        prompt = f"""You are a compliance expert for a German international freight forwarder.
The company handles TWO types of compliance daily:
1. DANGEROUS GOODS (DG) — ADR (road), IMDG (sea), IATA DGR (air)
2. CUSTOMS CLEARANCE — EU export declarations, CMR waybills, EUR.1 certificates, HS codes

Analyze this shipment document for ALL applicable compliance issues:

Document ID:        {doc.get('doc_id')}
Document Type:      {doc_type}
Route:              {route}
Is Dangerous Goods: {doc.get('is_dangerous_goods', 'No')}
DG Class:           {doc.get('dg_class', 'N/A')}
UN Number:          {doc.get('un_number', 'N/A')}
Current Status:     {doc.get('compliance_status')}
Known Error:        {doc.get('error_detail', 'None')}
AI Confidence:      {doc.get('confidence_score')}%

{"DG COMPLIANCE CHECKS REQUIRED:" if is_dg else ""}
{"- Verify UN number is present and valid" if is_dg else ""}
{"- Verify DG class is specified (ADR classes 1-9)" if is_dg else ""}
{"- ADR: check tunnel restriction code and 24h emergency contact" if "ADR" in doc_type else ""}
{"- IMDG: check stowage category and marine pollutant status" if "IMDG" in doc_type else ""}
{"- IATA: check packing instruction and net quantity per package" if "IATA" in doc_type else ""}

CUSTOMS COMPLIANCE CHECKS REQUIRED:
{"- EU export declaration: verify EORI number, HS code (8-digit), and Incoterms" if "Customs" in doc_type else ""}
{"- CMR waybill: verify consignee details and goods description" if "CMR" in doc_type else ""}
{"- EUR.1: verify goods origin and eligible trade agreement route" if "EUR.1" in doc_type else ""}
{"- Route DE → GB: post-Brexit customs declaration required" if "GB" in route else ""}
{"- Route DE → TR: EUR.1 certificate required for EU-Turkey customs union" if "TR" in route else ""}
{"- Route DE → US/CN/JP: HS code, country of origin, and Incoterms mandatory" if any(x in route for x in ["US","CN","JP"]) else ""}

Provide a structured assessment:
1. DG Compliance: (COMPLIANT / NON-COMPLIANT / N/A — one sentence)
2. Customs Compliance: (COMPLIANT / REVIEW REQUIRED / N/A — one sentence)
3. Overall Risk Level: (Low / Medium / High)
4. Primary Concern: (DG issue / Customs issue / Both / None)
5. Action Required: (one clear sentence)"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=400,
            messages=[
                {"role": "system", "content": "You are a logistics compliance expert specializing in both dangerous goods regulations and EU customs clearance. Be concise and structured."},
                {"role": "user",   "content": prompt}
            ]
        )

        content = response.choices[0].message.content

        # Determine compliance flags
        is_dg_compliant      = "NON-COMPLIANT" not in content.upper() or "DG Compliance: COMPLIANT" in content
        is_customs_compliant = "REVIEW REQUIRED" not in content.upper() or "Customs Compliance: COMPLIANT" in content
        is_compliant         = is_dg_compliant and is_customs_compliant

        risk_level = "High" if "High" in content else "Medium" if "Medium" in content else "Low"

        return {
            "doc_id":                doc.get("doc_id"),
            "doc_type":              doc_type,
            "route":                 route,
            "is_dangerous_goods":    doc.get("is_dangerous_goods", "No"),
            "compliance_status":     doc.get("compliance_status"),
            "confidence_score":      doc.get("confidence_score"),
            "ai_assessment":         content,
            "is_compliant":          is_compliant,
            "is_dg_compliant":       is_dg_compliant,
            "is_customs_compliant":  is_customs_compliant,
            "risk_level":            risk_level,
            "action_required":       "No action required" if is_compliant else "Review and correct before submission",
            "error":                 None
        }

    except Exception as e:
        return {
            "doc_id":               doc.get("doc_id", "Unknown"),
            "doc_type":             doc.get("doc_type", "Unknown"),
            "route":                doc.get("route", "Unknown"),
            "is_dangerous_goods":   doc.get("is_dangerous_goods", "Unknown"),
            "compliance_status":    "ERROR",
            "confidence_score":     0,
            "ai_assessment":        f"Analysis failed: {str(e)}",
            "is_compliant":         False,
            "is_dg_compliant":      False,
            "is_customs_compliant": False,
            "risk_level":           "Unknown",
            "action_required":      "Manual review required due to analysis error",
            "error":                str(e)
        }


# ── Main ──────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("Smart Document Automation Agent")
    print("Dangerous Goods & Customs Clearance Compliance")
    print("Monitored by LangSmith | Project 5")
    print("=" * 65)

    # Analyze mix of DG and customs documents
    dg_sample      = df[df["is_dangerous_goods"] == "Yes"].head(3)
    customs_sample = df[df["doc_category"] == "Customs"].head(2)
    sample         = pd.concat([dg_sample, customs_sample])

    print(f"\nAnalyzing {len(sample)} documents (3 DG + 2 Customs)...")
    results = []

    for _, row in sample.iterrows():
        doc = row.to_dict()
        print(f"\n  {doc['doc_id']} — {doc['doc_type']} ({doc['route']})")
        result = analyze_document(doc)
        results.append(result)

        if result["error"]:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Risk:      {result['risk_level']}")
            print(f"  Compliant: {result['is_compliant']}")
            print(f"  Action:    {result['action_required']}")

    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print(f"Documents analyzed:  {len(results)}")
    print(f"Fully compliant:     {sum(1 for r in results if r['is_compliant'])}")
    print(f"DG issues:           {sum(1 for r in results if not r.get('is_dg_compliant', True))}")
    print(f"Customs issues:      {sum(1 for r in results if not r.get('is_customs_compliant', True))}")
    print(f"Errors:              {sum(1 for r in results if r['error'])}")
    print(f"\nAll runs traced in LangSmith!")
    print(f"View at: https://eu.smith.langchain.com")
    print("=" * 65)


if __name__ == "__main__":
    main()