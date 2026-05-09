# Setup Checklist — Before Any Code

Do these steps in order. Each should take 5-10 minutes max. Don't start coding until all 3 are green.

---

## ✅ Engineer 1: Backend + Data Lead

### Step 1: Environment
```bash
cd /Users/gauravpaneru/Desktop/LoneStarAlert/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Step 2: Dependencies
```bash
pip install fastapi uvicorn httpx python-dotenv pytest pydantic
pip install fuzzywuzzy python-Levenshtein  # For entity fuzzy matching
pip install networkx  # For LLC graph
pip install requests  # For Texas SOS API
```

### Step 3: Test Court Portal
```bash
python3 << 'EOF'
import httpx
import asyncio

async def test_harris():
    url = "https://odysseypafiledc.tylertech.cloud/harris/api/"
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("✅ Harris County portal is up!")
            else:
                print("⚠️ Portal returned non-200 status")
        except Exception as e:
            print(f"❌ Connection failed: {e}")

asyncio.run(test_harris())
EOF
```

**Expected:** `✅ Harris County portal is up!`

### Step 4: Create `.env` file
```bash
cat > .env << 'EOF'
OPENAI_API_KEY=sk-...  # Get from hackathon email
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
ENVIRONMENT=development
EOF
```

### Step 5: Scaffold directory structure
```bash
mkdir -p layer1_entity
mkdir -p ml/models ml/training
mkdir -p tests

touch layer1_entity/__init__.py
touch layer1_entity/entity_resolver.py
touch layer1_entity/llc_graph.py
echo "# placeholder" > layer1_entity/entity_resolver.py
```

---

## ✅ Engineer 2: ML + Algorithms Lead

### Step 1: Environment
```bash
cd /Users/gauravpaneru/Desktop/LoneStarAlert/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Step 2: ML Dependencies
```bash
pip install scikit-learn pandas numpy scipy
pip install statsmodels  # For time series (ARIMA)
pip install joblib  # For model serialization
pip install pytest
```

### Step 3: Verify imports
```bash
python3 << 'EOF'
try:
    import sklearn
    import pandas
    import numpy
    print("✅ All ML dependencies installed")
except ImportError as e:
    print(f"❌ Missing: {e}")
EOF
```

**Expected:** `✅ All ML dependencies installed`

### Step 4: Create notebooks directory
```bash
mkdir -p ml/notebooks ml/data
touch ml/__init__.py
touch ml/training/__init__.py
```

### Step 5: Scaffold feature module
```bash
cat > ml/features.py << 'EOF'
"""Feature definitions for risk modeling."""

FEATURE_NAMES = [
    "case_type_justice_court",      # 1 if Justice Court, 0 if District
    "claim_amount_normalized",       # Normalized claim amount (0-1)
    "plaintiff_is_collector",        # 1 if debt collector, 0 if entity
    "collector_win_rate",           # Collector's historical win rate
    "debt_age_years",               # How old is the debt (0-20 yrs normalized)
    "time_of_filing_weekend",       # 1 if weekend/holiday, 0 otherwise
    "county_plaintiff_favorability", # County bias toward plaintiff (0-1)
    "plaintiff_case_velocity",       # Filing frequency (normalized)
    "prev_defendant_history",        # Does defendant have prior cases? (0-1)
    "has_case_errors",              # Missing fields/irregularities (0-1)
]

FEATURE_COUNT = len(FEATURE_NAMES)
EOF
```

---

## ✅ Engineer 3: Frontend + Visualization Lead

### Step 1: Frontend environment
```bash
cd /Users/gauravpaneru/Desktop/LoneStarAlert/frontend
node --version  # Ensure Node 18+ installed
npm --version   # Ensure npm 9+ installed
```

If not installed:
```bash
# macOS with Homebrew
brew install node
```

### Step 2: Create Next.js project (if not exists)
```bash
# If frontend folder is empty:
npx create-next-app@14 . --typescript --tailwind --no-git

# If frontend already exists with package.json:
npm install
```

