---
id: DOC-AUR-155
title: Aura Bell — Agent Working Rules & Workflow Specification
type: instruction
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001, AB-DM-001
last_updated: 2026-11-04
---

# Aura Bell — Agent Working Rules & Workflow Specification (এইআই এজেন্ট_workflow)

## 1. Agent Governance Hierarchy

### Confirmed Priority Order:
1. **প্রকল্পের মালিকের অনুমোদিত ব্যবসায়িক সিদ্ধান্ত (Owner-Approved Decisions)**
2. `PROJECT_BRAIN.md` (এই নথি)
3. `PROJECT_VISION.md` (DOC-AUR-010)
4. **অনুমোদিত প্রোডাক্ট রিকোয়ারমেন্ট ডকুমেন্টস (Approved PRDs - 03_PRODUCT_REQUIREMENTS/)**
5. **অনুমোদিত সিস্টেম আর্কিটেকচার (Approved Architecture - 04_SYSTEM_ARCHITECTURE/)**
6. **ডাটাবেজ স্কিমা ও টেকনিক্যাল স্পেসিফিকেশন (05_DATABASE/ & 06_API_DOCUMENTATION/)**
7. **কোডিং স্ট্যান্ডার্ড ও ডেভেলপমেন্ট ওয়ার্কফ্লো (09_AI_AGENT_SYSTEM/ & 10_DEVELOPMENT_WORKFLOW/)**

### CRITICAL WARNING:
- ❌ কোনো এআই এজেন্ট নিজ থেকে পূর্ব-অনুমোদিত প্রয়োজনীয়তা বা আর্কিটেকচার পরিবর্তন করতে পারবে না
- ❌ কোনো বৈপরীত্য দেখা দিলে অবিলম্বে কাজ স্থগিত করে রিপোর্ট করতে হবে
- ❌ অনুমোদিত সিদ্ধান্ত ছাড়া কোনো নতুন কোড লিখা যাবে না

---

## 2. Agent Working Rules

### 2.1 Code Generation Rules
- **Rule-AWR-001**: সব কোড তৈরি করার আগে `PROJECT_BRAIN.md`-এ বর্ণিত স confirmed_owner_decision-গুলো পূরণ করulsion
- **Rule-AWR-002**: কোনো নতুন ডাটাবেস টেবিল বা কলাম তৈরি করার আগে `05_DATABASE/DATABASE_SCHEMA.md`-এ টেবিল আইডি যোগ করulsion
- **Rule-AWR-003**: যেকোনো API এন্ডপয়েন্ট তৈরি করার আগে `06_API_DOCUMENTATION/API_ENDPOINTS.md`-এ স_PATH_METHOD- যোগ করulsion
- **Rule-AWR-004**: পেমেন্ট-সম্পর্কিত কোড তৈরি করার আগে `08_PAYMENT/`-এ চেক করulsion
- **Rule-AWR-005**: ইনভেন্টরি-সম্পর্কিত কোড তৈরি করার আগে `05_DATABASE/` এবং `03_PRODUCT_REQUIREMENTS/INVENTORY_PRD.md`-এ চেক করulsion

### 2.2 Documentation Rules
- **Rule-AWR-006**: সব ফাইলতে ইউনিক আইডি (`DOC-AUR-xxx`) ব্যবহার করulsion
- **Rule-AWR-007**: প্রতিটি ফাইলের শেষে `---` (triple dash) লিখা আবশ্যক
- **Rule-AWR-008**: `@last_updated` স	subset **সম্পূর্ণ** হতে হবে
- **Rule-AWR-009**: ডকুমেন্ট আইডি دوب্লিকেট করলেও `DOCUMENT_INDEX.md`-এ র입olarization করulsion
- **Rule-AWR-010**: `OPEN_OWNER_DECISIONS.md`-তে যে সিদ্ধান্ত **Pending Owner Review** সিন্ধিত আছে, সেগুলো কোনো ভাইজিনাল]\]tion ছাড়াই ওracle করulsion

### 2.3 Decision Rules
- **Rule-AWR-011**: `DEC-OWN-001` (Payment Gateway) decided না হল 때까지 অনলাইন পেমেন্ট কোড লিখা যাবে না
- **Rule-AWR-012**: `DEC-OWN-002` (Stock Reservation TTL) decided না হল 때까지_stock_reservation_timeout_ kode নহে_
- **Rule-AWR-013**: `DEC-OWN-003` (Delivery Fee Policy) decided না হল transport_fare_code লিখা যাবে না
- **Rule-AWR-014**: `DEC-OWN-004` (Courier Partner) decided না হল CourierIntegration code লিখা যাবে না

---

## 3. Agent Workflow Phases

### Phase 1: Initialization
1. `PROJECT_BRAIN.md` পূরণ করে মূলাভাবিক পরিচয় নেল
2. `OPEN_OWNER_DECISIONS.md`-এ চেক করে পanding সিদ্ধান্তগুলো নোট করelson
3. `DOCUMENT_INDEX.md`-ে所有目标) files খুঁজে বের করelson
4. `REQUIREMENT_TRACEABILITY_MATRIX.md`-এ উৎয়োজনীয় রিকোয়ারমেন্ট ID খুঁজে বের করelson

