# LLM-as-Judge Evaluation Report
## Project 5 — Smart Document Automation: DG & Customs Clearance
**Date:** 2026-03-23  
**Evaluator:** GPT-3.5-Turbo (acting as judge)  
**Insights evaluated:** 7  
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
| Relevance | 9.1/10 | Excellent |
| Accuracy | 9.3/10 | Excellent |
| Actionability | 7.9/10 | Good |
| Clarity | 8.7/10 | Excellent |
| **Overall Average** | **8.7/10** | **Excellent** |

**Best insight:** INS-003 — Error Rate (score: 9.5/10)  
**Weakest insight:** INS-002 — Confidence (score: 8/10)

---

## 3. Individual Insight Evaluations

### INS-001 — Efficiency
**Insight:** AI saves 559 seconds per document compared to manual processing — reducing total document handling time by 93%, freeing staff to focus on exception handling and customer communication instead of data entry.

| Criterion | Score | Reasoning |
|---|---|---|
| Relevance | 9/10 | Highly relevant as it directly impacts efficiency in handling DG declarations and customs clearance documents. |
| Accuracy | 10/10 | Factually correct and well-supported by the provided data source. |
| Actionability | 8/10 | The CEO can act on this insight by implementing AI automation to save time and improve staff focus. |
| Clarity | 9/10 | Clear and understandable, highlighting the time saved and benefits of staff reallocation. |
| **Overall** | **9/10** | |

**Feedback:** The insight is highly relevant, accurate, actionable, and clear. To further enhance, providing specific examples of exception handling and customer communication improvements could be beneficial.  
**Recommendation:** Include specific examples of how staff can utilize the saved time for exception handling and customer communication to enhance the insight further.

---

### INS-002 — Confidence
**Insight:** The AI achieves 90.7% average confidence across all document types, with Commercial Invoices scoring highest (93.2%) and DG Declaration (ADR) scoring lowest (87.1%) due to complex tunnel restriction and emergency contact validation rules.

| Criterion | Score | Reasoning |
|---|---|---|
| Relevance | 9/10 | Highly relevant as it directly addresses the AI's performance in handling DG declarations and customs documents. |
| Accuracy | 8/10 | The insight is backed by specific data (mean confidence scores) and provides details on document types. |
| Actionability | 7/10 | Chleo can act on this insight by focusing on improving confidence for DG Declaration documents. |
| Clarity | 8/10 | The insight is clear in explaining the AI's confidence levels for different document types and the reasons for variations. |
| **Overall** | **8/10** | |

**Feedback:** The insight provides valuable information on AI performance in handling different document types, but Chleo may need more specific recommendations for improvement.  
**Recommendation:** Provide Chleo with actionable steps to enhance the AI's confidence in handling DG Declaration documents, such as refining tunnel restriction and emergency contact validation rules.

---

### INS-003 — Error Rate
**Insight:** Only 1.2% of documents were flagged as non-compliant — just 6 out of 500 — compared to the industry average of 5-10%. This 94% error reduction directly reduces the risk of ADR fines up to €50,000 per violation.

| Criterion | Score | Reasoning |
|---|---|---|
| Relevance | 10/10 | Highly relevant as it directly relates to DG & customs compliance for a freight company. |
| Accuracy | 10/10 | Factually correct with clear data source provided for verification. |
| Actionability | 9/10 | The CEO can act on this insight immediately to reduce compliance risks. |
| Clarity | 9/10 | Clear and understandable even for a non-technical CEO. |
| **Overall** | **9.5/10** | |

**Feedback:** This insight provides valuable information on error reduction in compliance documents, empowering the CEO to make informed decisions. To improve, more context on how the error reduction was achieved could be beneficial.  
**Recommendation:** Provide additional details on the strategies or AI tools used to achieve the significant error reduction for better understanding and potential replication.

---

### INS-004 — Document Coverage
**Insight:** The system automates compliance checks for both dangerous goods (165 documents: ADR, IMDG, IATA) and customs clearance (212 documents: export declarations, CMR waybills, EUR.1 certificates) — covering 100% of Chleo's compliance workload.