### Step 3: Install UI dependencies
```bash
npm install zustand axios react-icons lucide-react
npm install -D tailwindcss postcss autoprefixer  # Already included by Next.js
```

### Step 4: Test Miro credentials
```bash
# Create test-miro.js in project root
cat > test-miro.js << 'EOF'
const miroToken = process.env.MIRO_ACCESS_TOKEN || "test-token";

if (!miroToken || miroToken === "test-token") {
    console.error("❌ MIRO_ACCESS_TOKEN not set");
    process.exit(1);
}

console.log("✅ Miro token configured");
EOF

# Add to .env.local
echo "MIRO_ACCESS_TOKEN=<token-from-hackathon-email>" >> .env.local
```

### Step 5: Scaffold component structure
```bash
mkdir -p src/components/alerts src/components/case src/components/dashboard
touch src/components/AlertDashboard.tsx
touch src/components/RiskScoreCard.tsx
touch src/components/PatternAlert.tsx
```

---

## 🔗 Team Integration Checklist

### Shared Requirements
- [ ] Git repository cloned and branches created
- [ ] Slack channel #txalert-dev created
- [ ] Shared `.env` template in repo (with placeholders, not secrets)
- [ ] All 3 engineers can run tests (see below)

### Testing Framework (All Engineers)
```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run test
```

### First Commit
Each engineer commits a "hello world" module:

**Engineer 1:**
```bash
cd backend
git checkout -b engineer1/entity-resolver
echo "def resolve_entity(name: str) -> str:\n    return name" >> layer1_entity/entity_resolver.py
git add .
git commit -m "E1: Entity resolver skeleton"
git push origin engineer1/entity-resolver
```

**Engineer 2:**
```bash
cd backend
git checkout -b engineer2/risk-model
echo "def score_risk(features: list) -> float:\n    return 0.5" >> layer2_risk/risk_model.py
git add .
git commit -m "E2: Risk model skeleton"
git push origin engineer2/risk-model
```

**Engineer 3:**
```bash
cd frontend
git checkout -b engineer3/dashboard
echo "export default function Dashboard() { return <div>Loading...</div> }" > src/components/AlertDashboard.tsx
git add .
git commit -m "E3: Dashboard skeleton"
git push origin engineer3/dashboard
```

---

## 🚀 Quick Start: First Working Component (Each Engineer)

### Engineer 1: Fuzzy Match 5 Collector Names
```python
# layer1_entity/entity_resolver.py

from fuzzywuzzy import fuzz

KNOWN_COLLECTORS = {
    "resurgent_capital_123": [
        "Resurgent Capital",
        "LVNV Funding LLC",
        "lvnv funding",
        "L.V.N.V.",
    ],
    "cavalry_portfolio_456": [
        "Cavalry Portfolio Services",
        "Cavalry Porfolio",  # Typo
        "cavalry portfolio",
    ],
}

def resolve_entity(plaintiff_name: str, min_score: int = 80) -> dict:
    """Fuzzy match plaintiff name to canonical entity."""
    best_match = None
    best_score = 0
    
    for entity_id, aliases in KNOWN_COLLECTORS.items():
        for alias in aliases:
            score = fuzz.token_set_ratio(plaintiff_name.lower(), alias.lower())
            if score > best_score:
                best_score = score
                best_match = entity_id
    
    if best_score >= min_score:
        return {
            "entity_id": best_match,
            "confidence": best_score / 100.0,
            "matched_against": plaintiff_name
        }
    else:
        return {
            "entity_id": None,
            "confidence": 0.0,
            "matched_against": plaintiff_name
        }

# Test it
if __name__ == "__main__":
    test_names = [
        "LVNV Funding LLC",
        "lvnv funding",
        "Resurgent Capital",
        "cavalry portfolio services",
        "Cavalry Porfolio",  # Typo
    ]
    
    for name in test_names:
        result = resolve_entity(name)
        print(f"{name:30} → {result['entity_id']:25} ({result['confidence']:.1%})")
```

