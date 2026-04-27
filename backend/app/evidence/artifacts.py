from __future__ import annotations

import csv
import html
import io
import json
from typing import Any


def build_artifacts(pack: dict[str, Any]) -> dict[str, str]:
    return {
        "evidence_pack.json": json.dumps(pack, indent=2, ensure_ascii=False),
        "run.json": json.dumps(pack["run"], indent=2, ensure_ascii=False),
        "source_summary.json": json.dumps(pack["source_summary"], indent=2, ensure_ascii=False),
        "demo_scenario.json": json.dumps(_demo_scenario(pack), indent=2, ensure_ascii=False),
        "records.geojson": json.dumps(pack["records_geojson"], indent=2, ensure_ascii=False),
        "quality_metrics.csv": _quality_csv(pack["quality_metrics"]),
        "gap_priorities.csv": _gap_priorities_csv(pack),
        "readiness_scorecard.csv": _readiness_scorecard_csv(pack),
        "dataset_contributions.csv": _dataset_csv(pack["dataset_contributions"]),
        "publisher_feedback.csv": _publisher_feedback_csv(pack["publisher_feedback"]),
        "derived_dataset_recipe.json": json.dumps(pack["citation_autopilot"]["derived_dataset_recipe"], indent=2, ensure_ascii=False),
        "provenance.json": json.dumps(_provenance(pack), indent=2, ensure_ascii=False),
        "citations.md": _citations_md(pack),
        "claim_guardrails.md": _claim_guardrails_md(pack),
        "methods_text.md": _methods_text_md(pack),
        "publisher_feedback.md": _publisher_feedback_md(pack),
        "passport.md": _passport_md(pack),
        "passport.html": _passport_html(pack),
    }


def _demo_scenario(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": pack["passport"]["title"],
        "taxon": pack["passport"]["taxon"],
        "region_name": pack["passport"]["region_name"],
        "purpose": pack["evidence_readiness"]["purpose"],
        "request": pack["run"]["request"],
        "source_summary": pack["source_summary"],
    }


def _quality_csv(metrics: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["metric", "value"])
    for key, value in metrics.items():
        writer.writerow([key, value])
    return output.getvalue()


def _gap_priorities_csv(pack: dict[str, Any]) -> str:
    output = io.StringIO()
    fields = [
        "cell_id",
        "occurrence_count",
        "dataset_count",
        "gap_priority_score",
        "gap_priority_label",
        "no_evidence",
        "neighbor_evidence",
        "recency_deficit",
        "uncertainty_burden",
        "source_diversity_gap",
        "reasons",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for feature in pack["grid_metrics"]["features"]:
        props = feature["properties"]
        components = props.get("gap_priority_components") or {}
        writer.writerow(
            {
                "cell_id": props.get("cell_id"),
                "occurrence_count": props.get("occurrence_count"),
                "dataset_count": props.get("dataset_count"),
                "gap_priority_score": props.get("gap_priority_score"),
                "gap_priority_label": props.get("gap_priority_label"),
                "no_evidence": components.get("no_evidence"),
                "neighbor_evidence": components.get("neighbor_evidence"),
                "recency_deficit": components.get("recency_deficit"),
                "uncertainty_burden": components.get("uncertainty_burden"),
                "source_diversity_gap": components.get("source_diversity_gap"),
                "reasons": "; ".join(props.get("gap_priority_reasons") or []),
            }
        )
    return output.getvalue()


def _dataset_csv(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fields = ["datasetKey", "datasetTitle", "publisher", "license", "record_count", "main_issues"]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field) for field in fields})
    return output.getvalue()


def _publisher_feedback_csv(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fields = ["datasetKey", "records_affected", "main_issue", "suggested_fix"]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field) for field in fields})
    return output.getvalue()


def _provenance(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool": "EcoGenesis Evidence Passport",
        "run": pack["run"],
        "source_summary": pack["source_summary"],
        "passport": pack["passport"],
        "evidence_readiness": pack["evidence_readiness"],
        "purpose_score_matrix": pack["purpose_score_matrix"],
        "citation_status": pack["citation_autopilot"]["citation_status"],
        "dataset_contributions": pack["dataset_contributions"],
        "known_limitations": [
            "GBIF-mediated occurrence records are heterogeneous and reflect variable sampling effort.",
            "No-evidence grid cells are not absence observations.",
            "Occurrence counts alone do not establish abundance or population trends.",
            "Fixture and fallback runs are reproducible demo artifacts, not publication citation bases.",
        ],
    }


