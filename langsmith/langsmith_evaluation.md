# LangSmith Evaluation Documentation
## Project 5 — Smart Document Automation: DG & Customs Clearance

**LangSmith Project:** project5-dg-customs-compliance  
**Endpoint:** https://eu.api.smith.langchain.com (EU server — GDPR compliant)  
**View traces:** https://eu.smith.langchain.com

---

## Datasets Created

### 1. DG-Customs-Compliance-Monitoring-Dataset
- **Purpose**: Monitors AI compliance agent performance in production
- **Examples**: 15 shipment documents (DG flagged, DG review, Customs flagged, Customs review, Auto-approved)
- **Inputs**: doc_id, doc_type, route, dg_class, un_number, compliance_status, confidence_score
- **Outputs**: expected_status, expected_action, risk_level, doc_type_category
- **Created by**: langsmith_monitoring.py

### 2. DG-Customs-Evaluation-Dataset
- **Purpose**: LLM-as-judge evaluation of AI-generated business insights
- **Examples**: 7 business insights evaluated on 4 criteria
- **Inputs**: insight_id, category, insight_text, data_source
- **Outputs**: relevance, accuracy, actionability, clarity, overall_score, feedback
- **Created by**: evaluation.py

---

## Traced Functions

Every AI decision is automatically traced in LangSmith via the `@traceable` decorator:

| Function | Trace Name | What it logs |
|---|---|---|
| analyze_document() | DG-Customs-Compliance-Agent | Input doc, DG check result, customs check result, risk level, latency |
| generate_insights() | Generate-Business-Insights | Dataset stats used, insights generated, latency |
| evaluate_insight() | LLM-Judge-Evaluation | Insight evaluated, all 4 scores, reasoning, latency |

---

## Evaluator Design

### LLM-as-Judge Approach
A second instance of GPT-3.5-Turbo acts as judge, evaluating each AI-generated insight on 4 criteria:

**1. Relevance (1-10)**
Is the insight directly relevant to DG & customs compliance for a German freight company?
High score: Directly addresses a pain point Chleo faces daily
Low score: Too generic, could apply to any company or sector

**2. Accuracy (1-10)**
Is the insight factually correct and properly backed by the data source?
High score: Numbers match the dataset, regulations cited correctly
Low score: Vague claims without data backing, incorrect regulatory references

**3. Actionability (1-10)**
Can CEO Chleo act on this insight immediately or in the near term?
High score: Clear next action, specific route or document type to prioritize
Low score: Interesting fact but no clear action required

**4. Clarity (1-10)**
Is the insight clear and understandable to a non-technical CEO?
High score: No jargon, plain language, concrete example
Low score: Technical terms unexplained, assumes regulatory knowledge

---

## Experiment Configuration
- **Judge model**: gpt-3.5-turbo, temperature=0 (deterministic)
- **Output format**: Structured JSON (enforced in system prompt)
- **Insights evaluated**: 7 (one per business category)
- **Run by**: evaluation.py

---

## How to View Results
1. Go to https://eu.smith.langchain.com
2. Select project: project5-dg-customs-compliance
3. Click "Datasets" to see both monitoring and evaluation datasets
4. Click "Traces" to see all agent runs with full input/output/latency
5. Full evaluation results: evaluation/evaluation_results.json
6. Full evaluation report: evaluation/evaluation_report.md