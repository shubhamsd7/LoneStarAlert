# TxAlert — Team Architecture for 3 People
### Managing 5 Technical Layers Across Backend, ML, and Frontend

---

## Team Structure

```
🧠 Engineer 1: Backend + Data Lead
   Owns: LAYER 0 (Data Ingestion) + LAYER 1 (Entity Resolution)
   
🤖 Engineer 2: ML + Algorithms Lead  
   Owns: LAYER 2 (Risk Modeling) + LAYER 3 (Pattern Detection)
   
💻 Engineer 3: Frontend + Visualization Lead
   Owns: LAYER 4 (Alert Generation UX) + LAYER 5 (Visualization)
```

---

## Engineer 1: Backend + Data Lead

**Title:** Data Platform Engineer  
**Repos:** `layer1_entity/`, `services/`, `models/`, `agents/court_monitor.py`

### Responsibilities

#### LAYER 0 — Data Ingestion (Existing Foundation)
- **Maintain:** `court_scraper.py` — Harris + Travis County portal queries
- **Maintain:** `property_lookup.py` — TCAD integration
- **Monitor:** API rate limits, portal schema changes
- **Test data:** Create 3-5 synthetic court cases for demo pipeline

#### LAYER 1 — Entity Resolution Engine (NEW)
- **Build:** `layer1_entity/entity_resolver.py`
  - Fuzzy name matching (Levenshtein distance)
  - Multi-variant handling: "John Smith" = "J. Smith" = "Jonathan Smith"
  - Handle collectors: "LVNV Funding LLC" = "Resurgent Capital Services"
  - Caching for performance
  
- **Build:** `layer1_entity/llc_graph.py`
  - Traverse Texas SOS corporate filings
  - Build ownership chains: Collector → Parent → Ultimate Owner
  - Store graph in-memory or light database
  - Result: one canonical entity per lawsuit plaintiff
  
- **Extend:** `models/case.py`
  - Add `resolved_entity_id` field
  - Add `entity_graph: dict` with ownership chain
  - Add `entity_confidence_score: float` (0-1)

#### Integration Points
- **Input:** Raw cases from `court_scraper.py`
- **Output:** Enriched cases with `resolved_entity_id` → goes to LAYER 2
- **Interface:** `async def resolve_entity(plaintiff_name: str, case_type: str) -> dict`

### Deliverables

| Milestone | Task | Done By |
|---|---|---|
| Day 1 (morning) | Fuzzy matching working for 10 test names | ✅ |
| Day 1 (evening) | LLC graph traversal pulling from Texas SOS | ✅ |
| Day 2 (morning) | Integration test: raw case → resolved entity | ✅ |
| Day 2 (afternoon) | Handle 3 edge cases (missing SOS data, ambiguous LLC names) | ✅ |

### Testing

```python
# test_entity_resolution.py
def test_fuzzy_match_variations():
    """All variations resolve to same entity"""
    names = ["LVNV Funding LLC", "lvnv funding", "L.V.N.V.", "Resurgent Capital"]
    resolved = [resolve_entity(n) for n in names]
    assert len(set(resolved)) == 1  # All same entity
    
def test_llc_ownership_chain():
    """Follow ownership from subsidiary to parent"""
    child_llc = "LVNV Funding LLC"
    graph = get_ownership_graph(child_llc)
    assert "Resurgent Capital" in graph.parents
    assert len(graph.all_subsidiaries) == 47
```

### Failure Modes & Fallbacks

| Failure | Impact | Fallback |
|---|---|---|
| Texas SOS API down | No LLC graph data | Use cached graph from last 24 hours |
| Fuzzy match ambiguous | Can't resolve entity uniquely | Mark with `confidence_score: 0.3`, pass through with plaintiff_name as entity |
| Collector not in SOS | No ownership data | Fall back to plaintiff_name as canonical entity |

---

## Engineer 2: ML + Algorithms Lead

**Title:** Machine Learning Engineer  
**Repos:** `layer2_risk/`, `layer3_patterns/`, `ml/`

### Responsibilities

#### LAYER 2 — Default Risk Model (NEW)
- **Build:** `layer2_risk/feature_engineer.py`
  - Extract 10-15 features per case:
    - Case type (Justice Court = higher risk)
    - Claim amount (high $ = more likely to pursue)
    - Plaintiff type (debt collector vs. city)
    - Collection agency win rate in county (from `collector_scorer.py`)
    - Claim age (older = past limitations)
    - Defendant's previous case history (if available)
    - Time of filing (holiday/weekend = lower service probability)
    - Plaintiff litigation frequency (pattern)
    - County (some counties favor plaintiffs)
    - Case metadata (error indicators, missing fields)
  - Return: normalized feature vector
  
