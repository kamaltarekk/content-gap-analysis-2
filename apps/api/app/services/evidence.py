from __future__ import annotations

from app.models.domain import ContentItem, EvidenceCategory, Evidence, FindingStatus
from app.services.repository import repo
from app.services.sales_elements import KEYWORDS

# Candidate evidence is extracted deterministically from collected content and always
# starts pending_review (domain rule 4 — nothing is auto-approved). Each candidate is
# classified into one of the persuasion families the product must distinguish
# (domain rule 8: Claims, Social Proof, Claim Proof). Verbatim text is preserved
# exactly, Arabic or English, so provenance survives.

WINDOW = 60
MAX_CANDIDATES_PER_ITEM = 12

# Highest-signal families are checked first so a certificate reads as claim_proof,
# not a generic claim.
CATEGORY_SIGNALS: list[tuple[EvidenceCategory, list[str], FindingStatus]] = [
    (EvidenceCategory.CLAIM_PROOF, KEYWORDS["claim_proof"], FindingStatus.OBSERVED_FACT),
    (EvidenceCategory.SOCIAL_PROOF, KEYWORDS["social_proof"], FindingStatus.OBSERVED_FACT),
    (EvidenceCategory.CLAIM, KEYWORDS["claim"], FindingStatus.BRAND_CLAIM),
]


def _snippet(text: str, index: int, length: int) -> str:
    start = max(0, index - WINDOW)
    end = min(len(text), index + length + WINDOW)
    return text[start:end].strip()


def extract_from_content_item(item: ContentItem) -> list[Evidence]:
    text = item.text or ""
    lowered = text.lower()
    seen: set[str] = set()
    candidates: list[Evidence] = []

    for category, keywords, finding_status in CATEGORY_SIGNALS:
        for keyword in keywords:
            index = lowered.find(keyword.lower())
            if index == -1:
                continue
            verbatim = _snippet(text, index, len(keyword))
            if not verbatim or verbatim in seen:
                continue
            seen.add(verbatim)
            candidates.append(
                Evidence(
                    project_id=item.project_id,
                    entity_id=item.entity_id,
                    source_id=item.source_id,
                    content_item_id=item.id,
                    verbatim_text=verbatim,
                    normalized_summary=f"{category.value} signal detected near '{keyword}'.",
                    finding_status=finding_status,
                    confidence="low",
                    category=category,
                )
            )
            if len(candidates) >= MAX_CANDIDATES_PER_ITEM:
                return candidates
    return candidates


def extract_candidate_evidence(project_id: str) -> list[Evidence]:
    """Extract and persist candidate evidence for a project's collected content.

    Idempotent per content item: items that already have extracted evidence are skipped
    so re-running does not duplicate candidates.
    """
    existing = repo.by_project(repo.evidence, project_id)
    covered = {e.content_item_id for e in existing}

    created: list[Evidence] = []
    for item in repo.by_project(repo.content_items, project_id):
        if item.id in covered:
            continue
        for evidence in extract_from_content_item(item):
            repo.add(repo.evidence, evidence)
            created.append(evidence)
    return created
