# Module Ownership & Dependencies

## Quick Reference: Who Owns What

```
ENGINEER 1: Backend + Data Lead
├── layer1_entity/
│   ├── entity_resolver.py          (PRIMARY)
│   └── llc_graph.py                (PRIMARY)
├── services/
│   ├── court_scraper.py            (MAINTAIN)
│   └── property_lookup.py          (MAINTAIN)
├── models/
│   └── case.py                     (EXTEND: add resolved_entity fields)
└── agents/
    └── court_monitor.py            (MAINTAIN)

ENGINEER 2: ML + Algorithms Lead
├── layer2_risk/
│   ├── feature_engineer.py         (PRIMARY)
│   └── risk_model.py               (PRIMARY)
├── layer3_patterns/
│   └── pattern_detector.py         (PRIMARY)
├── ml/
│   ├── training/
│   │   └── model_training.py       (PRIMARY)
│   ├── models/
│   │   ├── risk_model.pkl          (OUTPUT)
│   │   └── scaler.pkl              (OUTPUT)
│   └── features.py                 (PRIMARY)
└── models/
    ├── case.py                     (EXTEND: add risk/pattern fields)
    └── pattern.py                  (CREATE NEW)

ENGINEER 3: Frontend + Visualization Lead
├── frontend/src/
│   ├── components/
│   │   ├── AlertDashboard.tsx      (PRIMARY)
│   │   ├── RiskScoreCard.tsx       (NEW)
│   │   ├── PatternAlert.tsx        (NEW)
│   │   ├── CaseCard.tsx            (ENHANCE)
│   │   └── AnswerModal.tsx         (MAINTAIN)
│   ├── lib/
│   │   └── api.ts                  (ENHANCE)
│   └── store/
│       └── alertStore.ts           (ENHANCE)
├── agents/
│   └── alert_generator.py          (ENHANCE: integrate risk + patterns)
└── services/
    └── miro_service.py             (ENHANCE: post risk + patterns)
```

---

## Dependency Graph (Critical Path)

```
┌────────────────────────────────────────────────────────────┐
│ START: Raw court data from court_scraper.py                │
│ {plaintiff: "LVNV Funding LLC", amount: $5000, ...}        │
└────────────────┬─────────────────────────────────────────┘
                 │ [E1 OWNS THIS LAYER]
                 ▼
        ┌────────────────────────┐
        │ LAYER 1: Entity        │
        │ Resolution             │
        │ entity_resolver.py     │
        │ + llc_graph.py         │
        │ OUTPUT: entity_id      │
        │ QUALITY: >90%          │
        └────────────┬───────────┘
                     │
                     │ BLOCKS EVERYTHING
                     │
        ┌────────────┴─────────────┐
        │                          │
        │ [E2 OWNS BOTH PATHS]     │
        │                          │
     Path A: Risk                 Path B: Patterns
    (in parallel)                 (in parallel)
        │                          │
        ▼                          ▼
    Feature Eng.              Pattern Detection
    (feature list)            (anomaly_score)
        │                          │
        └────────┬─────────────────┘
                 │
                 ▼
        ┌──────────────────────┐
        │ Risk Score Output    │
        │ (0-100)              │
        │ + Anomalies Detected │
        └────────┬─────────────┘
                 │
                 │ [E3 OWNS THIS LAYER]
                 │
        ┌────────▼─────────────────┐
        │ LAYER 4: Alert Regen.    │
        │ (enhance existing)       │
        │ OUTPUT: Alert Text +     │
        │ Risk phrase              │
        │ + Pattern description    │
        └────────┬─────────────────┘
                 │
                 │ FINAL PUSH
                 │
        ┌────────▼──────────────────┐
        │ LAYER 5: Visualization    │
        │ Dashboard + Miro          │
        │ + Risk badge + Alerts     │
        └───────────────────────────┘
```

---

## Interface Contracts (What Each Engineer Outputs)