| Criterion | Score | Reasoning |
|---|---|---|
| Relevance | 10/10 | The insight directly addresses the automation of compliance checks for dangerous goods and customs clearance, which are crucial for a logistics company. |
| Accuracy | 10/10 | The insight is supported by specific numbers of documents for dangerous goods and customs clearance, providing clear data sources. |
| Actionability | 9/10 | Chleo can act on this insight by exploring the system for automating compliance checks, potentially saving time and reducing errors in document processing. |
| Clarity | 9/10 | The insight clearly outlines the coverage of compliance checks for both dangerous goods and customs clearance, using understandable document categories. |
| **Overall** | **9.5/10** | |

**Feedback:** The insight is highly relevant, accurate, and actionable, providing a clear overview of the system's capabilities. To improve, more details on the AI technology used could enhance transparency.  
**Recommendation:** Provide additional information on the AI algorithms or models used for compliance checks to increase transparency and build trust in the automation process.

---

### INS-005 — Time Savings
**Insight:** Automating 500 documents saves 78 hours total — equivalent to nearly 10 full working days of staff time. At German logistics staff cost of €25/hour, this represents €1,950 in direct labor savings per 500-document batch.

| Criterion | Score | Reasoning |
|---|---|---|
| Relevance | 8/10 | The insight directly relates to time savings in handling DG and customs documents, which is crucial for operational efficiency. |
| Accuracy | 9/10 | The calculations based on the data source provided are accurate and support the labor savings claim. |
| Actionability | 7/10 | The CEO can act on this insight by considering automation to achieve cost savings, but further analysis may be needed for implementation. |
| Clarity | 8/10 | The insight is presented in a clear and straightforward manner, making it understandable for a non-technical CEO. |
| **Overall** | **8/10** | |

**Feedback:** The insight provides valuable information on potential cost savings through automation, but more details on the automation process and potential challenges would enhance its usefulness.  
**Recommendation:** Include additional information on the AI automation process, potential risks, and benefits to provide a more comprehensive understanding for decision-making.

---

### INS-006 — Route Risk
**Insight:** DE→TR is the highest volume customs route (43 documents) and also the most compliance-sensitive — requiring EUR.1 certificates for EU-Turkey customs union preferences. Automating this route alone eliminates the most common customs hold reason.

| Criterion | Score | Reasoning |
|---|---|---|
| Relevance | 9/10 | Highly relevant as it pertains to customs compliance for a German freight company. |
| Accuracy | 10/10 | Factually correct and supported by specific data from the dataset. |
| Actionability | 8/10 | The CEO can act on this insight by prioritizing automation for the DE→TR route to reduce customs holds. |
| Clarity | 9/10 | Clear and concise, using simple language and providing specific details. |
| **Overall** | **9/10** | |

**Feedback:** This insight provides valuable information on a critical customs route, backed by data, and offers a clear course of action. To improve, more context on the impact of automating this route could be beneficial.  
**Recommendation:** Include additional information on the potential cost savings or efficiency gains from automating the DE→TR route to enhance the insight further.

---

### INS-007 — Transparency
**Insight:** Every AI decision is traced in LangSmith with average latency of 1.2 seconds per document. The full audit trail — input document, compliance checks run, result, and confidence score — is available for every shipment, addressing Chleo's concern about AI transparency.

| Criterion | Score | Reasoning |
|---|---|---|
| Relevance | 9/10 | Highly relevant as it addresses Chleo's concern about AI transparency in DG and customs compliance. |
| Accuracy | 8/10 | Backed by data source and specific average latency provided. |
| Actionability | 7/10 | Chleo can act on this insight by leveraging the audit trail for transparency improvements. |
| Clarity | 9/10 | Clear and concise explanation of how AI decisions are traced and the availability of audit trail. |
| **Overall** | **8.2/10** | |

**Feedback:** The insight is highly relevant and accurate, providing actionable steps for improving transparency. To enhance, more details on how the audit trail can be utilized effectively could be beneficial.  
**Recommendation:** Provide examples of how the audit trail can be used to enhance transparency and compliance monitoring.

---

## 4. Patterns Analysis

### High-scoring insights
Insights scoring above 9/10 tend to:
- Include specific numbers directly from the dataset (not vague claims)
- Connect the data point to a business impact Chleo can relate to (fines, staff time, cost savings)
- Use plain language without technical jargon (ADR, IMDG explained in context)

### Low-scoring insights
Insights scoring below 9/10 tend to:
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
- LangSmith dataset ID: 1f09f041-056f-43d4-94c8-1e8b2090775e
- Evaluation results: evaluation/evaluation_results.json