def _readiness_scorecard_csv(pack: dict[str, Any]) -> str:
    output = io.StringIO()
    fields = [
        "purpose",
        "purpose_label",
        "score",
        "spatial_accuracy",
        "temporal_recency",
        "taxonomic_confidence",
        "sampling_coverage",
        "citation_provenance",
        "issue_explainability",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for purpose, row in pack["purpose_score_matrix"].items():
        writer.writerow(
            {
                "purpose": purpose,
                "purpose_label": row["purpose_label"],
                "score": row["score"],
                **row["components"],
            }
        )
    return output.getvalue()


def _citations_md(pack: dict[str, Any]) -> str:
    citation = pack["citation_autopilot"]
    source = pack["source_summary"]
    lines = [
        "# Citation Autopilot",
        "",
        f"Status: **{citation['citation_status']}**",
        f"Source used: **{source['used_source_mode']}**",
        "",
        citation["gbif_download_warning"],
        "",
        "## Suggested Methods Text",
        "",
        citation["methods_text"],
        "",
        "## Dataset Contributions",
        "",
        "| datasetKey | Records | License |",
        "| --- | ---: | --- |",
    ]
    for row in pack["dataset_contributions"]:
        lines.append(f"| {row['datasetKey']} | {row['record_count']} | {row.get('license') or 'unknown'} |")
    lines.extend(["", "Create a DOI-backed GBIF download or derived dataset before formal publication."])
    return "\n".join(lines) + "\n"


def _claim_guardrails_md(pack: dict[str, Any]) -> str:
    guardrails = pack["claim_guardrails"]
    lines = ["# Claim Guardrails", ""]
    sections = [
        ("Supported Claims", guardrails["supported_claims"]),
        ("Weak Claims", guardrails["weak_claims"]),
        ("Unsupported Claims", guardrails["unsupported_claims"]),
        ("Required Verification", guardrails["required_verification"]),
    ]
    for title, rows in sections:
        lines.extend([f"## {title}", ""])
        lines.extend(f"- {row}" for row in rows)
        lines.append("")
    return "\n".join(lines)


def _methods_text_md(pack: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Methods Text",
            "",
            pack["citation_autopilot"]["methods_text"],
            "",
            "## Known Limitations",
            "",
            "- No-evidence cells are survey targets, not absence observations.",
            "- The readiness score is a purpose-aware decision-support heuristic, not a biological truth.",
            "- Formal research or policy use requires a DOI-backed GBIF occurrence download or derived dataset where applicable.",
        ]
    ) + "\n"


def _publisher_feedback_md(pack: dict[str, Any]) -> str:
    lines = [
        "# Publisher Feedback Pack",
        "",
        "| datasetKey | Records affected | Main issue | Suggested fix |",
        "| --- | ---: | --- | --- |",
    ]
    for row in pack["publisher_feedback"]:
        lines.append(
            f"| {row['datasetKey']} | {row['records_affected']} | {row['main_issue']} | {row['suggested_fix']} |"
        )
    return "\n".join(lines) + "\n"