- **Build:** `layer2_risk/risk_model.py`
  - Train GradientBoostingClassifier on historical cases
  - Label data: cases where defendant DID respond (default=0) vs. did NOT respond (default=1)
  - Output: probability 0-100 that defendant loses by default
  - Save model: `ml/models/risk_model.pkl`
  - Include feature importance analysis
  
- **Build:** `ml/training/model_training.py`
  - Historical case dataset (use court records from past 2 years)
  - Train/test split (80/20)
  - Cross-validation for model stability
  - Generate model metrics: accuracy, precision, recall, AUC-ROC

- **Extend:** `models/case.py`
  - Add `default_risk_score: float` (0-100)
  - Add `risk_confidence: float` (0-1)
  - Add `feature_vector: list[float]`

#### LAYER 3 — Pattern Detection (NEW)
- **Build:** `layer3_patterns/pattern_detector.py`
  - Time series analysis: per entity, analyze filing frequency
  - Anomaly detection on:
    - Bulk filing days (filed 50+ cases in one day = predatory?)
    - Holiday/weekend targeting (lower service rate expected)
    - ZIP code concentration (targeting low-income areas?)
    - Seasonal patterns (court open dates, collector cycles)
  - Return: `PatternAlert` with description + severity
  
- **Use:** Statistical methods
  - ARIMA for time series decomposition
  - Isolation Forest or Local Outlier Factor for anomalies
  - DBSCAN for geographic clustering

- **Extend:** `models/case.py` + new `models/pattern.py`
  - Add `pattern_anomaly_score: float` (0-1)
  - Add `pattern_description: str` ("Collector filed 120 cases in 3 days")
  - Add `geographic_anomaly_score: float` (0-1)
  - Add `zip_cluster_label: str` ("Predatory ZIP targeting detected")

#### Integration Points
- **Input:** Resolved entities (from LAYER 1) → case features
- **Output:** Risk scores + pattern alerts → goes to LAYER 4 (alerts)
- **Interface:** 
  ```python
  async def score_risk(features: list[float]) -> float
  async def detect_patterns(entity_id: str, cases: list[dict]) -> PatternAlert
  ```

### Deliverables

| Milestone | Task | Done By |
|---|---|---|
| Day 1 (morning) | Feature engineering pipeline for 10 cases | ✅ |
| Day 1 (evening) | Model training script with synthetic data | ✅ |
| Day 2 (morning) | Risk scoring working end-to-end | ✅ |
| Day 2 (afternoon) | Pattern detection + anomaly scoring | ✅ |
| Day 2 (evening) | Model accuracy validated on test set | ✅ |

### Testing

```python
# test_risk_modeling.py
def test_feature_engineering():
    """Feature vector shape and normalization"""
    case = {case_type: "justice_court", amount: 5000, ...}
    features = engineer_features(case)
    assert len(features) == 15
    assert all(0 <= f <= 1 for f in features)
    
def test_model_prediction():
    """Risk scores are sensible"""
    cases = [high_risk_case, low_risk_case]
    scores = [score_risk(engineer_features(c)) for c in cases]
    assert scores[0] > scores[1]  # high risk > low risk

# test_pattern_detection.py
def test_bulk_filing_anomaly():
    """Detect bulk filing days"""
    cases = [100 cases filed on same day]
    alert = detect_patterns("entity_123", cases)
    assert alert.severity == "HIGH"
    assert "bulk filing" in alert.description
```

### Failure Modes & Fallbacks

| Failure | Impact | Fallback |
|---|---|---|
| Model not trained | Can't score risk | Default risk = 50% for all cases |
| Feature engineering fails | Can't score | Skip risk scoring, pass case as-is to Layer 4 |
| Pattern detection insufficient data | Can't detect patterns | Skip pattern alerts, mark as "insufficient history" |
| Model accuracy <60% | Unreliable predictions | Use model + human override flag in alert |

---

## Engineer 3: Frontend + Visualization Lead

**Title:** Frontend + UX Engineer  
**Repos:** `frontend/src/`, `agents/alert_generator.py`, `services/miro_service.py`

### Responsibilities

