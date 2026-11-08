# Aura Bell — Delivery Fee Economic Analysis

**Review Date:** 2026-11-08  
**Reviewer:** Independent Architecture Reviewer  
**Focus:** Flat delivery fee policy economics, cost allocation, financial exposure

---

## Owner Decision Context

**DEC-OWN-003 (CONFIRMED 2026-11-08):**
- **Decision**: Flat delivery fee per order (single fee regardless of stores/shipments)
- **Architecture Recommendation**: "Combined flat fee for improved customer conversion and operational simplicity"

---

## Policy vs Economic Reality

### Confirmed Policy (DEC-OWN-003)
- **One flat delivery fee per parent order**
- **Applies regardless of**: Number of stores, number of shipments, weight, distance
- **Displayed at checkout** (PRD-CHK-004, RULE-AUR-008)

### Documented Cost Model (`SHIPPING_SYSTEM_ARCHITECTURE.md` §5.1)

```
Shipping Cost = Base Fee + Weight Fee + Service Fee

Where:
- Base Fee = Fixed fee per carrier
- Weight Fee = Rate per kg × weight_kg (rounded up)
- Service Fee = Service charge based on destination zone
```

**Critical Issue**: All cost components are **TBD** — no actual rates defined.

---

## Economic Scenario Analysis

### Assumptions (Bangladesh Market)
| Parameter | Value |
|-----------|-------|
| Flat delivery fee (assumed) | 80 BDT |
| Pathao Dhaka metro base | 60 BDT |
| Pathao per kg | 15 BDT/kg |
| Pathao outside Dhaka base | 100 BDT |
| Pathao per kg (outside) | 20 BDT/kg |
| Average order weight | 1.5 kg |
| Dhaka metro order % | 70% |
| Outside Dhaka order % | 30% |

### Scenario Analysis

| Scenario | Fee Collected | Actual Courier Cost | Net Margin |
|----------|---------------|---------------------|------------|
| **Single store, Dhaka, 1kg** | 80 BDT | 60 + 15 = 75 BDT | **+5 BDT** |
| **Single store, Dhaka, 3kg** | 80 BDT | 60 + 45 = 105 BDT | **-25 BDT** |
| **Single store, Outside Dhaka, 1kg** | 80 BDT | 100 + 20 = 120 BDT | **-40 BDT** |
| **Multi-store (2), consolidated, Dhaka** | 80 BDT | 60 + 30 = 90 BDT | **-10 BDT** |
| **Multi-store (2), split shipment** | 80 BDT | 2×(60+15) = 150 BDT | **-70 BDT** |
| **Failed delivery (RTO)** | 80 BDT | 2×forward = 150-240 BDT | **-70 to -160 BDT** |
| **Return shipment** | 80 BDT | Return courier = 75-120 BDT | **0 to -40 BDT** |

### Key Findings

| Finding | Impact |
|---------|--------|
| **Heavy orders lose money** | Orders >2kg in Dhaka, any order outside Dhaka |
| **Multi-store split shipments lose heavily** | 2× courier cost vs 1× fee |
| **RTO is catastrophic** | 2× courier cost, no fee recovery |
| **Returns lose money** | Return shipping not covered by fee |
| **Flat fee only works for light, Dhaka, single-store orders** | ~40% of orders profitable |

---

## Critical Economic Gaps

### 1. No Courier Rate Card Integration

| Missing | Consequence |
|---------|-------------|
| Pathao rate card (base, per-kg, zones) | Cannot calculate actual cost per order |
| Weight/dimension capture at checkout | Cannot compute weight fee |
| Zone detection (Dhaka metro vs outside) | Cannot apply zone surcharge |
| Volume/dimensional weight | Large light items undercharged |

**Current**: All cost components TBD in `SHIPPING_SYSTEM_ARCHITECTURE.md` §5.1

### 2. Multi-Shipment Loss Scenario

**Policy**: "Flat delivery fee per order" (DEC-OWN-003)  
**Reality**: "No partial shipments V1" (Confirmed Business Decision) BUT multi-store orders create multi-shipment

| Order Type | Shipments | Fee Collected | Courier Cost |
|------------|-----------|---------------|--------------|
| Single store | 1 | 1× fee | 1× cost |
| Multi-store (2) | 2 (split) | 1× fee | 2× cost |
| Multi-store (3) | 3 (split) | 1× fee | 3× cost |

**Loss per additional shipment**: Full courier cost with zero additional revenue

### 3. RTO (Return to Origin) Economic Disaster

| Event | Fee Collected | Courier Cost | Net Loss |
|-------|---------------|--------------|----------|
| Customer refuses COD | 1× fee | 2× forward cost | ~1.5-2× fee |
| Address not found | 1× fee | 2× forward cost | ~1.5-2× fee |
| Customer unavailable (3 attempts) | 1× fee | 2× forward cost | ~1.5-2× fee |

**No RTO cost recovery mechanism defined**

### 4. Return Shipping Economics

| Return Type | Fee Collected | Return Courier Cost | Net |
|-------------|---------------|---------------------|-----|
| Customer return (within 7 days) | 0 (already paid) | 1× return cost | -1× cost |
| Exchange | 0 | 2× (return + reship) | -2× cost |
| Defective return | 0 | 1× cost | -1× cost |

