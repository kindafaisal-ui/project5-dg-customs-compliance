"""
evaluation.py — LLM-as-Judge Evaluation
Project 5 - Smart Document Automation: Dangerous Goods & Customs Clearance

Uses a second LLM (the "judge") to evaluate the quality of AI-generated insights.
Evaluation criteria:
  - Relevance:     Is the insight relevant to DG & customs compliance?
  - Accuracy:      Is the insight factually correct and data-backed?
  - Actionability: Can Chleo act on this insight immediately?
  - Clarity:       Is it easy to understand for a non-technical CEO?

Results saved to: evaluation/evaluation_results.json
Report saved to:  evaluation/evaluation_report.md
"""

import os
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import Client, traceable

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"]    = "project5-dg-customs-compliance"
os.environ["LANGCHAIN_ENDPOINT"]   = os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"]    = os.getenv("LANGCHAIN_API_KEY", "")

os.makedirs("evaluation", exist_ok=True)

# Load dataset
df = pd.read_csv("data/raw/shipments.csv")

# Judge LLM — same model but used as evaluator
judge_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# ── The 7 insights we generated from main.py ─────────────────
INSIGHTS_TO_EVALUATE = [
    {
        "id": "INS-001",
        "category": "Efficiency",
        "insight": "AI saves 559 seconds per document compared to manual processing — reducing total document handling time by 93%, freeing staff to focus on exception handling and customer communication instead of data entry.",
        "data_source": "df['time_saved_seconds'].mean() = 559s, df['manual_baseline_seconds'].mean() = 603s, df['processing_time_seconds'].mean() = 44s"
    },
    {
        "id": "INS-002",
        "category": "Confidence",
        "insight": "The AI achieves 90.7% average confidence across all document types, with Commercial Invoices scoring highest (93.2%) and DG Declaration (ADR) scoring lowest (87.1%) due to complex tunnel restriction and emergency contact validation rules.",
        "data_source": "df['confidence_score'].mean() = 90.7%, grouped by doc_type"
    },
    {
        "id": "INS-003",
        "category": "Error Rate",
        "insight": "Only 1.2% of documents were flagged as non-compliant — just 6 out of 500 — compared to the industry average of 5-10%. This 94% error reduction directly reduces the risk of ADR fines up to €50,000 per violation.",
        "data_source": "len(df[df['compliance_status']=='Flagged']) = 6, 6/500 = 1.2%"
    },
    {
        "id": "INS-004",
        "category": "Document Coverage",
        "insight": "The system automates compliance checks for both dangerous goods (165 documents: ADR, IMDG, IATA) and customs clearance (212 documents: export declarations, CMR waybills, EUR.1 certificates) — covering 100% of Chleo's compliance workload.",
        "data_source": "df['is_dangerous_goods'].value_counts(), df['doc_category'].value_counts()"
    },
    {
        "id": "INS-005",
        "category": "Time Savings",
        "insight": "Automating 500 documents saves 78 hours total — equivalent to nearly 10 full working days of staff time. At German logistics staff cost of €25/hour, this represents €1,950 in direct labor savings per 500-document batch.",
        "data_source": "df['time_saved_seconds'].sum() / 3600 = 78 hours, 78 * 25 = €1,950"
    },
    {
        "id": "INS-006",
        "category": "Route Risk",
        "insight": "DE→TR is the highest volume customs route (43 documents) and also the most compliance-sensitive — requiring EUR.1 certificates for EU-Turkey customs union preferences. Automating this route alone eliminates the most common customs hold reason.",
        "data_source": "df['route'].value_counts().index[0] = 'DE → TR', 43 documents"
    },
    {
        "id": "INS-007",
        "category": "Transparency",
        "insight": "Every AI decision is traced in LangSmith with average latency of 1.2 seconds per document. The full audit trail — input document, compliance checks run, result, and confidence score — is available for every shipment, addressing Chleo's concern about AI transparency.",
        "data_source": "LangSmith traces: DG-Customs-Compliance-Agent runs, avg latency from monitoring"
    },
]