### Phase 2: Requirement Analysis
1. PRDs (`03_PRODUCT_REQUIREMENTS/`) পূরণ করে ফাংশনাল স্পেসিফিকেশন বিশ্লেষণ করelson
2. Business Rules (`02_BUSINESS_REQUIREMENTS/BUSINESS_RULES.md`) পর্যালোচনা করelson
3. ADRs (`04_SYSTEM_ARCHITECTURE/ARCHITECTURE_DECISION_RECORDS.md`) চেক করelson
4. Confirmed vs Pending vs Specified vs Not Implemented categorize করelson

### Phase 3: Implementation Planning
1. Owner-approved decisions boundaries বোঝায়
2. Specified requirements understanding
3. Not yet implemented requirements চিহ্নিত করelson
4. Integration points mapped

### Phase 4: Code Generation
1. Owner-approved features only code generation
2. Specified features documentation-only mode
3. Pending features marked "awaiting owner decision"
4. Not implemented features marked "pending implementation"

### Phase 5: Validation
1. Cross-document consistency check
2. No contradictory business rules verification
3. No duplicate requirement IDs detection
4. All internal links working validation

---

## 4. Critical Guardrails

### ⚠️ MANDATORY CHECKS BEFORE ANY CODE GENERATION:

| Check | File | Status Required |
|-------|------|-----------------|
| Owner Decisions | `OPEN_OWNER_DECISIONS.md` | All DEC-OWN-xxx must show "Pending Owner Review" or "Approved" |
| Document Count | `DOCUMENT_INDEX.md` | Must match actual file count in project directory |
| Requirement IDs | `REQUIREMENT_TRACEABILITY_MATRIX.md` | No duplicates, all IDs unique |
| Business Rules | `BUSINESS_RULES.md` | No contradictory rules |
| API Definitions | `API_ENDPOINTS.md` | No unimplemented endpoints described as implemented |
| Database Schema | `DATABASE_SCHEMA.md` | Table count must be consistent |

### 🛑 HARD BLOCKERS (Code Generation Will Be STOPPED If):

1. ✅ **Owner decision pending** but code for that feature requested
2. ✅ **Document count mismatch** in DOCUMENT_INDEX.md
3. ✅ **Duplicate requirement IDs** found
4. ✅ **Conflicting business rules** detected
5. ✅ **Unimplemented endpoint** described as "implemented"
6. ✅ **Missing table** in DATABASE_SCHEMA.md but code references it

---

## 5. Agent Communication Protocol

### 5.1 Status Reporting
Every agent session must report:
- ✅ `session_status`: "idle", "busy", "waiting", "error"
- ✅ `progress_percentage`: 0-100
- ✅ `blocking_issues`: Array of blocking issues
- ✅ `next_action`: Clear description of next step

### 5.2 Decision Escalation
If any ambiguity found:
1. Stop current task
2. Report to `OPEN_OWNER_DECISIONS.md` pending decisions
3. Wait for owner clarification
4. Document the uncertainty in session notes
5. Resume only after clarification

### 5.3 File Modification Rules
- Never modify `PROJECT_BRAIN.md` without owner approval
- Never modify `OPEN_OWNER_DECISIONS.md` pending decisions
- Always update `DOCUMENT_INDEX.md` when adding new files
- Update `CHANGELOG.md` for all significant changes
- Preserve Bangla with English technical terms convention

---

## 6. Termination Conditions

Agent session should terminate if:
1. ✅ All owner decisions approved and documented
2. ✅ All required documentation created
3. ✅ Cross-document consistency validated
4. ❌ Unresolvable conflicts detected
5. ❌ Owner unavailable for critical decisions
6. ❌ Required documentation evidence missing

---

## 7. Working Directory Structure

### Recommended Project Structure for Agents:
```
AURA_BELL_PROJECT_BLUEPRINT/
├── 00_FOUNDATION/          # Vision, scope, principles
├── 01_SOURCE_DOCUMENTS/    # Source analysis
├── 02_BUSINESS_REQUIREMENTS/  # Business rules, requirements
├── 03_PRODUCT_REQUIREMENTS/  # PRDs
├── 04_SYSTEM_ARCHITECTURE/    # Architecture docs
├── 05_DATABASE/              # Database schema, migrations
├── 06_API_DOCUMENTATION/     # API specs
├── 07_UI_UX_DESIGN/          # Design guidelines
├── 08_PAYMENT/               # Payment system docs *(NEW)*
├── 08_SECURITY_AND_PRIVACY/  # Security docs
├── 09_INVENTORY/               # Inventory docs *(NEW)*
├── 10_DEVELOPMENT_WORKFLOW/  # Workflow docs
├── 11_QUALITY_ASSURANCE/       # Testing docs
├── 12_PROJECT_GOVERNANCE/      # Governance docs
├── 13_REFERENCE/               # Reference docs
└── ROOT/                          # Root level docs
```

---

## 8. Final Agent Directive

> **⚠️ SATARK BARATRA**: Code generation without owner approval for pending decisions constitutes governance violation. Always verify:
> 1. `OPEN_OWNER_DECISIONS.md` status
> 2. `DOCUMENT_INDEX.md` count
> 3. `REQUIREMENT_TRACEABILITY_MATRIX.md` ID uniqueness
> 4. `BUSINESS_RULES.md` consistency
> 
> When in doubt: **STOP and report**.

---

**Document ID**: DOC-AUR-155  
**Version**: 1.0  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Documentation Preparation