**Flat fee collected at checkout doesn't cover return shipping**

---

## Required Financial Policies (Missing)

### 1. Courier Rate Card Integration (Required)

| Data Needed | Source | Use |
|-------------|--------|-----|
| Base fee per courier | Pathao contract | Base cost calc |
| Per-kg rate | Pathao contract | Weight fee calc |
| Zone surcharges | Pathao contract | Zone fee calc |
| Dimensional weight factor | Pathao contract | Volumetric weight |
| COD surcharge | Pathao contract | COD fee inclusion |
| Fuel surcharge | Pathao contract | Dynamic adjustment |

### 2. Fee Adequacy Model (Required)

| Metric | Target | Monitoring |
|--------|--------|------------|
| Average fee / average cost | > 1.15x | Monthly |
| Loss-making order % | < 10% | Weekly |
| RTO cost as % of revenue | < 5% | Monthly |
| Return shipping as % of revenue | < 3% | Monthly |

### 3. RTO Cost Recovery Policy (Owner Decision Required)

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Customer pays** | Charge customer return shipping on refusal | Full recovery | Customer hostility, abandoned carts |
| **Platform absorbs** | Platform pays all RTO costs | Customer experience | Unbounded loss |
| **Hybrid** | First RTO free, subsequent charged | Balanced | Complex |
| **Courier insurance** | Insure against RTO | Predictable cost | Premium cost |

### 4. Return Shipping Policy (Owner Decision Required)

| Option | Description |
|--------|-------------|
| **Free returns** | Platform pays all return shipping |
| **Customer pays** | Customer pays return shipping |
| **Hybrid** | Free for defective, customer pays for change of mind |
| **Capped** | Platform pays up to X BDT per return |

### 4. Multi-Shipment Surcharge (Owner Decision Required)

| Option | Description |
|--------|-------------|
| **No surcharge** | Platform absorbs (current DEC-OWN-003) |
| **Per-additional-shipment fee** | Flat fee per extra shipment |
| **Weight-based surcharge** | Additional fee proportional to weight |
| **Dynamic** | Surcharge = actual additional courier cost |

---

## Fee Adequacy Simulation

### Required Flat Fee Calculation

To break even across all scenarios:

```
Required Fee = Weighted Average Courier Cost + Buffer
             = (0.7 × Dhaka_avg + 0.3 × Outside_avg) × (1 + multi_shipment_factor) + RTO_buffer + Return_buffer
```

**Estimated minimum viable flat fee: 120-150 BDT** (vs assumed 80 BDT)

### Sensitivity Analysis

| Variable | Change | Fee Impact |
|-----------|--------|------------|
| Fuel surcharge +10% | +10% courier cost | +8-12 BDT |
| Outside Dhaka orders +20% | +20% remote orders | +15-20 BDT |
| RTO rate 10% → 20% | Double RTO | +15-25 BDT |
| Return rate 5% → 15% | Triple returns | +10-15 BDT |

---

## Required Owner Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Courier rate card** | Pathao provides / Platform estimates | Obtain from Pathao |
| **Flat fee amount** | 80 / 100 / 120 / 150 BDT | 120 BDT minimum |
| **RTO cost recovery** | Customer / Platform / Hybrid / Insurance | Hybrid (first free) |
| **Return shipping cost** | Free / Customer / Capped / Hybrid | Capped (100 BDT) |
| **Multi-shipment surcharge** | None / Per shipment / Weight-based / Dynamic | Per-shipment (50 BDT) |
| **Weight-based fee tiers** | Flat / Tiered (0-1kg, 1-3kg, 3-5kg, 5kg+) | Tiered |
| **Zone-based pricing** | Flat / Metro vs Remote / Per-district | Metro vs Remote |

---

## Financial Exposure Without Policies

| Risk | Annual Exposure (est. 1000 orders/mo) |
|------|--------------------------------------|
| Heavy order losses | 300 orders × 30 BDT loss = 108,000 BDT/yr |
| Multi-shipment losses | 200 orders × 70 BDT loss = 168,000 BDT/yr |
| RTO losses | 150 RTO × 150 BDT loss = 270,000 BDT/yr |
| Return shipping losses | 300 returns × 80 BDT = 288,000 BDT/yr |
| **Total Annual Exposure** | **~834,000 BDT/year** |

---

## Verdict

**Delivery Fee Economics: PARTIALLY ADDRESSED — MEDIUM-HIGH RISK**

**What's Good**: Policy decided (flat fee), displayed at checkout (RULE-AUR-008), architecture supports cost calculation.

**What's Missing**: 
1. **No courier rate card** → cannot compute actual costs
2. **No fee adequacy model** → flat fee likely too low
3. **No RTO cost policy** → unbounded loss on refused deliveries
4. **No return shipping policy** → platform absorbs all return costs
5. **No multi-shipment surcharge** → split orders lose money

**Blocker for Implementation**: Courier rate card from Pathao required before shipping cost engine can be implemented.

**Required Before Launch**: Owner decisions on 6 financial policies + Pathao rate card integration.

---

**Document ID:** DELIVERY_FEE_ECONOMIC_ANALYSIS  
**Version:** 1.0  
**Status:** FINAL  
**Date:** 2026-11-08