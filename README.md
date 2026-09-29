# Vireo Audio — Support Intelligence & AI Triage

## 1. What This Is

The **Vireo Audio Support Intelligence & AI Triage Platform** is an interactive operations and decision-support web application built for Vireo Audio's executive leadership. It ingests historical customer support records, automatically categorises support tickets across a 10-category semantic taxonomy, analyzes monthly intake versus resolving workload distributions, and evaluates a high-stakes headcount allocation dispute (a proposed ₹9 Lakh/year budget for two new hires between Billing and Logistics).

---

## 2. Requirements

- **Python**: Python 3.8+ (standard library only; `pandas` and `numpy` for data handling)
- **Web Browser**: Any modern browser (Chrome, Firefox, Safari, Edge)
- **External Dependencies**: **None**. Zero external API keys, zero paid cloud LLM calls, and zero `npm install` / build steps required. The application runs 100% locally on a clean machine.

---

## 3. Quick Start

Run the following command from the project root directory:

```bash
python app.py 8000
```

Then open your web browser at:

```
http://127.0.0.1:8000
```

*The final evaluation-facing application runs on **port 8000**.*

---

## 4. Application Sections

The application is structured into four functional tabs:

### 1. Executive Overview
- Displays headline operational KPIs for the **1 Jan 2025 – 30 Jun 2026** reporting window (11,641 tickets, ₹4,52,200 SLA breach penalties, ₹3,96,195 transfer re-handling costs, ₹31,82,240 contact costs).
- Features an interactive **Billing vs. Logistics Head-to-Head panel** and an **Intake Keyword Trap** flow diagram illustrating the misrouted volume flow.
- Renders an inline SVG time series chart tracking monthly intake versus resolving demand across 18 months.

### 2. AI Ticket Triage
- Live interactive sandbox allowing operators to enter customer messages and optional agent closing notes.
- Predicts semantic category, policy owning team, confidence score, primary evidence quote, and recommended routing action.
- Features an automated **Misrouting Warning** that detects payment keywords on shipment tracking queries.
- Includes one-click example presets for *Delivery Misroute*, *Battery Defect*, and *Bluetooth Pairing*.

### 3. Staffing Simulator
- Models the ₹9,00,000 / year (2-hire) support budget across five interactive scenarios (Baseline, 2 to Billing, 2 to Logistics, Split 1+1, and Routing Improvement + 2 to Logistics).
- Displays per-agent monthly workload shifts (28.6 to 20.4 tickets/agent/month) and operational trade-offs.

### 4. Ticket Explorer
- Searchable, filterable in-memory data grid of all 11,641 reporting-window support tickets.
- Filter by Initial/Resolving Team, Category, Channel, and SLA Status with pagination and a click-to-inspect detail modal.

---

## 5. Data & Reporting Scope