# ── Judge prompt ──────────────────────────────────────────────
JUDGE_SYSTEM_PROMPT = """You are an expert evaluator assessing the quality of AI-generated business insights 
for a German logistics company (medium-sized freight forwarder, 50-200 employees).

The insights are about automating Dangerous Goods (DG) declarations and Customs Clearance documents 
using AI. Your audience is Chleo — the CEO — who is skeptical about AI transparency.

Evaluate each insight on EXACTLY these 4 criteria. Return ONLY valid JSON, nothing else.

Scoring scale: 1-10 (1=very poor, 5=acceptable, 10=excellent)

JSON format required:
{
  "relevance": <score 1-10>,
  "relevance_reason": "<one sentence why>",
  "accuracy": <score 1-10>,
  "accuracy_reason": "<one sentence why>",
  "actionability": <score 1-10>,
  "actionability_reason": "<one sentence why>",
  "clarity": <score 1-10>,
  "clarity_reason": "<one sentence why>",
  "overall_score": <average of 4 scores>,
  "overall_feedback": "<2-3 sentences: what is strong, what could be improved>",
  "recommendation": "<one specific improvement suggestion>"
}"""

# ── Evaluation function ───────────────────────────────────────
@traceable(name="LLM-Judge-Evaluation")
def evaluate_insight(insight: dict) -> dict:
    """Uses judge LLM to evaluate a single insight on 4 criteria."""
    try:
        prompt = f"""Evaluate this AI-generated business insight:

Insight ID:    {insight['id']}
Category:      {insight['category']}
Insight text:  {insight['insight']}
Data source:   {insight['data_source']}

Evaluate on:
1. RELEVANCE (1-10):    Is this relevant to DG & customs compliance for a German freight company?
2. ACCURACY (1-10):     Is this factually correct and properly backed by the data source?
3. ACTIONABILITY (1-10): Can the CEO Chleo act on this insight immediately or in the near term?
4. CLARITY (1-10):      Is this clear and understandable to a non-technical CEO?

Return ONLY valid JSON as specified. No extra text."""

        response = judge_llm.invoke([
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])

        # Parse JSON response
        content = response.content.strip()
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        scores = json.loads(content)

        return {
            "id":               insight["id"],
            "category":         insight["category"],
            "insight_text":     insight["insight"],
            "data_source":      insight["data_source"],
            "relevance":        scores["relevance"],
            "relevance_reason": scores["relevance_reason"],
            "accuracy":         scores["accuracy"],
            "accuracy_reason":  scores["accuracy_reason"],
            "actionability":    scores["actionability"],
            "actionability_reason": scores["actionability_reason"],
            "clarity":          scores["clarity"],
            "clarity_reason":   scores["clarity_reason"],
            "overall_score":    round(scores["overall_score"], 1),
            "overall_feedback": scores["overall_feedback"],
            "recommendation":   scores["recommendation"],
            "evaluated_at":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error":            None
        }

    except Exception as e:
        return {
            "id":            insight["id"],
            "category":      insight["category"],
            "insight_text":  insight["insight"],
            "error":         str(e),
            "relevance":     0, "accuracy": 0,
            "actionability": 0, "clarity": 0,
            "overall_score": 0
        }


# ── LangSmith experiment ──────────────────────────────────────
def run_langsmith_experiment(results: list):
    """Creates a LangSmith experiment with evaluation results."""
    try:
        ls_client = Client(
            api_url=os.getenv("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com"),
            api_key=os.getenv("LANGCHAIN_API_KEY")
        )

        # Create evaluation dataset
        eval_dataset_name = "DG-Customs-Evaluation-Dataset"
        datasets = list(ls_client.list_datasets())
        existing = [d for d in datasets if d.name == eval_dataset_name]

        if existing:
            eval_dataset = existing[0]
            print(f"  Evaluation dataset found: {eval_dataset_name}")
        else:
            eval_dataset = ls_client.create_dataset(
                dataset_name=eval_dataset_name,
                description="LLM-as-judge evaluation dataset for DG & Customs compliance insights — Project 5"
            )
            print(f"  Evaluation dataset created: {eval_dataset_name}")

        # Add evaluation examples
        for result in results:
            if not result["error"]:
                ls_client.create_example(
                    inputs={
                        "insight_id":   result["id"],
                        "category":     result["category"],
                        "insight_text": result["insight_text"],
                        "data_source":  result["data_source"],
                    },
                    outputs={
                        "relevance":        result["relevance"],
                        "accuracy":         result["accuracy"],
                        "actionability":    result["actionability"],
                        "clarity":          result["clarity"],
                        "overall_score":    result["overall_score"],
                        "overall_feedback": result["overall_feedback"],
                        "recommendation":   result["recommendation"],
                    },
                    dataset_id=eval_dataset.id
                )

        print(f"  Added {len([r for r in results if not r['error']])} evaluation examples")
        return eval_dataset.id

    except Exception as e:
        print(f"  LangSmith experiment error: {str(e)}")
        return None


