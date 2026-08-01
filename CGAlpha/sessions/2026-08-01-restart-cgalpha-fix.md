---
title: CGAlpha restart-cgalpha Fix - Complete Restart Protocol Implementation
date: 2026-08-01
category: CGAlpha/development
tags: [restart-cgalpha, gui, watchdog, cloud-infra, protocol]
status: complete
---

# CGAlpha restart-cgalpha Complete Fix - 2026-08-01

## Summary
Updated the `restart-cgalpha` script and alias to include the **full restart protocol** from `prompt_reinicio_cgalpha.md`, covering:
1. Cloud infrastructure verification (R2, CloudSync)
2. GUI Server startup with verification (port 8080, HTTP 200)
3. Watchdog startup with verification (Check result: OK)
4. Full 5-criteria verification per protocol

## Changes Made

### 1. Script: `/home/vaclav/bin/restart-cgalpha`
- Complete rewrite combining cloud restart + GUI/Watchdog protocol
- Uses `PYTHONPATH=. python3 cgalpha_v3/gui/server.py` (fixed ModuleNotFoundError bug from original protocol Step 3)
- Proper venv activation from `.venv/bin/activate`
- 12s wait for GUI init, 5s for watchdog
- Verifies all 5 success criteria:
  - ✅ 2 processes (GUI + Watchdog)
  - ✅ Port 8080 LISTEN
  - ✅ Heartbeat price > 10000 (BTC, not ETH)
  - ✅ Heartbeat aggtrade_gap_ms < 30000
  - ✅ Watchdog log shows "Check result: OK"

### 2. Alias in `.bashrc` (line 140)
```bash
alias cgalpha-restart="cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3 && bash documentation/prompts/prompt_reinicio_cgalpha.md"
```
Note: This alias points to the markdown file (which doesn't execute as script). The **function** `restart-cgalpha()` at line 145 runs the actual script from `~/bin/restart-cgalpha`.

## Verification Results (2026-08-01 16:35)

| Criterion | Status | Value |
|-----------|--------|-------|
| GUI HTTP 200 | ✅ | 200 |
| Port 8080 LISTEN | ✅ | tcp 0.0.0.0:8080 |
| Processes (GUI + Watchdog) | ✅ | 2 core processes running |
| Heartbeat price | ✅ | 63,105.41 (> 10000) |
| Heartbeat gap | ✅ | 194ms (< 30000ms) |
| Watchdog Check result | ✅ | "Check result: OK" in logs |

## Protocol Reference
Source: `/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3/documentation/prompts/prompt_reinicio_cgalpha.md`

Key fix from original protocol:
- **Step 3 bug**: Used `python3 -m cgalpha_v3.gui.server` → **Fixed to** `PYTHONPATH=. python3 cgalpha_v3/gui/server.py`
- Commit: `5b91874` pushed

## Usage
```bash
restart-cgalpha  # Runs complete cloud + GUI + watchdog verification
```

---

## LLM External Response - Key Findings (Saved for Reference)

### 1) TabPFN Licensing — Critical Discovery
**TabPFN-2.5/3 NOT usable in production** — license allows only testing/evaluation/benchmarking. Commercial/production use (including internal trading decisions) explicitly prohibited.

**Recommendation**: Use 2.5/3 for benchmark shootout only. If it wins, production choice is:
- (a) TabPFN v2 (Apache 2.0 + attribution) — may lose performance
- (b) Negotiate commercial license with Prior Labs

### 2) LightGBM Hyperparameters for 358 FULL
```python
num_leaves: 7–15
max_depth: 3–5
min_child_samples: 15–25
learning_rate: 0.01–0.05
n_estimators: 500–2000 (early_stopping_rounds=50)
feature_fraction: 0.6–0.8
bagging_fraction: 0.7–0.8, bagging_freq: 1
lambda_l1/lambda_l2: grid [0.0, 1.0]
is_unbalance=True
# Determinism: deterministic=True, force_row_wise=True, num_threads=1, fixed seeds
```

### 3) SHAP on 358×50 — CPU Time
TreeSHAP = seconds, not minutes. Use `TreeExplainer` (never `KernelExplainer`). Background = full training set. LightGBM/XGBoost: use native `pred_contrib=True`.

### 4) Online Learning A/B Test
Don't compare SGDClassifier vs RF (mixes model family + cadence). Compare **same model, two cadences**:
- SGDClassifier(partial_fit) vs LogisticRegression retrained every N
- Or River's Hoeffding Trees vs RF batch
- Expected: marginal difference at 1-3 samples/day

### 5) MaxDD Bootstrap CI
- **Block bootstrap** (not IID) — block size ~√N ≈ 19 trades
- **5,000-10,000 resamples** — cheap, reduces Monte Carlo noise
- Report **95th percentile** as risk planning number (not median)
- CI: 5th/95th (90%) — interval width = how much more data needed

### 6) Slippage Model with bid_wall_depth_10_btc
2-segment model (best level + depth-10 aggregate). Calibrate `depth_price_range_bps` against real fills. Track fill probability empirically for limit orders.

### Closing Two "Debilidades" with Code

```python
def test_rf_deterministic_across_njobs():
    X, y = load_training_data()
    p1 = RandomForestClassifier(random_state=42, n_jobs=1).fit(X, y).predict_proba(X)
    p2 = RandomForestClassifier(random_state=42, n_jobs=-1).fit(X, y).predict_proba(X)
    assert np.allclose(p1, p2, atol=1e-10), "n_jobs rompe el determinismo"

def test_rf_reproducible_same_seed():
    X, y = load_training_data()
    rf1 = RandomForestClassifier(random_state=42).fit(X, y)
    rf2 = RandomForestClassifier(random_state=42).fit(X, y)
    assert np.array_equal(rf1.predict(X), rf2.predict(X))
```

**Logistic Regression sanity-check**: `CalibratedClassifierCV(method='sigmoid', cv=5)` — Platt scaling, not isotonic (overfits at 250-300 samples/fold).

### Priority Unchanged
1. MAE regressor
2. Shootout (with licensing caveat)
3. Cost model

The TabPFN licensing finding means: shootout is valid research under license, but **deployment is a separate conversation**.