- **Data Preservation**: All original source files in [`data/`](file:///d:/ATSLite/data/) (`tickets.csv`, `agents.csv`, `customers.csv`, `orders.csv`, `products.csv`) are preserved in their original state and are never modified by the application.
- **Reporting Window**: All headline metrics strictly reflect the **1 Jan 2025 – 30 Jun 2026** reporting window (**11,641 tickets**; 646.7 tickets/month average).
- **Legacy Tail Demarcation**: The 139 pre-2025 legacy tickets (June–Dec 2024) are explicitly excluded from headline period calculations.

---

## 6. Classification Approach

The application uses a **local hybrid semantic classification engine** based on the project's validated 10-category taxonomy and deterministic inference rules ([`analysis/classification_rules.md`](file:///d:/ATSLite/analysis/classification_rules.md)).

- **No Cloud LLM**: The system does **not** make external cloud LLM API calls.
- **Explainability**: Every classification outputs an exact primary evidence text quote, a confidence score, owning team routing, and misrouting detection.
- **Disclosure**: Designed as an AI-assisted triage system that operates locally with zero external latency, zero cost, and zero internet dependency.

---

## 7. Validation & Benchmark Integrity

The categorization approach was audited and verified through a dedicated validation protocol:

- **Validation Sample**: 121 representative support tickets ([`analysis/output/manual_review_sample.csv`](file:///d:/ATSLite/analysis/output/manual_review_sample.csv)).
- **Genuine Human Reviews**: **2 tickets** (`TK-245609`, `TK-254555`) reviewed and marked `HUMAN_REVIEWED`.
- **Browser-Agent Independent Reviews**: **119 tickets** adjudicated via live browser automation on `http://127.0.0.1:8080` and marked `AUTOMATED_INDEPENDENT_REVIEW`.
- **Classifier Agreement**: **102 / 119 = 85.71%**.

> [!IMPORTANT]
> **85.71% is browser-agent agreement with the classifier, not human accuracy.** The 2 genuine human-reviewed records are maintained separately in the audit logs.

---

## 8. Key Business Findings

The data resolves the executive dispute between Priya Raman (Head of CX), Arjun Mehta (Finance Controller), and Neha Kulkarni (Operations Manager):

```
========================================================================================
HEADLINE COMPARATIVE METRICS (1 Jan 2025 – 30 Jun 2026)
========================================================================================
Metric                            Billing Desk              Logistics Desk
----------------------------------------------------------------------------------------
Initial Intake Queue Size         2,425 tickets (20.83%)    1,905 tickets (16.36%)
True Resolving Workload           1,798 tickets (15.45%)    2,574 tickets (22.11%)
Net Workload Shift                -627 tickets (-25.86%)    +669 tickets (+35.12%)
Cross-Team Misrouted Handoffs     696 tickets -> Logistics  35 tickets -> Billing
Observed Transfer Spend (Window)  ₹1,92,760 (48.65% total)  ₹34,160 (8.62% total)
Median Resolution Latency         1.23 hours                26.16 hours (21.3x higher)
P90 Resolution Latency Tail       48.80 hours (2.0 days)    120.61 hours (5.0 days)
========================================================================================
```

**Core Takeaway**: Intake volume and resolving workload tell completely different stories. Billing's intake queue is artificially inflated because the keyword intake bot tags delivery delays mentioning *"money deducted"* or *"paid"* as Billing. In reality, **28.70% of Billing tickets (696 tickets) are handed off to and resolved by Logistics**, making Logistics the single largest specialized resolving workload in the company.

---

## 9. Known Limitations

1. **Local Deterministic Inference**: Uses regex-pattern semantic rules rather than dynamic multi-billion-parameter neural weights.
2. **Limited Human Ground Truth**: Only 2 tickets were reviewed by genuine human operators; the remaining 119 validation tickets were processed via browser automation.
3. **Legacy Transfer Field Omission**: The `transfers` field was not captured in legacy Freshdesk; transfer metrics are computed strictly across current helpdesk records ($N = 7,728$).
4. **Modeled Cost Projections**: The potential ₹1.93L transfer-cost reduction is a **modeled scenario estimate**, not realized savings.

---

## 10. Deliberate Scope Decisions

To ensure clean-machine reliability and adhere to the ~5-hour effort guideline, the following were deliberately excluded:
- **External LLM APIs**: Avoids API key dependencies, rate limits, network latency, and billing setup.
- **Heavy Frontend Frameworks**: Built in Vanilla HTML/CSS/JS with inline SVG charts instead of React/Next.js/Webpack build pipelines.
- **Production SQL / Microservices**: In-memory Python data structures provide sub-millisecond response times without database setup.
- **Authentication / RBAC**: Excluded to allow instant evaluation by reviewers.

---

## 11. Project Structure

```
ATSLite/
│
├── app.py                      # Main application server (Port 8000)
├── app.html                    # 4-Tab single-page web interface
├── app.css                     # Design system & dark/light theme
├── app.js                      # Chart rendering, triage logic, & explorer controller
├── README.md                   # Evaluator quickstart & documentation (This file)
├── README.txt                  # Original data dictionary from client pack
├── ANTIGRAVITY_PROJECT_CONTEXT.md # Development context & policy standards
│
├── data/                       # Canonical raw CSV files (Untouched)
│   ├── tickets.csv             # 11,780 support ticket records
│   ├── agents.csv              # 44 agent assignments / roster history
│   ├── customers.csv           # 9,500 customer profiles
│   ├── orders.csv              # 15,000 order records
│   └── products.csv            # 14 product catalog SKUs
│
├── docs/                       # Official policy documents
│   ├── support-policy.pdf      # Vireo Support Operating Policy v3.2
│   └── email-thread.txt        # Stakeholder email discussion
│
└── analysis/                   # Analytical models, validation audit, & outputs
    ├── review_server.py        # Temporary validation review server (Port 8080)
    ├── step4_business_outcome.md # Comprehensive business outcome report
    ├── final_tool_audit.md     # Final system verification report
    └── output/                 # Pre-computed metrics, validation CSVs, & charts
```

---

## 12. Validation Server vs. Final Application Distinction

- **Port 8000 (`python app.py 8000`)**: The **Final Evaluator-Facing Application** containing the Executive Dashboard, Live AI Triage Sandbox, Staffing Simulator, and Ticket Explorer.
- **Port 8080 (`python analysis/review_server.py 8080`)**: The **Temporary Step 3.6 Validation Tool** used exclusively for auditing and reviewing the 121 validation sample tickets.

---

## 13. Submission Artifacts

- **Executive Briefing**: [`memo_to_priya.md`](file:///d:/ATSLite/memo_to_priya.md) (1-page non-technical briefing for Priya Raman, Head of CX).
- **Official Submission Form**: [`submission-form.md`](file:///d:/ATSLite/submission-form.md) (Complete candidate submission report).
- **Screen Recording**: Linked in the official submission form.
