# AI Model Provenance Tracker

> **One-line pitch:** Chain of custody for AI — track what data trained what model so enterprises can answer "where did this output come from?" before regulators ask.

## Problem

**Who feels the pain:**
- **Enterprise legal/compliance** — Can't answer "was our model trained on copyrighted data?"
- **AI/ML teams** — No audit trail when something goes wrong (bias, hallucination, IP issues)
- **CISOs** — Data governance mandates now include AI, but no tools exist
- **Procurement** — Evaluating AI vendors without knowing their training data lineage
- **General Counsel** — Perplexity lawsuit, NYT v. OpenAI, Getty v. Stability — who's next?

**How bad:**
- **Perplexity lawsuit (2024)** — Forbes, NYT suing over content scraping; no way for Perplexity to prove clean provenance
- **Mercor data breach (2025)** — Candidate data leaked; no audit trail of how it was used in training
- **Getty v. Stability** — $1.8B copyright suit; Stability can't prove what was/wasn't in training data
- **EU AI Act** — Requires training data documentation; most companies can't comply
- **Enterprise paralysis** — Legal blocking AI adoption because "we don't know where it comes from"

**The gap:**
MLOps tools track experiments, deployments, metrics. NO ONE tracks data provenance end-to-end:
- What datasets went into which training run?
- What was the license status of each data source?
- Which outputs came from which model version?
- Can we prove we DIDN'T train on specific content?

## Solution

**What we build:**
End-to-end AI provenance platform — from data ingestion to model output, with audit trails that satisfy legal.

**Core features:**
1. **Data Catalog** — Track every dataset, source, license, ingestion date, transformations
2. **Training Lineage** — Which data → which model version → which deployment
3. **Output Provenance** — Trace any model output back to training data (where possible)
4. **License Compliance** — Automated license scanning, conflict detection, risk scoring
5. **Audit Reports** — One-click reports for legal, regulators, litigation
6. **Negative Attestation** — Prove specific content was NOT in training data

**How it works:**
- Integrations with ML platforms (MLflow, Weights & Biases, SageMaker, Vertex)
- Data source connectors (S3, GCS, Snowflake, Databricks)
- Automated license detection (package scanning, web source analysis)
- Cryptographic audit trail (tamper-evident logs)
- Query interface: "Show me everything related to NYT content"

**Key output:**
```
PROVENANCE REPORT: model-v2.3.1
Generated: 2026-04-07

DATA SOURCES (47 total):
├── Common Crawl (CC-BY) — 2.1TB — Ingested 2026-01-15
├── Wikipedia (CC-BY-SA) — 180GB — Ingested 2026-01-15
├── Internal docs (Proprietary) — 50GB — Ingested 2026-02-01
└── ...

LICENSE STATUS: ⚠️ ATTENTION REQUIRED
- 3 sources have unclear licenses (requires legal review)
- 1 source (Reddit API) has updated TOS since ingestion

TRAINING LINEAGE:
- Base model: Llama-3-70B (Meta license)
- Fine-tune run: ft-2026-02-15-abc123
- Deployment: prod-east-2026-03-01

NEGATIVE ATTESTATION:
- NYT content: NOT PRESENT (verified)
- Getty images: NOT PRESENT (verified)
```

## Why Now

1. **Litigation wave hitting** — Perplexity, NYT v. OpenAI, Getty v. Stability; every enterprise watching nervously
2. **EU AI Act enforcement (2026)** — Training data documentation now legally required
3. **Enterprise AI adoption inflection** — Companies want to deploy but legal is blocking
4. **MLOps maturity** — Teams already use MLflow/W&B; provenance is natural extension
5. **Insurance pressure** — AI liability insurance now asking about data governance
6. **Board-level visibility** — Audit committees asking "what's our AI risk exposure?"

## Market Landscape

**TAM:** $15B (data governance + MLOps + compliance automation)
**SAM:** $800M (AI-specific data provenance and compliance for enterprise)
**SOM Year 1:** $5-10M (100-200 enterprises at $50-100K/year)

**Competitors:**

| Company | What They Do | Gap |
|---------|--------------|-----|
| **MLflow** | Experiment tracking | No data provenance, no license compliance |
| **Weights & Biases** | ML platform | Artifacts tracked but no legal/compliance focus |
| **DataRobot** | AutoML | Model-centric, not data-centric provenance |
| **Collibra** | Data governance | Traditional data, not AI/ML specific |
| **Alation** | Data catalog | Discovery not provenance, no ML focus |
| **Securiti.ai** | Data privacy | Privacy focus, not AI training provenance |
| **BigID** | Data intelligence | Discovery and privacy, not ML training |
| **Fiddler AI** | Model monitoring | Post-deployment monitoring, not provenance |

**No one is doing:** End-to-end AI training data provenance with license compliance and legal-grade audit trails.

## Competitive Advantages

1. **Legal-first design** — Built for compliance officers, not just ML engineers
2. **Negative attestation** — Prove you DIDN'T train on something (unique capability)
3. **License intelligence** — Automated scanning and conflict detection
4. **Integration depth** — Works with existing MLOps stack (not replace)
5. **Cryptographic audit trail** — Tamper-evident, court-admissible
6. **Regulatory timing** — EU AI Act creates mandatory demand

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Source Connectors                    │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│ Cloud       │ Data        │ ML          │ Web Sources      │
│ Storage     │ Warehouses  │ Platforms   │ (Crawl Logs)     │
│ S3/GCS/Azure│ Snowflake   │ MLflow/W&B  │                  │
└──────┬──────┴──────┬──────┴──────┬──────┴────────┬─────────┘
       │             │             │               │
       ▼             ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ingestion & Analysis                      │
