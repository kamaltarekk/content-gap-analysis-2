# Product Specification

## Product

Evidence-Based Brand & Competitor Content Diagnosis Tool.

## Primary user

Marketing strategist, marketing manager, creative strategist, or commercial advisor.

## Job to be done

Given one brand, one buying decision, one primary segment, approved competitors, exact source URLs, uploaded files, and a bounded sample, collect evidence and diagnose:

- content coverage,
- buying-journey coverage,
- customer-language coverage,
- Sales Elements coverage,
- claims and proof,
- competitive deficits and whitespace,
- root causes,
- research needs,
- readiness to move into strategy.

## Product boundary

Included:

- guided setup,
- exact-URL source registration,
- browser collection,
- uploaded-file ingestion,
- content inventory,
- evidence ledger,
- AI-assisted classification,
- human review,
- 17 Sales Elements,
- brand/competitor comparison,
- gap register,
- dashboard and exports.

Excluded from MVP:

- final content calendar,
- scripts and captions,
- autonomous publishing,
- ad buying,
- unsupported private competitor performance,
- bypassing platform access controls.

## Core state flow

```text
DRAFT → READY_FOR_COLLECTION → COLLECTING → COLLECTED → READY_FOR_REVIEW
→ APPROVED_FOR_ANALYSIS → ANALYZED → READY_FOR_FINAL_REVIEW → APPROVED
```

A state cannot be skipped.

## Canonical Sales Elements

| ID | Family | Key |
|---|---|---|
| SE01 | core | trigger_pain |
| SE02 | core | claim |
| SE03 | core | gain |
| SE04 | core | logistics |
| SE05 | intellect | calculation |
| SE06 | intellect | objection_handler |
| SE07 | intellect | reason |
| SE08 | intellect | comparison |
| SE09 | trust | social_proof |
| SE10 | trust | identity_proof |
| SE11 | trust | authority_proof |
| SE12 | trust | fear_free_promise |
| SE13 | trust | claim_proof |
| SE14 | instinct | urgency |
| SE15 | instinct | scarcity |
| SE16 | instinct | reciprocity |
| SE17 | instinct | offer |

## Required user inputs

- Project name
- Brand name
- Product/service
- Country/market
- Target buying decision
- Purchase type
- Primary segment
- Bottleneck or `unknown`
- Exact website/social/ad/review URLs
- Competitors
- Date range
- Collection caps
- Score configuration

## Main screens

1. Projects
2. Guided Setup
3. Sources
4. Collection Jobs
5. Content Inventory
6. Review Queue
7. Sales Elements
8. Competitor Comparison
9. Gap Explorer
10. Evidence Library
11. Method & Limitations

## Acceptance principles

- Every finding links to evidence.
- Every AI proposal is reviewable.
- Blocked sources are not treated as absence.
- One-page competitor samples do not receive full scores.
- Unknown values are visible.
- The app runs in mock mode without paid APIs.