def _passport_md(pack: dict[str, Any]) -> str:
    summary = pack["passport"]
    readiness = pack["evidence_readiness"]
    citation = pack["citation_autopilot"]
    source = pack["source_summary"]
    grid_meta = pack["grid_metrics"]["meta"]
    lines = [
        f"# GBIF Evidence Passport: {summary['taxon']}",
        "",
        f"- Region: {summary['region_name']}",
        f"- Purpose: {readiness['purpose_label']}",
        f"- Source used: {source['used_source_mode']}",
        f"- Records used: {summary['records_used']}",
        f"- Datasets used: {summary['datasets_used']}",
        f"- Evidence readiness: {readiness['score']}/100",
        f"- Citation status: {citation['citation_status']}",
        "",
        "## Source Summary",
        "",
        f"- Requested source mode: {source['requested_source_mode']}",
        f"- GBIF API status: {source['gbif_api_status']}",
        f"- Fixture fallback used: {source['fallback_used']}",
        "",
        "## Grid Summary",
        "",
        f"- Total cells: {grid_meta['cell_count']}",
        f"- Occupied cells: {grid_meta['occupied_cell_count']}",
        f"- Empty/no-evidence cells: {grid_meta['empty_cell_count']}",
        f"- Under-sampled occupied cells: {grid_meta['under_sampled_occupied_cells']}",
        f"- Survey priority cells: {grid_meta['survey_priority_cells']}",
        "",
        "## Readiness Components",
        "",
        "| Component | Score | Weight |",
        "| --- | ---: | ---: |",
    ]
    for key, score in readiness["components"].items():
        lines.append(f"| {key.replace('_', ' ').title()} | {score} | {readiness['weights'][key]} |")
    lines.extend(["", "## Purpose Comparison", "", "| Purpose | Score |", "| --- | ---: |"])
    for row in pack["purpose_score_matrix"].values():
        lines.append(f"| {row['purpose_label']} | {row['score']} |")
    lines.extend([
        "",
        "## Top Sampling Priorities",
        "",
        "| Cell | Score | Label | Reasons |",
        "| --- | ---: | --- | --- |",
    ])
    for cell in grid_meta.get("top_survey_priority_cells", []):
        lines.append(
            f"| {cell['cell_id']} | {cell['score']} | {cell['label']} | {'; '.join(cell.get('reasons') or [])} |"
        )
    lines.extend([
        "",
        "## Main Risks",
        "",
    ])
    lines.extend(f"- {risk}" for risk in pack["main_risks"])
    lines.extend(["", "## Allowed Claims", ""])
    lines.extend(f"- {claim}" for claim in pack["claim_guardrails"]["supported_claims"])
    lines.extend(["", "## Weak Claims", ""])
    lines.extend(f"- {claim}" for claim in pack["claim_guardrails"]["weak_claims"])
    lines.extend(["", "## Unsupported Claims", ""])
    lines.extend(f"- {claim}" for claim in pack["claim_guardrails"]["unsupported_claims"])
    lines.extend(["", "## Required Verification", ""])
    lines.extend(f"- {claim}" for claim in pack["claim_guardrails"]["required_verification"])
    lines.extend(["", "## Citation Guidance", "", citation["gbif_download_warning"], "", citation["methods_text"]])
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in pack["next_actions"])
    return "\n".join(lines) + "\n"


