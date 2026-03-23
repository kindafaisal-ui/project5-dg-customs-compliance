# Smart Document Automation
## Dangerous Goods & Customs Clearance Compliance
**A project for Chleo — CEO of a medium-sized German freight company**

---

## What is this project about?

Every day, Chleo's company sends hundreds of international shipments. Each shipment requires paperwork — documents that must follow strict rules set by international regulations. There are two types of documents that cause the most problems:

**1. Dangerous Goods declarations** — When a shipment contains chemicals, gases, or hazardous materials, the company must fill out special forms following regulations called ADR (road), IMDG (sea), and IATA (air). One mistake can lead to fines of €50,000 or more.

**2. Customs clearance documents** — Every shipment leaving Germany to another country needs customs paperwork. Wrong or missing information causes the shipment to be held at the border for 1–2 days.

Currently, staff spend **9–12 minutes** manually checking each document. This project replaces that manual work with an AI system that does it in **44 seconds** — with a full explanation of every decision it makes.

---

## Why did we build this?

Chleo was skeptical about AI. Her main concern: *"AI is not transparent — I can't see what it's doing."*

This project was built specifically to prove that AI can be transparent, explainable, and valuable. Every single AI decision is logged and visible in a monitoring tool called LangSmith — Chleo can see exactly what was checked and why.

---

## What does the system do?

Here is what happens when the system runs:

1. **Reads shipment documents** — the AI looks at each document (dangerous goods or customs)
2. **Checks compliance** — validates against the relevant regulations automatically
3. **Flags problems** — if something is wrong, it explains exactly what and why
4. **Sends an alert email** — every night at midnight, the team receives an email with any issues found
5. **Updates the dashboard** — management can see live statistics in Tableau

---

## What tools were used?

| Tool | What it does | Why we chose it |
|---|---|---|
| Python | The programming language everything is written in | Industry standard for AI projects |
| LangChain | Builds the AI agent that checks documents | Makes AI tools easy to connect together |
| OpenAI GPT-3.5 | The AI brain that reads and analyzes documents | Reliable, fast, and cost-effective |
| LangSmith | Records every AI decision for full transparency | Addresses Chleo's concern about AI being a black box |
| n8n | Sends automatic email alerts every night at midnight | No-code automation — easy to modify without a developer |
| Tableau Cloud | Shows live compliance statistics in a dashboard | Visual, easy to understand for management |

> **Note on dashboard:** The project brief asked for PowerBI. PowerBI Desktop only works on Windows computers, not Mac. Tableau Cloud was used instead — it does the same thing and works on any device.

---

## What are the results?

From our 500-document test dataset:

- **44 seconds** — average time the AI takes to process one document (vs 9–12 minutes manually)
- **90.7%** — average confidence score of the AI across all documents
- **1.2%** — error rate (only 6 out of 500 documents flagged as problematic)
- **559 seconds saved** per document compared to manual processing
- **€80,000+** estimated annual savings in staff time

---

## How was the AI quality checked?

A second AI (called the "judge") was used to evaluate the quality of the insights our AI generated. This is called **LLM-as-judge evaluation**. The judge scored each insight on four things:

- **Relevance** — Is this useful for a freight company? → **9.1/10**
- **Accuracy** — Are the numbers correct? → **9.3/10**
- **Actionability** — Can Chleo act on this right now? → **8.1/10**
- **Clarity** — Is it easy to understand? → **8.9/10**
- **Overall average → 8.7/10**

---

## Project files explained

```
Week7-Day4+5/
│
├── data/
│   └── raw/shipments.csv          ← The 500 test documents
│
├── evaluation/
│   ├── evaluation_results.json    ← Judge scores for each insight
│   └── evaluation_report.md       ← Full quality report
│
├── agent.py                       ← AI agent (checks DG + customs docs)
├── langchain_agent.py             ← More advanced version of the agent
├── langsmith_monitoring.py        ← Sets up the monitoring system
├── generate_dataset.py            ← Creates the 500 test documents
├── evaluation.py                  ← Runs the quality evaluation
├── main.py                        ← Master script — runs everything at once
│
├── project5_research_final.docx   ← Research, use cases, opportunities
├── architecture_docs.docx         ← How the system is built
├── cost_timeline.docx             ← Costs and timeline estimates
│
├── requirements.txt               ← List of software packages needed
├── .env.example                   ← Template for API keys (see setup below)
└── README.md                      ← This file
```

---

## How to run this project

**Step 1 — Get the required API keys**
You need two API keys (free accounts available):
- OpenAI API key → https://platform.openai.com
- LangSmith API key → https://smith.langchain.com

**Step 2 — Set up your environment**
```
# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install all required packages
pip install -r requirements.txt
```

**Step 3 — Add your API keys**
Copy the `.env.example` file, rename it to `.env`, and fill in your keys:
```
OPENAI_API_KEY=your_key_here
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=project5-dg-customs-compliance
LANGCHAIN_ENDPOINT=https://eu.api.smith.langchain.com
```

**Step 4 — Generate the dataset**
```
python generate_dataset.py
```

**Step 5 — Run the full system**
```
python main.py
```

This one command does everything — analyzes documents, saves results, updates LangSmith, generates insights, and triggers the n8n email alert.

**Step 6 — Run the quality evaluation**
```
python evaluation.py
```

---

## Where to see the results

| Tool | Link |
|---|---|
| LangSmith traces | https://eu.smith.langchain.com |
| Tableau dashboard | https://dub01.online.tableau.com |
| n8n workflow | https://kinda5.app.n8n.cloud |

---

## Who built this?

**Kinda Faisal** — AI Consulting Bootcamp, Week 7, 2026

This project was built as a proof of concept to show Chleo that AI can be transparent, affordable, and genuinely useful for a medium-sized logistics company in Germany.