#### LAYER 4 — Alert Generation (Existing Code + Enhancement)
- **Enhance:** `agents/alert_generator.py`
  - Input: case + risk score + patterns from LAYER 2
  - Generate alert text that includes:
    - Case basics: plaintiff, case number, deadline
    - Risk assessment: "87% chance of losing by default"
    - Pattern info: "This collector filed 120 cases in 3 days"
    - Deadline urgency: "11 days remaining — TIME CRITICAL"
    - Defense suggestion: "Your debt is from 2019 — past 4-year limit. Consider this in your response."
  - Output: Plain English alert ready for frontend
  
- **Maintain:** Pre-filled Answer form generation
  - Case-specific form based on case type
  - Interactive PDF or web form
  - Link to legal aid finder

#### LAYER 5 — Visualization + Miro Board (Existing + Enhanced)
- **Enhance:** `frontend/src/components/AlertDashboard.tsx`
  - Show each alert with:
    - Risk score (color-coded: red 80+, yellow 50-80, green <50)
    - Deadline countdown timer
    - Pattern badge if anomaly detected
    - "View case details" → expands to full CaseCard
  
- **Build:** `frontend/src/components/RiskScoreCard.tsx` (NEW)
  - Display risk score as percentage
  - Show feature importance (which factors matter most?)
  - Tooltip: "This collector wins 94% of cases. Respond quickly."
  
- **Build:** `frontend/src/components/PatternAlert.tsx` (NEW)
  - Show pattern anomalies discovered
  - "Collector filed 120 cases in one week"
  - "85% of cases against low-income ZIP codes"
  
- **Enhance:** `services/miro_service.py`
  - When alert fires: auto-post to Miro board
  - Include:
    - Case card (left): plaintiff, amount, deadline
    - Timeline (center): filed → served → deadline → hearing
    - Risk indicator (top right): "87% default probability"
    - Pattern notes (bottom): anomalies detected
    - Action checklist (right): what to do next

#### Integration Points
- **Input:** Risk scores + patterns from LAYER 2
- **Output:** User-facing alerts + Miro visualizations
- **Interfaces:**
  ```python
  async def generate_alert_text(case: dict, risk: float, patterns: PatternAlert) -> str
  async def post_alert_to_miro(alert: dict, risk: float) -> str
  ```

### Deliverables

| Milestone | Task | Done By |
|---|---|---|
| Day 1 (morning) | AlertDashboard component showing mock alerts | ✅ |
| Day 1 (evening) | RiskScoreCard displaying risk with colors | ✅ |
| Day 2 (morning) | PatternAlert component for anomalies | ✅ |
| Day 2 (afternoon) | Miro integration posting alerts live | ✅ |
| Day 2 (evening) | End-to-end demo: case → alert → dashboard → Miro | ✅ |

### Testing

```python
# test_alert_generation.py
def test_alert_text_includes_risk():
    """Generated alert mentions risk score"""
    case = {...}
    alert = generate_alert_text(case, risk_score=87, patterns=None)
    assert "87" in alert
    assert "percent" in alert or "%" in alert

# test_miro_posting.py
def test_miro_integration():
    """Alert successfully posted to Miro"""
    miro_id = post_alert_to_miro(test_alert, risk=87)
    assert miro_id is not None
    # Verify on Miro board
```

### Failure Modes & Fallbacks

| Failure | Impact | Fallback |
|---|---|---|
| Miro API down | Can't post visual board | Show error toast, store alert locally, retry |
| Risk score missing | Can't display risk | Show "Risk assessment unavailable" |
| Pattern data malformed | Can't display patterns | Hide pattern section, show alert without it |

---

## Data Flow: Integration Map

```
┌─────────────────────────────────────────────────────────┐
│ Raw Court Case (from court_scraper.py)                  │
│ {plaintiff: "LVNV Funding LLC", amount: $5000, ...}     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼ [Engineer 1: Entity Resolution]
┌─────────────────────────────────────────────────────────┐
│ Resolved Entity (entity_resolver.py)                    │
│ {entity_id: "resurgent_capital_123",                    │
│  subsidiary_of: "Resurgent Capital Services",           │
│  confidence: 0.95}                                      │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼ [Engineer 2: Features]    ▼ [Engineer 2: Patterns]
┌──────────────────────┐      ┌──────────────────────────┐
│ Feature Vector       │      │ Pattern Detection        │
│ [0.2, 0.8, 0.1...]  │      │ {bulk_filing: true,      │
│ (normalized)        │      │  zip_predation: HIGH}    │
└──────────┬───────────┘      └──────────────┬───────────┘
           │                                 │
           └──────────────┬──────────────────┘
                          │
                  ▼ [Engineer 2: Risk Model]
         ┌─────────────────────────────────┐
         │ Risk Score                      │
         │ {score: 87, confidence: 0.92}   │
         └──────────────┬────────────────┘
                        │
              ┌─────────┴────────┐
              │                  │
              ▼ [Engineer 3]     ▼ [Engineer 3]
         ┌─────────────────┐  ┌──────────────┐
         │ Alert Text      │  │ Miro Card    │
         │ + Form          │  │ Visual       │
         │ + Legal Aid     │  │ Dashboard    │
         └─────────────────┘  └──────────────┘
              │                     │
              └────────┬────────────┘
                       │
                       ▼ User sees alert + board
```

