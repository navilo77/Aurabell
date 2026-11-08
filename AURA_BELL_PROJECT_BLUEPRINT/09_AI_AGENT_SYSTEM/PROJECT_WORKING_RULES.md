---
id: DOC-AUR-156
title: Aura Bell — Agent Project Working Rules Specification
type: instruction
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001, AB-DM-001
last_updated: 2026-11-04
---

# Aura Bell — Agent Project Working Rules (এইআই এজেন্ট প্রোekt_WORKING_RULES)

## 1. Requirement Traceability

### 1.1 Unique Requirement IDs
Every requirement must have a unique ID following the format:
- **BR-AUR-xxx**: Business Requirements (`02_BUSINESS_REQUIREMENTS/`)
- **PRD-CUST-xxx**: Customer PRD (`03_PRODUCT_REQUIREMENTS/CUSTOMER_PRD.md`)
- **PRD-CHK-xxx**: Cart & Checkout PRD (`03_PRODUCT_REQUIREMENTS/CART_CHECKOUT_PRD.md`)
- **PRD-ORD-xxx**: Order Management PRD (`03_PRODUCT_REQUIREMENTS/ORDER_MANAGEMENT_PRD.md`)
- **PRD-PAY-xxx**: Payment PRD (`03_PRODUCT_REQUIREMENTS/PAYMENT_PRD.md`)
- **PRD-SHP-xxx**: Shipping PRD (`03_PRODUCT_REQUIREMENTS/SHIPPING_DELIVERY_PRD.md`)
- **PRD-INV-xxx**: Inventory PRD (`03_PRODUCT_REQUIREMENTS/INVENTORY_PRD.md`)
- **RULE-AUR-xxx**: Business Rules (`02_BUSINESS_REQUIREMENTS/BUSINESS_RULES.md`)
- **ADR-xxx**: Architectural Decision Records (`04_SYSTEM_ARCHITECTURE/ARCHITECTURE_DECISION_RECORDS.md`)
- **TC-AUR-xxx**: Test Cases (`11_QUALITY_ASSURANCE/TEST_CASES.md`)

### 1.2 Traceability Matrix
Requirement → Owner Decision → Architecture → Database → API → Module → Test

Example Traceability Path:
```
BR-AUR-002 (Unified Customer Account)
→ DEC-OWN-001 (Online Payment Gateway - pending)
→ API Endpoint: /api/v1/auth/login
→ Database: profiles, authentication tables
→ Module: Identity Module (app.modules.identity)
→ Test: TC-AUR-001 (Customer login test)
```

### 1.3 ID Uniqueness Verification
- Search existing IDs before creating new ones
- Never reuse existing IDs
- Update `REQUIREMENT_TRACEABILITY_MATRIX.md` after adding new requirements
- Document ID conflicts in session notes and halt work

---

## 2. Documentation Governance

### 2.1 File Status Categories
Every documentation file must have one of these statuses:
- **CONFIRMED**: Owner-approved, implementation-ready specification
- **PENDING OWNER REVIEW**: Awaiting owner decision (listed in `OPEN_OWNER_DECISIONS.md`)
- **SPECIFIED**: Documented but pending owner approval for implementation
- **NOT IMPLEMENTED**: Documented but no code exists
- **DEPRECATED**: No longer applicable or replaced
- **ARCHIVED**: Removed from active development

### 2.2 Status Transition Rules
```
CONFIRMED → PENDING OWNER REVIEW → SPECIFIED → NOT IMPLEMENTED → IMPLEMENTED → VERIFIED
```

### 2.3 Modification Rules
- Never change status from PENDING to CONFIRMED without explicit owner approval
- Never change status from CONFIRMED to PENDING without recording the reason
- Always update `DOCUMENT_APPROVAL_STATUS.md` when status changes
- Record all status changes in `CHANGELOG.md`

### 2.3 Required Fields in All Documents
Every documentation file must include:
- `id: DOC-AUR-xxx` (unique document ID)
- `status: confirmed/pending owner review/specified/not implemented`
- `version: 1.0` (or appropriate version)
- `language: Bangla with English technical terms`
- `source: AB-PV-001, AB-SA-001, AB-DS-001, AB-DM-001` (or appropriate sources)
- `last_updated: YYYY-MM-DD`

---

## 3. Pending Decision Workflow

### 3.1 DEC-OWN-001: Payment Gateway Selection
**Background**: Online payment gateway must be selected before any payment integration can proceed.

**Available Options**:
- **Option A**: bKash PGW (Direct) - supports bKash direct integration
- **Option B**: SSLCommerz - supports all card types and mobile financial services
- **Option C**: Shurjopay - supports Bangladeshi payment ecosystem

**Architectural Implications**:
- Provider Interface must be implemented before payment module development
- Provider Adapter Pattern must be created (provider-independent)
- Webhook endpoints must be configured for selected gateway
- Idempotency keys must match gateway specifications

**Financial Implications**:
- SSLCommerz: Standard transaction fees apply
- bKash Direct: Lower fees but limited feature set
- Shurjopay: Moderate fees, good coverage

**Questions Requiring Owner Approval**:
1. Which payment gateway should be selected for V1 launch?
2. What are the exact transaction fee structures for each option?
3. Are there any regulatory requirements for specific gateways?

**Current Status**: Pending Owner Review (DEC-OWN-001)

### 3.2 DEC-OWN-002: Stock Reservation TTL (Time To Live)
**Background**: Stock reservation timeout period before automatic release if payment not completed.

