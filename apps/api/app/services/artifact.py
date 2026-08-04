from __future__ import annotations

import csv
import html
import io
import json

from app.services.comparability import comparison_matrix
from app.services.repository import repo

DISCLAIMER = (
    "Findings are limited to the analyzed sample. Absences read as "
    "'not found within the analyzed sample'; nothing is confirmed without a recorded review."
)

CSV_DATASETS = ("sales_elements", "gaps", "evidence")


def artifact_payload(project_id: str) -> dict:
    """Canonical export bundle shared by JSON export, CSV export, and the HTML artifact."""
    project = repo.projects.get(project_id)
    if project is None:
        raise KeyError(project_id)

    entities = repo.by_project(repo.entities, project_id)
    sources = repo.by_project(repo.sources, project_id)
    content_items = repo.by_project(repo.content_items, project_id)
    evidence = repo.by_project(repo.evidence, project_id)
    assessments = repo.by_project(repo.assessments, project_id)
    gaps = repo.by_project(repo.gaps, project_id)

    url_by_content = {c.id: c.url for c in content_items}

    evidence_rows = []
    for e in evidence:
        row = e.model_dump(mode="json")
        # Direct link back to the exact page the quote came from.
        row["source_url"] = url_by_content.get(e.content_item_id)
        evidence_rows.append(row)

    return {
        "project": project.model_dump(mode="json"),
        "disclaimer": DISCLAIMER,
        "counts": {
            "entities": len(entities),
            "sources": len(sources),
            "content_items": len(content_items),
            "evidence": len(evidence),
            "sales_elements": len(assessments),
            "gaps": len(gaps),
        },
        "entities": [e.model_dump(mode="json") for e in entities],
        "sources": [s.model_dump(mode="json") for s in sources],
        "sales_elements": [a.model_dump(mode="json") for a in assessments],
        "gaps": [g.model_dump(mode="json") for g in gaps],
        "evidence": evidence_rows,
        "comparison": comparison_matrix(project_id),
    }