---

## Dependencies & Blocking

```
Engineer 1's work must finish FIRST:
  └─ entity_resolver.py + llc_graph.py
     (needed for Engineer 2's pattern detection)

Engineer 2 can start after Engineer 1:
  └─ feature_engineer.py (needs resolved entities)
  └─ risk_model.py (needs features)
  └─ pattern_detector.py (needs entity history)

Engineer 3 can start in parallel with Engineer 2:
  └─ mock risk scores in frontend
  └─ mock patterns in frontend
  └─ integrate real scores from Engineer 2 later
```

---

## Critical Path to Demo

**Friday Night — Hour 0 to 4**
- Engineer 1: Entity resolver working on 5 test cases
- Engineer 2: Feature engineering pipeline ready
- Engineer 3: Dashboard mockup with placeholder data

**Saturday Morning — Hour 8 to 12**
- Engineer 1: LLC graph pulling from Texas SOS
- Engineer 2: Risk model trained and scoring
- Engineer 3: AlertDashboard + PatternAlert components

**Saturday Afternoon — Hour 12 to 18**
- Engineer 1: End-to-end test: scraper → resolver → ready for Layer 2
- Engineer 2: Risk + pattern scores live
- Engineer 3: Miro integration working

**Saturday Evening — Hour 18 to 22**
- Engineer 1: Load demo data set
- Engineer 2: Validate model accuracy
- Engineer 3: Full UI polish + demo script

**Sunday Morning — Hour 22+**
- Code freeze
- Demo rehearsal
- Ship

---

## Standup Questions (Daily)

**Engineer 1:**
- [ ] Entity resolver confidence score? (target: >90% for known plaintiffs)
- [ ] LLC graph coverage? (what % of plaintiffs have SOS data?)
- [ ] Integration with Engineer 2 blocked on anything?

**Engineer 2:**
- [ ] Model accuracy on test set? (target: >75%)
- [ ] Sufficient historical data? (need N cases to train)
- [ ] Pattern detection working on demo data?

**Engineer 3:**
- [ ] Dashboard rendering risk scores correctly?
- [ ] Miro API credentials working?
- [ ] Demo flow smooth end-to-end?

---

## Success Metrics

| Layer | Success Criteria |
|---|---|
| LAYER 0 | Court scraper returns 10+ real cases ✅ |
| LAYER 1 | Entity resolver disambiguates 5 test collectors ✅ |
| LAYER 2 | Risk model achieves >75% accuracy on test set ✅ |
| LAYER 3 | Pattern detector flags bulk filing anomaly ✅ |
| LAYER 4 | Alert text mentions risk + patterns + deadline ✅ |
| LAYER 5 | Miro board auto-populates when alert fires ✅ |

---

## Communication Protocol

- **Real-time:** Slack #txalert-dev
- **Blockers:** Tag @engineer immediately
- **Daily standup:** 9am + 4pm (5 min each)
- **Handoff meetings:**
  - Engineer 1 → 2: Saturday 9am (entity format + quality)
  - Engineer 2 → 3: Saturday 1pm (risk/pattern output format)

---

## Glossary

- **Canonical Entity:** Single, unified identifier for a plaintiff (e.g., "Resurgent Capital" even if filed as "LVNV Funding LLC")
- **Feature Vector:** Normalized list of numeric features for ML model input
- **Default Probability:** Predicted likelihood defendant loses without responding
- **Anomaly Score:** 0-1 metric for how unusual a filing pattern is
- **Confidence Score:** 0-1 metric for how sure the system is about a prediction

---

*Built for speed. Built for impact. Built to prevent someone from losing their home.*