**Available Options**:
- **Option A**: 10 minutes - shorter wait time for customers
- **Option B**: 15 minutes - balanced time (RECOMMENDED in architecture)
- **Option C**: 30 minutes - longer wait time, potentially cart abandonment

**Technical Implications**:
- `inventory_reservations` table TTL field
- Background job to release expired reservations
- Stock availability logic integration
- COD confirmation workflow integration

**Current Status**: Pending Owner Review (DEC-OWN-002)

### 3.3 DEC-OWN-003: Delivery Fee Policy
**Background**: Multi-store delivery fee calculation policy.

**Available Options**:
- **Option A**: Store-per-store delivery fee - each store sets own fee
- **Option B**: Combined flat fee - single delivery fee for entire order

**Architectural Implications**:
- `orders` table delivery_fee calculation logic
- `store_orders` table store-specific fee application
- Admin panel configuration for fee settings
- Checkout price recalculation integration

**Current Status**: Pending Owner Review (DEC-OWN-003)

### 3.4 DEC-OWN-004: Courier Partner Selection
**Background**: Courier service provider for V1 manual dispatch.

**Available Options**:
- **Option A**: Steadfast Courier - good COD rates, reliable coverage
- **Option B**: Pathao Courier - excellent COD rates, good coverage
- **Option C**: RedX - moderate rates, limited coverage

**Architectural Implications**:
- `couriers` table provider selection and configuration
- `shipments` table courier-specific tracking
- Manual dispatch workflow in admin panel
- Tracking events integration

**Current Status**: Pending Owner Review (DEC-OWN-004)

### 3.4 Decision Workflow Process
1. Owner reviews pending decisions in `OPEN_OWNER_DECISIONS.md`
2. Owner provides explicit approval or modification
3. Approved decisions recorded in `OWNER_DECISIONS_REQUIRED.md`
4. Implementation proceeds based on owner-approved decisions
5. All documentation updated to reflect owner decisions
6. `CHANGELOG.md` updated with decision changes

---

## 4. Code Generation Constraints

### 4.1 Mandatory Pre-Checks Before Any Code Generation:
- [ ] `OPEN_OWNER_DECISIONS.md` - All pending decisions reviewed
- [ ] `DOCUMENT_INDEX.md` - Document count verified
- [ ] `REQUIREMENT_TRACEABILITY_MATRIX.md` - No duplicate IDs
- [ ] `BUSINESS_RULES.md` - No contradictory rules
- [ ] `API_ENDPOINTS.md` - No unimplemented endpoints marked implemented
- [ ] `DATABASE_SCHEMA.md` - Table count consistent

### 4.2 Hard Blockers (Will Stop Code Generation):
1. Owner decision pending but code for that feature requested
2. Document count mismatch in DOCUMENT_INDEX.md
3. Duplicate requirement IDs found
4. Conflicting business rules detected
5. Unimplemented endpoint described as "implemented"
6. Missing table in DATABASE_SCHEMA.md but code references it

### 4.3 Agent Session Termination Conditions:
1. All owner decisions approved and documented ✅
2. All required documentation created ✅
3. Cross-document consistency validated ✅
4. Unresolvable conflicts detected ❌
5. Owner unavailable for critical decisions ❌
6. Required documentation evidence missing ❌

---

## 5. Working Directory Reference

### 5.1 Key Files for Agent Reference:
```
AURA_BELL_PROJECT_BLUEPRINT/
├── 09_AI_AGENT_SYSTEM/
│   ├── AGENTS.md                    # Agent overview
│   ├── AGENT_ROLES.md               # Agent roles
│   ├── AGENT_WORKFLOW.md            # This file - workflow rules
│   ├── PROJECT_WORKING_RULES.md     # This file - working rules
│   ├── KILO_CODE_INSTRUCTIONS.md   # Kilo Code instructions
│   ├── PROJECT_CONTEXT_RULES.md    # Context preservation
│   ├── CODING_STANDARDS.md         # Coding standards
│   ├── CODE_REVIEW_RULES.md       # Code review rules
│   └── DOCUMENTATION_UPDATE_RULES.md # Documentation update rules
├── 12_PROJECT_GOVERNANCE/
│   ├── OWNER_DECISIONS_REQUIRED.md  # Owner decisions
│   ├── OPEN_OWNER_DECISIONS.md     # Pending decisions (created)
│   ├── REQUIREMENT_TRACEABILITY_MATRIX.md  # RTM
│   ├── RISK_REGISTER.md             # Risk register
│   ├── DOCUMENT_APPROVAL_STATUS.md # Document approval tracker
│   └── CHANGELOG.md                # Change log
└── ROOT/
    ├── PROJECT_BRAIN.md              # Single source of truth
    ├── PROJECT_STATUS.md             # Project status
    ├── DOCUMENT_INDEX.md             # Document master index
    ├── CHANGELOG.md                  # Project changelog
    └── AURA_BELL_FINAL_DOCUMENTATION_READINESS_REPORT.md  # Final report (to create)
```

---

## 6. Final Agent Directive

> **⚠️ SATARK BARATRA**: Code generation without owner approval for pending decisions constitutes governance violation. Always verify:
> 1. `OPEN_OWNER_DECISIONS.md` - All pending decisions status
> 2. `DOCUMENT_INDEX.md` - Document count matches
> 3. `REQUIREMENT_TRACEABILITY_MATRIX.md` - ID uniqueness
> 4. `BUSINESS_RULES.md` - Business rule consistency
> 
> **When in doubt: STOP and report to owner for clarification.**

---

**Document ID**: DOC-AUR-156  
**Version**: 1.0  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Agent Working Rules Preparation