### Engineer 1 → Engineer 2
**Module:** `entity_resolver.py`
```python
async def resolve_entity(plaintiff_name: str, case_type: str) -> dict:
    """
    RETURNS:
    {
        "entity_id": "resurgent_capital_123",
        "canonical_name": "Resurgent Capital Services",
        "confidence_score": 0.95,  # 0-1, min 0.5 acceptable
        "subsidiaries": ["LVNV Funding LLC", "..."],
        "parent_company": "Encore Capital Group",
        "tax_id": "XX-XXXXXXX" (if available)
    }
    """
```
**Quality Gate:** Must resolve >90% of top 100 collectors in Harris County
**Fallback:** If can't resolve confidently, return entity_id=None (E2 skips pattern detection)

### Engineer 2 → Engineer 3
**Module:** `risk_model.py`
```python
def score_risk(features: list[float]) -> float:
    """
    INPUT: 10-15 normalized features (0-1 range)
    OUTPUT: 0-100 probability defendant loses
    """
```

**Module:** `pattern_detector.py`
```python
async def detect_patterns(entity_id: str, case_history: list[dict]) -> dict:
    """
    RETURNS:
    {
        "anomaly_score": 0.87,  # 0-1: how unusual is this pattern
        "pattern_type": "bulk_filing | holiday_targeting | zip_predation",
        "description": "Filed 120 cases on same day",
        "severity": "HIGH | MEDIUM | LOW",
        "confidence": 0.92
    }
    """
```
**Quality Gate:** Must detect ≥1 anomaly in test dataset (synthetic bulk filer)
**Fallback:** If insufficient history (< 5 cases), return anomaly_score=0

### Engineer 3 ← Engineer 2 Data
**Alert Generator Integration:**
```python
def generate_alert_text(case: dict, risk_score: float, patterns: dict) -> str:
    """
    INPUT:
    - case: {plaintiff, amount, deadline, ...}
    - risk_score: 0-100 (from Engineer 2)
    - patterns: {anomaly_score, description, severity} (from Engineer 2)
    
    OUTPUT: Plain English alert string
    
    EXAMPLE:
    "⚠️ HIGH ALERT: LVNV Funding LLC filed against you on May 8.
     You have 11 days to respond (deadline May 19).
     
     RISK ASSESSMENT: 87% chance of losing by default.
     This collector wins 94% of cases where defendants don't respond.
     
     PATTERN: This collector filed 120 cases in one week,
     targeting ZIP codes with median income <$40K.
     
     NEXT STEPS: Download Answer form → Find free legal aid → File before May 19"
    """
```

---

## Testing Plan (Each Engineer Validates Own Work)

### Engineer 1 Test Suite
```python
# tests/test_entity_resolution.py

def test_exact_match_collectors():
    """Top 100 Harris County collectors should resolve with >95% confidence"""
    assert resolve_entity("LVNV Funding LLC").confidence > 0.95
    
def test_fuzzy_match_misspellings():
    """Should handle common misspellings"""
    assert resolve_entity("cavalry porfolio").entity_id is not None
    
def test_llc_chain():
    """Should traverse subsidiary → parent → ultimate owner"""
    graph = get_llc_chain("LVNV Funding LLC")
    assert "Encore Capital Group" in [n.name for n in graph.ancestors]
    
def test_fallback_unknown_plaintiff():
    """Unknown plaintiff returns entity_id=None without crashing"""
    result = resolve_entity("John Smith Lawn Care")
    assert result is not None  # No exception
    assert result["entity_id"] is None or result["confidence"] < 0.5
```