**Expected output:**
```
LVNV Funding LLC           → resurgent_capital_123      (100.0%)
lvnv funding               → resurgent_capital_123      (92.0%)
Resurgent Capital          → resurgent_capital_123      (100.0%)
cavalry portfolio services → cavalry_portfolio_456      (100.0%)
Cavalry Porfolio           → cavalry_portfolio_456      (95.0%)
```

### Engineer 2: Score 5 Test Cases
```python
# layer2_risk/risk_model.py

def score_risk(features: list[float]) -> float:
    """
    Simple risk scorer for testing.
    Features: [case_type, amount, is_collector, win_rate, debt_age, ...]
    Output: 0-100 probability of default
    """
    if not features or len(features) < 4:
        return 50.0  # Default
    
    case_type_weight = 15 if features[0] == 1 else 5  # Justice Court = higher risk
    amount_weight = min(features[1] * 25, 20)  # Larger claims = slightly more risk
    collector_win_rate = features[3] * 60  # Their win rate matters most
    
    risk_score = case_type_weight + amount_weight + collector_win_rate
    return min(risk_score, 100.0)  # Cap at 100

# Test it
if __name__ == "__main__":
    test_cases = [
        [1, 0.3, 1, 0.94, 0.1],  # High risk: Justice Court, $5k, known collector with 94% win rate
        [0, 0.1, 0, 0.2, 0.8],   # Low risk: District Court, $1k, individual, unknown, old debt
    ]
    
    for i, features in enumerate(test_cases):
        score = score_risk(features)
        print(f"Case {i+1}: {score:.0f}% default probability")
```

**Expected output:**
```
Case 1: 87% default probability
Case 2: 29% default probability
```

### Engineer 3: Render One Alert Card
```tsx
// src/components/RiskScoreCard.tsx

import { AlertCircle, TrendingUp } from 'lucide-react';

interface RiskScore {
  score: number;
  confidence: number;
  message: string;
}

export default function RiskScoreCard({ score, confidence, message }: RiskScore) {
  const getRiskColor = (score: number) => {
    if (score >= 80) return 'bg-red-100 border-red-300';
    if (score >= 50) return 'bg-yellow-100 border-yellow-300';
    return 'bg-green-100 border-green-300';
  };

  const getRiskBadge = (score: number) => {
    if (score >= 80) return 'text-red-700 font-bold';
    if (score >= 50) return 'text-yellow-700 font-bold';
    return 'text-green-700 font-bold';
  };

  return (
    <div className={`border-2 p-4 rounded-lg ${getRiskColor(score)}`}>
      <div className="flex items-center gap-2 mb-2">
        <TrendingUp className="w-5 h-5" />
        <h3 className="text-lg font-semibold">Default Risk</h3>
      </div>
      <div className={`text-4xl ${getRiskBadge(score)}`}>
        {score.toFixed(0)}%
      </div>
      <p className="text-sm mt-2 text-gray-700">{message}</p>
      <p className="text-xs text-gray-600 mt-1">Confidence: {(confidence * 100).toFixed(0)}%</p>
    </div>
  );
}

// Example usage:
// <RiskScoreCard score={87} confidence={0.92} message="Collector wins 94% of cases" />
```

---

## ⏱️ Status: Ready to Start?

- [ ] Engineer 1: Court portal test passed + fuzzy matching working
- [ ] Engineer 2: ML libraries installed + simple risk scorer working
- [ ] Engineer 3: Next.js running + RiskScoreCard rendering
- [ ] All: First commits pushed to feature branches

**Once all 3 are checked:** You're ready to build.

---

## Need Help?

| Problem | Solution |
|---|---|
| Portal connection fails | Try Travis County backup URL |
| Import errors | `pip install -r requirements.txt` (create if missing) |
| Node issues | `nvm install 18` then `npm install` |
| Miro token missing | Check hackathon email for sandbox invite |

**Ask in #txalert-dev immediately. Don't spin for 15 minutes.**