def _passport_html(pack: dict[str, Any]) -> str:
    summary = pack["passport"]
    readiness = pack["evidence_readiness"]
    quality = pack["quality_metrics"]
    citation = pack["citation_autopilot"]
    source = pack["source_summary"]
    grid_meta = pack["grid_metrics"]["meta"]
    map_svg = _passport_map_svg(pack)
    thesis = _scientific_thesis(pack)
    components = "".join(
        f"""
        <tr>
          <td>{_escape(key.replace('_', ' ').title())}</td>
          <td>{score}</td>
          <td>{readiness['weights'][key]}</td>
        </tr>"""
        for key, score in readiness["components"].items()
    )
    purpose_rows = "".join(
        f"""
        <tr>
          <td>{_escape(row['purpose_label'])}</td>
          <td>{row['score']}</td>
        </tr>"""
        for row in pack["purpose_score_matrix"].values()
    )
    priority_rows = "".join(
        f"""
        <tr>
          <td>{_escape(row['cell_id'])}</td>
          <td>{row['score']}</td>
          <td>{_escape(row['label'])}</td>
          <td>{_escape('; '.join(row.get('reasons') or []))}</td>
        </tr>"""
        for row in grid_meta.get("top_survey_priority_cells", [])
    ) or '<tr><td colspan="4">No survey-priority cells generated.</td></tr>'
    datasets = "".join(
        f"""
        <tr>
          <td>{_escape(row['datasetKey'])}</td>
          <td>{row['record_count']}</td>
          <td>{_escape(row.get('license') or 'unknown')}</td>
          <td>{_escape(row.get('main_issues') or 'none_detected')}</td>
        </tr>"""
        for row in pack["dataset_contributions"]
    )
    risks = _list_html(pack["main_risks"])
    next_actions = _list_html(pack["next_actions"])
    supported = _list_html(pack["claim_guardrails"]["supported_claims"])
    weak = _list_html(pack["claim_guardrails"]["weak_claims"])
    unsupported = _list_html(pack["claim_guardrails"]["unsupported_claims"])
    required = _list_html(pack["claim_guardrails"]["required_verification"])
    warnings = _list_html(source["warnings"]) if source["warnings"] else "<p>No source warnings.</p>"
    score = pack["evidence_readiness"]["score"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>GBIF Evidence Passport</title>
  <style>
    :root {{ color: #17201a; font-family: Inter, Arial, sans-serif; }}
    body {{ background: #f4f7f1; margin: 0; line-height: 1.55; }}
    main {{ margin: 0 auto; max-width: 1120px; padding: 36px 24px; }}
    header, section {{ background: #fff; border: 1px solid #dce5dd; border-radius: 8px; margin-bottom: 18px; padding: 22px; }}
    h1, h2, h3 {{ margin: 0; }}
    h1 {{ font-size: 2rem; }}
    h2 {{ font-size: 1.05rem; margin-bottom: 12px; }}
    .eyebrow {{ color: #5f6f68; font-size: .76rem; font-weight: 800; text-transform: uppercase; }}
    .hero {{ align-items: center; display: flex; gap: 20px; justify-content: space-between; }}
    .score {{ background: #e4f2e7; border: 1px solid #bcd8c5; border-radius: 8px; color: #1d6147; font-size: 2.2rem; font-weight: 800; padding: 16px 18px; }}
    .kpis {{ display: grid; gap: 12px; grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .kpi {{ background: #f7f9f5; border: 1px solid #e1e9e2; border-radius: 8px; padding: 14px; }}
    .kpi strong {{ display: block; font-size: 1.3rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #e7ece8; padding: 9px; text-align: left; vertical-align: top; }}
    th {{ color: #4a5b53; font-size: .82rem; }}
    .claims {{ display: grid; gap: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .map-wrap {{ background: #e8f1f4; border: 1px solid #bfd0d6; border-radius: 8px; overflow: hidden; position: relative; }}
    .map-wrap svg {{ display: block; height: auto; width: 100%; }}
    .map-thesis {{ background: #f6faf7; border: 1px solid #dce8df; border-radius: 8px; font-weight: 700; padding: 12px; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 10px; }}
    .legend span {{ align-items: center; color: #4e5f56; display: inline-flex; font-size: .84rem; gap: 6px; }}
    .dot, .cell {{ background: #206b4f; border-radius: 50%; display: inline-block; height: 10px; width: 10px; }}
    .dot.issue {{ background: #bd553d; }}
    .cell {{ background: #e4a24e; border-radius: 2px; }}
    .cell.empty {{ background: #8ca0ad; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li + li {{ margin-top: 6px; }}
    .warning {{ background: #fff6de; border: 1px solid #ead493; border-radius: 8px; padding: 12px; }}
    @media (max-width: 760px) {{ .hero, .claims {{ display: block; }} .kpis {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <div>
        <p class="eyebrow">GBIF Evidence Passport</p>
        <h1>{_escape(summary['taxon'])}</h1>
        <p>{_escape(summary['region_name'])} · {_escape(readiness['purpose_label'])}</p>
      </div>
      <div class="score">{score}/100</div>
    </header>
    <section class="kpis" aria-label="Evidence summary">
      <div class="kpi"><span>Records</span><strong>{summary['records_used']}</strong></div>
      <div class="kpi"><span>Datasets</span><strong>{summary['datasets_used']}</strong></div>
      <div class="kpi"><span>Missing dates</span><strong>{quality['missing_date_count']}</strong></div>
      <div class="kpi"><span>High uncertainty</span><strong>{quality['high_uncertainty_count']}</strong></div>
    </section>
    <section>
      <h2>Scientific Evidence Map</h2>
      <p class="map-thesis">{_escape(thesis)}</p>
      <div class="map-wrap">{map_svg}</div>
      <div class="legend">
        <span><i class="dot"></i>occurrence record</span>
        <span><i class="dot issue"></i>quality caveat</span>
        <span><i class="cell empty"></i>no-evidence cell</span>
        <span><i class="cell"></i>under-sampled occupied</span>
      </div>
    </section>
    <section>
      <h2>Source & Provenance</h2>
      <table><tbody>
        <tr><th>Requested source mode</th><td>{_escape(source['requested_source_mode'])}</td></tr>
        <tr><th>Used source mode</th><td>{_escape(source['used_source_mode'])}</td></tr>
        <tr><th>GBIF API status</th><td>{_escape(source['gbif_api_status'])}</td></tr>
        <tr><th>Fallback used</th><td>{_escape(source['fallback_used'])}</td></tr>
        <tr><th>Taxon key</th><td>{_escape(summary.get('taxonKey'))}</td></tr>
        <tr><th>Match confidence</th><td>{_escape(summary.get('match_confidence'))}</td></tr>
      </tbody></table>
      {warnings}
    </section>
    <section class="kpis" aria-label="Grid summary">
      <div class="kpi"><span>Total cells</span><strong>{grid_meta['cell_count']}</strong></div>
      <div class="kpi"><span>Occupied cells</span><strong>{grid_meta['occupied_cell_count']}</strong></div>
      <div class="kpi"><span>No-evidence cells</span><strong>{grid_meta['empty_cell_count']}</strong></div>
      <div class="kpi"><span>Survey priorities</span><strong>{grid_meta['survey_priority_cells']}</strong></div>
    </section>
    <section>
      <h2>Sampling Gap Engine</h2>
      <p>No-evidence cells are ranked as survey priorities, never as absence observations.</p>
      <table><thead><tr><th>Cell</th><th>Gap score</th><th>Label</th><th>Reasons</th></tr></thead><tbody>{priority_rows}</tbody></table>
    </section>
    <section>
      <h2>Readiness Components</h2>
      <table><thead><tr><th>Component</th><th>Score</th><th>Purpose weight</th></tr></thead><tbody>{components}</tbody></table>
    </section>
    <section>
      <h2>Purpose Comparison</h2>
      <table><thead><tr><th>Purpose</th><th>Score</th></tr></thead><tbody>{purpose_rows}</tbody></table>
    </section>
    <section>
      <h2>Main Risks</h2>
      {risks}
    </section>
    <section class="claims">
      <div><h2>Supported Claims</h2>{supported}</div>
      <div><h2>Weak Claims</h2>{weak}</div>
      <div><h2>Unsupported Claims</h2>{unsupported}</div>
      <div><h2>Required Verification</h2>{required}</div>
    </section>
    <section>
      <h2>Citation Guidance</h2>
      <p class="warning">{_escape(citation['gbif_download_warning'])}</p>
      <p>{_escape(citation['methods_text'])}</p>
    </section>
    <section>
      <h2>Dataset Contributions</h2>
      <table><thead><tr><th>datasetKey</th><th>Records</th><th>License</th><th>Main issues</th></tr></thead><tbody>{datasets}</tbody></table>
    </section>
    <section>
      <h2>Next Actions</h2>
      {next_actions}
    </section>
  </main>
</body>
</html>
"""


def _scientific_thesis(pack: dict[str, Any]) -> str:
    grid_meta = pack["grid_metrics"]["meta"]
    quality = pack["quality_metrics"]
    if grid_meta["empty_cell_count"] > grid_meta["occupied_cell_count"]:
        return (
            f"The evidence supports presence and sampling-priority claims, but "
            f"{grid_meta['empty_cell_count']} no-evidence cells cannot be interpreted as absence."
        )
    if quality["high_uncertainty_count"]:
        return (
            f"The evidence is useful for regional screening, while "
            f"{quality['high_uncertainty_count']} high-uncertainty records need geospatial review."
        )
    return "The evidence pack supports a bounded biodiversity claim with explicit provenance and citation caveats."


def _passport_map_svg(pack: dict[str, Any]) -> str:
    bbox = pack["passport"]["bbox"]
    height = 68.0
    cells = []
    for feature in pack["grid_metrics"]["features"]:
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"][0]
        x1, y1 = _project(coords[0][0], coords[2][1], bbox, height)
        x2, y2 = _project(coords[1][0], coords[0][1], bbox, height)
        css_class = "empty" if props.get("empty_cell") else "under" if props.get("under_sampled") else "occupied"
        title = _escape(
            f"{props['cell_id']}: {props['occurrence_count']} records, coverage {props['sampling_coverage_proxy']}"
        )
        cells.append(
            f'<rect class="grid-cell {css_class}" x="{x1:.2f}" y="{y1:.2f}" '
            f'width="{max(0, x2 - x1):.2f}" height="{max(0, y2 - y1):.2f}"><title>{title}</title></rect>'
        )
    points = []
    for feature in pack["records_geojson"]["features"]:
        lon, lat = feature["geometry"]["coordinates"]
        x, y = _project(lon, lat, bbox, height)
        props = feature["properties"]
        issue = bool(props.get("issues")) or (props.get("coordinateUncertaintyInMeters") or 0) > 10000
        css_class = "issue" if issue else ""
        title = _escape(f"{props.get('gbif_id')} · {props.get('datasetKey')} · {lon:.3f}, {lat:.3f}")
        points.append(f'<circle class="record {css_class}" cx="{x:.2f}" cy="{y:.2f}" r="1.25"><title>{title}</title></circle>')
    return f"""
        <svg role="img" aria-label="Static scientific evidence map" viewBox="0 0 100 {height:g}" preserveAspectRatio="xMidYMid meet">
          <style>
            .sea {{ fill: #d5e7ed; }}
            .land {{ fill: #dce5cd; stroke: #7c986f; stroke-width: .45; vector-effect: non-scaling-stroke; }}
            .grid-line {{ stroke: rgba(53,87,99,.22); stroke-dasharray: 1.2 1.2; stroke-width: .25; vector-effect: non-scaling-stroke; }}
            .bbox {{ fill: none; stroke: rgba(28,72,91,.78); stroke-width: .55; vector-effect: non-scaling-stroke; }}
            .grid-cell {{ stroke: rgba(36,69,59,.42); stroke-width: .36; vector-effect: non-scaling-stroke; }}
            .grid-cell.empty {{ fill: rgba(63,90,110,.14); stroke-dasharray: 1.1 .9; }}
            .grid-cell.under {{ fill: rgba(224,143,57,.36); stroke: rgba(160,83,29,.72); }}
            .grid-cell.occupied {{ fill: rgba(44,125,83,.28); stroke: rgba(32,94,69,.72); }}
            .record {{ fill: #176b4f; stroke: #fff; stroke-width: .55; vector-effect: non-scaling-stroke; }}
            .record.issue {{ fill: #bd553d; }}
            .label {{ fill: rgba(43,65,57,.7); font-size: 2.1px; font-weight: 800; letter-spacing: 0; paint-order: stroke; stroke: rgba(255,255,255,.82); stroke-width: .65; text-anchor: middle; }}
          </style>
          <rect class="sea" x="0" y="0" width="100" height="{height:g}"></rect>
          <polygon class="land" points="{_static_iberia_points(bbox, height)}"><title>Iberian Peninsula</title></polygon>
          <line class="grid-line" x1="25" x2="25" y1="0" y2="{height:g}"></line>
          <line class="grid-line" x1="50" x2="50" y1="0" y2="{height:g}"></line>
          <line class="grid-line" x1="75" x2="75" y1="0" y2="{height:g}"></line>
          <line class="grid-line" x1="0" x2="100" y1="{height / 4:.2f}" y2="{height / 4:.2f}"></line>
          <line class="grid-line" x1="0" x2="100" y1="{height / 2:.2f}" y2="{height / 2:.2f}"></line>
          <line class="grid-line" x1="0" x2="100" y1="{height * 3 / 4:.2f}" y2="{height * 3 / 4:.2f}"></line>
          <text class="label" x="44" y="28">Iberian Peninsula</text>
          <text class="label" x="46" y="37">Spain</text>
          <rect class="bbox" x=".6" y=".6" width="98.8" height="{height - 1.2:.2f}"></rect>
          {''.join(cells)}
          {''.join(points)}
        </svg>
    """


def _static_iberia_points(bbox: list[float], height: float) -> str:
    coords = [
        (-9.5, 43.7),
        (-8.1, 43.35),
        (-6.2, 43.72),
        (-2.5, 43.47),
        (0.7, 42.75),
        (3.15, 41.95),
        (3.25, 40.45),
        (1.15, 39.25),
        (0.0, 38.62),
        (-0.65, 37.78),
        (-2.25, 36.75),
        (-5.0, 36.08),
        (-6.65, 36.02),
        (-7.38, 37.05),
        (-8.85, 37.0),
        (-9.3, 38.5),
        (-9.15, 40.15),
        (-9.62, 41.6),
        (-9.5, 43.7),
    ]
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in (_project(lon, lat, bbox, height) for lon, lat in coords))


def _project(lon: float, lat: float, bbox: list[float], height: float) -> tuple[float, float]:
    west, south, east, north = bbox
    x = max(0.0, min(100.0, ((lon - west) / (east - west)) * 100.0))
    y = max(0.0, min(height, height - ((lat - south) / (north - south)) * height))
    return x, y


def _list_html(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in items) + "</ul>"


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)
