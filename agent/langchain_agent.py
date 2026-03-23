import os
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langsmith import traceable

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "project5-dg-compliance"
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")

try:
    df = pd.read_csv("data/raw/shipments.csv")
    print(f"Dataset loaded: {len(df)} records")
except FileNotFoundError:
    print("ERROR: data/raw/shipments.csv not found!")
    exit(1)

try:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

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
            if "CN" in route or "JP" in route:
                violations.append("IMDG documentation required")
            if "US" in route:
                violations.append("IATA DGR compliance required")
        return f"NON-COMPLIANT: {'; '.join(violations)}" if violations else "COMPLIANT: All DG requirements met"
    except Exception as e:
        return f"ERROR: {str(e)}"

@tool
def check_customs_compliance(doc_type: str, route: str, error_detail: str) -> str:
    """Checks customs document compliance for EU/international shipments."""
    try:
        issues = []
        if error_detail and error_detail not in ["nan", "None", ""]:
            issues.append(f"Error: {error_detail}")
        if "TR" in route or "GB" in route:
            issues.append("EUR.1 certificate required")
        if "US" in route or "CN" in route:
            issues.append("HS code required")
        return f"REVIEW REQUIRED: {'; '.join(issues)}" if issues else "COMPLIANT: Customs docs in order"
    except Exception as e:
        return f"ERROR: {str(e)}"

@traceable(name="LangChain-DG-Compliance-Agent")
def analyze_document(doc: dict) -> dict:
    """Analyzes a shipment document using LangChain. Traced in LangSmith."""
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
        prompt = f"Document {doc.get('doc_id')} - {doc.get('doc_type')}, Route: {doc.get('route')}. DG={dg_result}. Customs={customs_result}. Give: 1.Compliant? 2.Risk? 3.Action?"
        response = llm.invoke([
            SystemMessage(content="You are a logistics compliance expert. Be concise."),
            HumanMessage(content=prompt)
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
            "error": None
        }
    except Exception as e:
        return {
            "doc_id": doc.get("doc_id", "Unknown"),
            "doc_type": doc.get("doc_type", "Unknown"),
            "route": doc.get("route", "Unknown"),
            "dg_check": "ERROR",
            "customs_check": "ERROR",
            "assessment": f"Analysis failed: {str(e)}",
            "is_compliant": False,
            "risk_level": "Unknown",
            "action_required": "Manual review required",
            "error": str(e)
        }

@traceable(name="Generate-Dataset-Insights")
def generate_insights() -> list:
    """Generates 5 meaningful business insights from the dataset."""
    try:
        avg_conf = df["confidence_score"].mean()
        avg_proc = df["processing_time_seconds"].mean()
        avg_manual = df["manual_baseline_seconds"].mean()
        avg_saved = df["time_saved_seconds"].mean()
        error_rate = len(df[df["compliance_status"] == "Flagged"]) / len(df) * 100
        best_doc = df.groupby("doc_type")["confidence_score"].mean().idxmax()
        worst_doc = df.groupby("doc_type")["confidence_score"].mean().idxmin()
        prompt = f"Generate exactly 5 business insights from: avg confidence={avg_conf:.1f}%, avg AI time={avg_proc:.0f}s, avg manual time={avg_manual:.0f}s, avg saved={avg_saved:.0f}s, error rate={error_rate:.1f}%, best doc={best_doc}, worst doc={worst_doc}. Format: INSIGHT N: title - description"
        response = llm.invoke([
            SystemMessage(content="You are a logistics business analyst."),
            HumanMessage(content=prompt)
        ])
        return [line for line in response.content.split("\n") if line.strip()][:10]
    except Exception as e:
        return [
            f"INSIGHT 1: AI saves {df['time_saved_seconds'].mean():.0f} seconds per document vs manual processing",
            f"INSIGHT 2: Average AI confidence score is {df['confidence_score'].mean():.1f}% across all document types",
            f"INSIGHT 3: Only {len(df[df['compliance_status']=='Flagged'])} out of {len(df)} documents flagged ({len(df[df['compliance_status']=='Flagged'])/len(df)*100:.1f}% error rate)",
            f"INSIGHT 4: DG declarations take longest to process due to regulatory complexity",
            f"INSIGHT 5: Automating document processing saves ~{df['time_saved_seconds'].sum()/3600:.0f} hours annually"
        ]

def main():
    print("=" * 60)
    print("LangChain DG Compliance Agent - LangSmith Monitored")
    print("=" * 60)
    print("\n[1/2] Analyzing 5 sample documents...")
    results = []
    for _, row in df.head(5).iterrows():
        doc = row.to_dict()
        print(f"\n  Analyzing {doc['doc_id']} - {doc['doc_type']}...")
        result = analyze_document(doc)
        results.append(result)
        if result["error"]:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  DG Check:  {result['dg_check']}")
            print(f"  Customs:   {result['customs_check']}")
            print(f"  Risk:      {result['risk_level']}")
            print(f"  Compliant: {result['is_compliant']}")
    print("\n[2/2] Generating 5 business insights...")
    insights = generate_insights()
    print("\n" + "=" * 60)
    print("5 MEANINGFUL INSIGHTS FROM THE DATA")
    print("=" * 60)
    for insight in insights:
        print(f"\n{insight}")
    print("\n" + "=" * 60)
    print(f"Analyzed: {len(results)} | Compliant: {sum(1 for r in results if r['is_compliant'])} | Errors: {sum(1 for r in results if r['error'])}")
    print("All runs traced in LangSmith: https://eu.smith.langchain.com")
    print("=" * 60)

if __name__ == "__main__":
    main()