│  - Content fingerprinting (hash, embeddings)                │
│  - License detection (SPDX, custom rules)                   │
│  - Source attribution                                       │
│  - Metadata extraction                                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Provenance Graph (Neo4j + Postgres)             │
│  - Data sources → Datasets → Training runs → Models        │
│  - Immutable audit log (append-only)                        │
│  - Cryptographic integrity (Merkle tree)                    │
│  - Query interface (Cypher + SQL)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Compliance Engine                         │
│  - License conflict detection                               │
│  - Risk scoring by source                                   │
│  - Policy enforcement                                       │
│  - Negative attestation queries                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output Layer                              │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│ Dashboard   │ API         │ Audit       │ Integrations     │
│ (Viz, Query)│ (GraphQL)   │ Reports     │ (GRC, Legal)     │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

**Tech stack:**
- Neo4j for provenance graph (relationships are first-class)
- PostgreSQL for structured metadata
- MinHash/SimHash for content fingerprinting
- SPDX + custom rules for license detection
- GraphQL API for flexible queries
- React dashboard
- SOC 2 + GDPR compliant infrastructure

## Build Plan

### Phase 1: Foundation (Months 1-4)
- [ ] Core provenance graph schema
- [ ] Connectors for top 3 ML platforms (MLflow, W&B, SageMaker)
- [ ] Basic license detection (SPDX + common patterns)
- [ ] Simple dashboard with lineage visualization
- [ ] Land 3-5 design partners (F500 enterprises with AI litigation concern)
- **Milestone:** Working system, 5 pilots, $100K pilot revenue

### Phase 2: Compliance Engine (Months 5-9)
- [ ] Advanced license intelligence (conflict detection, risk scoring)
- [ ] Negative attestation capability ("prove X not in training data")
- [ ] Audit report generation (PDF, legal-ready format)
- [ ] GRC integrations (ServiceNow, OneTrust, Archer)
- [ ] More connectors (Vertex, Azure ML, Databricks)
- [ ] SOC 2 Type 1 certification
- **Milestone:** $500K ARR, 15 enterprise customers, legal teams as champions

### Phase 3: Platform (Months 10-18)
- [ ] Cryptographic audit trail (tamper-evident, court-admissible)
- [ ] Output-to-source tracing (experimental, for retrievable models)
- [ ] Vendor assessment module (evaluate third-party AI providers)
- [ ] EU AI Act compliance templates
- [ ] On-premise deployment for regulated industries
- [ ] Insurance partnership (data for underwriting)
- **Milestone:** $1.5M ARR, 40+ customers, recognized standard for AI provenance

## Risks & Challenges

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Technical limitation: can't trace closed models** | High | Focus on enterprise-trained models; vendor attestation for third-party |
| **Enterprise sales cycle (6-12 months)** | High | Start with litigation-motivated buyers (urgent need) |
| **MLOps platforms add provenance features** | Medium | Go deeper on compliance/legal; they won't prioritize legal-grade audits |
| **False sense of security** | Medium | Clear documentation of what provenance can/can't prove |
| **Data sensitivity concerns** | Medium | On-prem option, metadata-only mode, strong security posture |
| **Regulatory requirements don't materialize** | Low | EU AI Act already passed; litigation pressure independent of regulation |

## Monetization

**Pricing tiers:**

| Tier | Price | Includes |
|------|-------|----------|
| **Team** | $30K/year | 5 users, 10 models, basic connectors, email support |
| **Business** | $75K/year | 25 users, 50 models, all connectors, license intelligence |
| **Enterprise** | $150K+/year | Unlimited, on-prem option, GRC integrations, dedicated CSM |
| **Litigation Support** | $50K+ one-time | Expert analysis, court-ready documentation, expert witness |

**Path to $1M ARR:**
- 8 Enterprise ($150K) = $1.2M
- OR: 5 Enterprise + 5 Business + 3 Litigation = $1.3M
- Timeline: 14-18 months (enterprise sales cycle)

**Expansion revenue:**
- Vendor assessment module (evaluate AI providers)
- Insurance data licensing (anonymized risk data)
- Compliance certification programs

## Verdict

### 🟢 BUILD

**Rationale:**

1. **Existential enterprise need** — Legal blocking AI adoption; this unlocks it
2. **Regulatory tailwind** — EU AI Act makes this mandatory, not optional
3. **Litigation urgency** — Every enterprise watching Perplexity/NYT cases nervously
4. **Clear buyer** — GC, CISO, Chief Data Officer — budget holders with authority
5. **High ACV** — $75-150K/year is realistic for compliance tooling
6. **Timing** — Litigation wave + EU AI Act enforcement = now

**Concerns:**
- Enterprise sales cycle is long (12-18 months typical)
- Technical limitations on closed/third-party models
- Need domain expertise (legal + ML + compliance)

**Recommendation:** Lead with litigation-motivated buyers (companies already facing AI lawsuits or subpoenas). They have urgency. Build credibility with 3-5 marquee logos, then expand to "preventive" buyers. The EU AI Act deadline (2026-2027) creates a forcing function.

**Key insight:** This isn't just about tracking data — it's about giving enterprises the confidence to deploy AI. Legal is the blocker; provenance is the unlocker.