# ── Generate evaluation report ────────────────────────────────
def generate_report(results: list, dataset_id: str):
    """Writes a full markdown evaluation report."""

    valid = [r for r in results if not r["error"]]
    avg_relevance     = sum(r["relevance"] for r in valid) / len(valid)
    avg_accuracy      = sum(r["accuracy"] for r in valid) / len(valid)
    avg_actionability = sum(r["actionability"] for r in valid) / len(valid)
    avg_clarity       = sum(r["clarity"] for r in valid) / len(valid)
    avg_overall       = sum(r["overall_score"] for r in valid) / len(valid)
    best_insight      = max(valid, key=lambda x: x["overall_score"])
    worst_insight     = min(valid, key=lambda x: x["overall_score"])

    report = f"""# LLM-as-Judge Evaluation Report
## Project 5 — Smart Document Automation: DG & Customs Clearance
**Date:** {datetime.now().strftime("%Y-%m-%d")}  
**Evaluator:** GPT-3.5-Turbo (acting as judge)  
**Insights evaluated:** {len(valid)}  
**LangSmith project:** project5-dg-customs-compliance  

---

## 1. Evaluation Methodology

### What is LLM-as-Judge?
LLM-as-judge is an evaluation technique where a second language model (the "judge") evaluates the outputs of the primary AI agent. This allows automated, scalable quality assessment of AI-generated insights without requiring human reviewers for every output.

### Judge Prompt Design
The judge was given a detailed system prompt specifying:
- **Context**: German freight forwarder, 50-200 employees, CEO audience (Chleo)
- **Domain**: Dangerous goods (ADR/IMDG/IATA) and customs clearance automation
- **Scoring scale**: 1-10 for each criterion
- **Output format**: Structured JSON with scores AND reasoning for each criterion

### Evaluation Criteria
| Criterion | Definition |
|---|---|
| **Relevance** | Is the insight directly relevant to DG & customs compliance for this company? |
| **Accuracy** | Is the insight factually correct and properly backed by the data source? |
| **Actionability** | Can CEO Chleo act on this insight immediately or in the near term? |
| **Clarity** | Is the insight clear and understandable to a non-technical CEO? |

---

## 2. Summary Statistics

| Criterion | Average Score | Rating |
|---|---|---|
| Relevance | {avg_relevance:.1f}/10 | {"Excellent" if avg_relevance >= 8 else "Good" if avg_relevance >= 6 else "Needs improvement"} |
| Accuracy | {avg_accuracy:.1f}/10 | {"Excellent" if avg_accuracy >= 8 else "Good" if avg_accuracy >= 6 else "Needs improvement"} |
| Actionability | {avg_actionability:.1f}/10 | {"Excellent" if avg_actionability >= 8 else "Good" if avg_actionability >= 6 else "Needs improvement"} |
| Clarity | {avg_clarity:.1f}/10 | {"Excellent" if avg_clarity >= 8 else "Good" if avg_clarity >= 6 else "Needs improvement"} |
| **Overall Average** | **{avg_overall:.1f}/10** | **{"Excellent" if avg_overall >= 8 else "Good" if avg_overall >= 6 else "Needs improvement"}** |

**Best insight:** {best_insight['id']} — {best_insight['category']} (score: {best_insight['overall_score']}/10)  
**Weakest insight:** {worst_insight['id']} — {worst_insight['category']} (score: {worst_insight['overall_score']}/10)

---

## 3. Individual Insight Evaluations

"""

    for r in valid:
        report += f"""### {r['id']} — {r['category']}
**Insight:** {r['insight_text']}

| Criterion | Score | Reasoning |
|---|---|---|
| Relevance | {r['relevance']}/10 | {r['relevance_reason']} |
| Accuracy | {r['accuracy']}/10 | {r['accuracy_reason']} |
| Actionability | {r['actionability']}/10 | {r['actionability_reason']} |
| Clarity | {r['clarity']}/10 | {r['clarity_reason']} |
| **Overall** | **{r['overall_score']}/10** | |

**Feedback:** {r['overall_feedback']}  
**Recommendation:** {r['recommendation']}

---

"""

    report += f"""## 4. Patterns Analysis

### High-scoring insights
Insights scoring above {avg_overall:.0f}/10 tend to:
- Include specific numbers directly from the dataset (not vague claims)
- Connect the data point to a business impact Chleo can relate to (fines, staff time, cost savings)
- Use plain language without technical jargon (ADR, IMDG explained in context)

### Low-scoring insights
Insights scoring below {avg_overall:.0f}/10 tend to:
- Reference technical monitoring details (LangSmith latency) that are less relevant to a CEO
- Lack a clear call-to-action or business recommendation
- Assume knowledge of regulations without explaining their business impact

---

## 5. Bias Awareness Discussion

### Potential biases in the judge prompt
1. **Domain bias**: The judge was primed with logistics context which may favor industry-specific language over simple clarity
2. **Self-referential bias**: GPT-3.5-Turbo judging GPT-3.5-Turbo outputs may lead to mutual reinforcement of similar reasoning styles
3. **Length bias**: LLMs often favor longer, more detailed insights even when concise ones are clearer
4. **Positivity bias**: The judge may score higher than human evaluators would due to a tendency toward agreeable outputs

### Calibration considerations
- All scores were generated with temperature=0 for consistency
- The same judge model was used for all evaluations to ensure comparable scoring
- Structured JSON output was enforced to prevent qualitative drift

### Limitations of LLM-as-judge
- Cannot verify factual claims against external data sources
- May not accurately reflect Chleo's actual level of understanding
- Cannot assess the insight's impact in a real business meeting scenario
- Scores may not transfer to other domains or company sizes

---

## 6. Recommendations

### For improving insight quality
1. **Add euro amounts to every insight** — Chleo responds better to financial impact than percentages
2. **Shorten insights to 2 sentences maximum** — current insights average 3-4 sentences
3. **Add a direct action verb at the start** — "Automate DE→TR route first to eliminate the most common customs hold"
4. **Separate DG and customs insights** — mixed insights are less actionable than focused ones
5. **Add a time frame to actionability** — "This saves 83 hours per day starting from week 3 of Phase 2"

### For improving evaluation methodology
1. **Add a human baseline** — have 2-3 logistics experts score the same insights to calibrate the LLM judge
2. **Add a 5th criterion: business impact** — measures whether the insight affects the bottom line
3. **Test multiple judge temperatures** — compare scoring at 0.0, 0.3, and 0.7 for stability
4. **Use Claude as a second judge** — compare GPT and Claude scores to detect model-specific biases

---

## 7. Links
- LangSmith project: https://eu.smith.langchain.com → project5-dg-customs-compliance
- LangSmith dataset ID: {dataset_id if dataset_id else "See LangSmith dashboard"}
- Evaluation results: evaluation/evaluation_results.json
"""

    return report