### Engineer 2 Test Suite
```python
# tests/test_risk_modeling.py

def test_feature_engineering_shapes():
    """Feature vector must be 10-15 floats, normalized 0-1"""
    features = engineer_features(sample_case)
    assert len(features) in range(10, 16)
    assert all(0 <= f <= 1 for f in features)
    
def test_model_predicts_high_risk():
    """High-risk case (Justice Court, known collector, recent debt)"""
    high_risk_case = {
        "court_type": "justice",
        "plaintiff_win_rate": 0.94,
        "debt_age_years": 0.5,
    }
    score = score_risk(engineer_features(high_risk_case))
    assert score > 75  # High risk
    
def test_model_predicts_low_risk():
    """Low-risk case (old debt, unknown plaintiff, district court)"""
    low_risk_case = {
        "court_type": "district",
        "plaintiff_win_rate": 0.2,
        "debt_age_years": 5.0,
    }
    score = score_risk(engineer_features(low_risk_case))
    assert score < 30  # Low risk
    
def test_pattern_detection_bulk_filing():
    """Should detect when one entity filed 100+ cases in one day"""
    bulk_cases = [
        {plaintiff_id: "X", filing_date: "2025-05-08"} for _ in range(120)
    ]
    alert = detect_patterns("entity_X", bulk_cases)
    assert alert["anomaly_score"] > 0.8
    assert "bulk" in alert["description"].lower()
```

### Engineer 3 Test Suite
```javascript
// frontend/__tests__/AlertDashboard.test.tsx

describe('AlertDashboard', () => {
    test('renders risk scores with correct colors', () => {
        const { getByText } = render(<AlertDashboard alerts={mockAlerts} />);
        const highRiskCard = getByText('87%');
        expect(highRiskCard).toHaveClass('bg-red-100');
    });
    
    test('displays pattern alerts', () => {
        const alerts = [{
            risk_score: 87,
            patterns: {
                description: "Bulk filing detected"
            }
        }];
        const { getByText } = render(<AlertDashboard alerts={alerts} />);
        expect(getByText(/Bulk filing/)).toBeInTheDocument();
    });
    
    test('miro integration posts on alert', async () => {
        await postAlertToMiro(mockAlert);
        expect(mockMiroAPI.post).toHaveBeenCalled();
    });
});
```

---

## Data Models (Shared)

### Case Model Extensions
```python
# models/case.py

class CourtCase(BaseModel):
    # ... existing fields ...
    
    # [NEW - Engineer 1 fills these]
    resolved_entity_id: str | None = None
    canonical_entity_name: str | None = None
    entity_confidence: float = 0.0  # 0-1
    entity_ownership_chain: dict | None = None
    
    # [NEW - Engineer 2 fills these]
    default_risk_score: float | None = None  # 0-100
    risk_confidence: float = 0.0  # 0-1
    feature_vector: list[float] | None = None
    anomaly_score: float | None = None  # 0-1
    pattern_description: str | None = None
    geographic_anomaly: str | None = None
```

### Pattern Model (NEW)
```python
# models/pattern.py

class PatternAlert(BaseModel):
    entity_id: str
    pattern_type: Literal[
        "bulk_filing",
        "holiday_targeting",
        "zip_code_predation",
        "seasonal_spike",
        "unusual_timing"
    ]
    anomaly_score: float  # 0-1
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    description: str  # Plain English: "Filed 120 cases in one day"
    affected_cases: int
    timeframe: str  # "2025-05-08"
    confidence: float  # 0-1
```

---

## Deployment Checklist (Post-Demo)

- [ ] Engineer 1: Entity resolver accuracy validated >90%
- [ ] Engineer 2: Model accuracy >75% on test set + patterns on historical data
- [ ] Engineer 3: Dashboard + Miro integration manual tested
- [ ] All: No console errors in demo run-through
- [ ] All: Code committed to main branch
- [ ] All: One-page summary of what each engineer built

---

## Common Gotchas

| Issue | Prevention |
|---|---|
| E1 sends bad entity_id format | Define schema in contract early |
| E2 forgets to normalize features | Test with raw vs normalized input |
| E3 UI breaks with missing risk_score | Handle None case in frontend |
| Model takes 5 min to train | Pre-train during setup, save PKL file |
| Miro token expired | Store in .env, refresh before demo |

---

*Last Updated: Day 1*