def csv_for(payload: dict, dataset: str) -> str:
    if dataset not in CSV_DATASETS:
        raise KeyError(dataset)
    buffer = io.StringIO()

    if dataset == "sales_elements":
        fields = [
            "entity_id",
            "canonical_element_id",
            "canonical_key",
            "presence_status",
            "computed_score",
            "confidence",
            "review_status",
            "evidence_ids",
        ]
    elif dataset == "gaps":
        fields = [
            "id",
            "gap_type",
            "status",
            "severity",
            "confidence",
            "root_cause",
            "review_status",
            "title",
            "evidence_ids",
        ]
    else:  # evidence
        fields = [
            "id",
            "entity_id",
            "category",
            "finding_status",
            "review_status",
            "source_url",
            "verbatim_text",
            "normalized_summary",
        ]

    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in payload[dataset]:
        record = dict(row)
        if isinstance(record.get("evidence_ids"), list):
            record["evidence_ids"] = " ".join(record["evidence_ids"])
        writer.writerow(record)
    return buffer.getvalue()


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def render_artifact_html(payload: dict) -> str:
    project = payload["project"]
    counts = payload["counts"]

    def count_tile(key: str, label: str) -> str:
        return (
            f'<article class="tile"><strong data-count="{key}">{counts[key]}</strong>'
            f"<span>{_esc(label)}</span></article>"
        )

    tiles = "".join(
        count_tile(k, k.replace("_", " ").title())
        for k in ("entities", "sources", "content_items", "evidence", "sales_elements", "gaps")
    )

    element_rows = "".join(
        "<tr>"
        f"<td>{_esc(a['canonical_element_id'])}</td>"
        f'<td dir="auto">{_esc(a["canonical_key"])}</td>'
        f"<td>{_esc(a['presence_status'])}</td>"
        f"<td>{_esc('—' if a['computed_score'] is None else a['computed_score'])}</td>"
        f"<td>{_esc(a['confidence'])}</td>"
        f"<td>{_esc(a['review_status'])}</td>"
        "</tr>"
        for a in payload["sales_elements"]
    )

    gap_items = "".join(
        "<li>"
        f'<strong dir="auto">{_esc(g["title"])}</strong>'
        f"<div class=\"tags\"><span>{_esc(g['gap_type'])}</span><span>{_esc(g['status'])}</span>"
        f"<span>severity: {_esc(g['severity'])}</span><span>confidence: {_esc(g['confidence'])}</span>"
        f"<span>{_esc(g['root_cause'])}</span></div>"
        + (
            "<ul>"
            + "".join(f'<li dir="auto">{_esc(alt)}</li>' for alt in g.get("alternative_explanations", []))
            + "</ul>"
            if g.get("alternative_explanations")
            else ""
        )
        + "</li>"
        for g in payload["gaps"]
    )

    evidence_cards = "".join(
        '<article class="evidence" data-evidence-id="{eid}">'
        '<div class="tags"><span>{cat}</span><span>{finding}</span><span>{review}</span></div>'
        '<blockquote dir="auto">{verbatim}</blockquote>'
        '<p dir="auto">{summary}</p>{link}'
        "</article>".format(
            eid=_esc(e["id"]),
            cat=_esc(e["category"]),
            finding=_esc(e["finding_status"]),
            review=_esc(e["review_status"]),
            verbatim=_esc(e["verbatim_text"]),
            summary=_esc(e["normalized_summary"]),
            link=(
                f'<a class="source-link" href="{_esc(e["source_url"])}" '
                f'target="_blank" rel="noreferrer">source</a>'
                if e.get("source_url")
                else ""
            ),
        )
        for e in payload["evidence"]
    )

    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diagnosis artifact — {_esc(project['brand_name'])}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; color: #172033; background: #f5f7fb; }}
  main {{ max-width: 1100px; margin: auto; padding: 2rem; }}
  .tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin: 1rem 0; }}
  .tile {{ background: white; border: 1px solid #e4e7ec; border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; }}
  .tile strong {{ font-size: 1.8rem; }}
  section {{ background: white; border: 1px solid #e4e7ec; border-radius: 12px; padding: 1.2rem; margin: 1rem 0; }}
  table {{ border-collapse: collapse; width: 100%; font-size: .85rem; }}
  th, td {{ border: 1px solid #eaecf0; padding: .35rem .5rem; text-align: start; }}
  .tags {{ display: flex; flex-wrap: wrap; gap: .4rem; margin: .3rem 0; }}
  .tags span {{ background: #e8edf6; border-radius: 999px; padding: .1rem .55rem; font-size: .75rem; }}
  blockquote {{ margin-inline: 0; padding-inline-start: 1rem; border-inline-start: 3px solid #2758c7; }}
  .evidence {{ border: 1px solid #eaecf0; border-radius: 10px; padding: .8rem; margin: .6rem 0; }}
  .source-link {{ color: #2758c7; }}
  .notice {{ background: #fff8e6; border: 1px solid #f5d98a; border-radius: 8px; padding: .6rem .8rem; }}
</style>
</head>
<body>
<main>
  <h1 dir="auto">{_esc(project['brand_name'])}</h1>
  <p dir="auto">{_esc(project['target_buying_decision'])}</p>
  <p class="notice" dir="auto">{_esc(payload['disclaimer'])}</p>

  <div class="tiles">{tiles}</div>

  <details open><summary>Sales Elements</summary>
    <section>
      <table><thead><tr><th>ID</th><th>Element</th><th>Presence</th><th>Score</th><th>Confidence</th><th>Review</th></tr></thead>
      <tbody>{element_rows}</tbody></table>
    </section>
  </details>

  <details open><summary>Gaps</summary>
    <section><ul class="gaps">{gap_items}</ul></section>
  </details>

  <details><summary>Evidence drawer</summary>
    <section>{evidence_cards}</section>
  </details>

  <script type="application/json" id="artifact-data">{data_json}</script>
</main>
</body>
</html>"""