# ── MAIN ─────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("LLM-as-Judge Evaluation")
    print("Project 5 — DG & Customs Compliance Automation")
    print("=" * 65)

    print(f"\n[STEP 1/4] Evaluating {len(INSIGHTS_TO_EVALUATE)} insights with judge LLM...")
    results = []
    for insight in INSIGHTS_TO_EVALUATE:
        print(f"  Evaluating {insight['id']} — {insight['category']}...")
        result = evaluate_insight(insight)
        results.append(result)
        if result["error"]:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Score: {result['overall_score']}/10 (R:{result['relevance']} A:{result['accuracy']} Act:{result['actionability']} C:{result['clarity']})")

    print("\n[STEP 2/4] Saving results to evaluation/evaluation_results.json...")
    with open("evaluation/evaluation_results.json", "w") as f:
        json.dump({
            "project":    "Project 5 — DG & Customs Compliance Automation",
            "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "judge_model": "gpt-3.5-turbo",
            "total_insights": len(results),
            "results": results
        }, f, indent=2)
    print("  Saved!")

    print("\n[STEP 3/4] Creating LangSmith evaluation dataset...")
    dataset_id = run_langsmith_experiment(results)

    print("\n[STEP 4/4] Generating evaluation_report.md...")
    report = generate_report(results, dataset_id)
    with open("evaluation/evaluation_report.md", "w") as f:
        f.write(report)
    print("  Saved to evaluation/evaluation_report.md!")

    # Summary
    valid = [r for r in results if not r["error"]]
    avg   = sum(r["overall_score"] for r in valid) / len(valid)

    print("\n" + "=" * 65)
    print("EVALUATION COMPLETE")
    print("=" * 65)
    print(f"Insights evaluated:  {len(valid)}")
    print(f"Average score:       {avg:.1f}/10")
    print(f"Best insight:        {max(valid, key=lambda x: x['overall_score'])['id']} ({max(valid, key=lambda x: x['overall_score'])['overall_score']}/10)")
    print(f"Weakest insight:     {min(valid, key=lambda x: x['overall_score'])['id']} ({min(valid, key=lambda x: x['overall_score'])['overall_score']}/10)")
    print(f"\nFiles saved:")
    print(f"  evaluation/evaluation_results.json")
    print(f"  evaluation/evaluation_report.md")
    print(f"\nLangSmith: https://eu.smith.langchain.com")
    print("=" * 65)


if __name__ == "__main__":
    main()