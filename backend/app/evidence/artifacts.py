from __future__ import annotations

import csv
import html
import io
import json
import re
from typing import Any


def build_graph_memory(pack: dict[str, Any]) -> dict[str, Any]:
    """Build a portable evidence graph and Markdown vault for a passport run."""
    summary = pack["passport"]
    run = pack["run"]
    readiness = pack["evidence_readiness"]
    taxon_label = summary.get("accepted_name") or summary["taxon"]
    run_id = run["run_id"]
    run_node = f"run:{run_id}"
    taxon_node = f"taxon:{summary.get('taxonKey') or _slug(taxon_label)}"
    region_node = f"region:{_slug(summary['region_name'])}"
    purpose_node = f"purpose:{readiness['purpose']}"
    nodes = [
        _graph_node(run_node, "run", f"{taxon_label} in {summary['region_name']}", run_id=run_id),
        _graph_node(taxon_node, "taxon", taxon_label, taxonKey=summary.get("taxonKey")),
        _graph_node(region_node, "region", summary["region_name"], bbox=summary.get("bbox")),
        _graph_node(purpose_node, "purpose", readiness["purpose_label"], purpose=readiness["purpose"]),
    ]
    edges = [
        _graph_edge(run_node, "uses_taxon", taxon_node),
        _graph_edge(run_node, "covers_region", region_node),
        _graph_edge(run_node, "serves_purpose", purpose_node),
    ]

    dataset_nodes = []
    for dataset in pack["dataset_contributions"]:
        node_id = f"dataset:{dataset['datasetKey']}"
        dataset_nodes.append(node_id)
        nodes.append(
            _graph_node(
                node_id,
                "dataset",
                dataset["datasetKey"],
                records=dataset.get("record_count"),
                license=dataset.get("license"),
                publisher=dataset.get("publisher"),
            )
        )
        edges.append(_graph_edge(run_node, "draws_from_dataset", node_id, records=dataset.get("record_count")))

    issue_nodes: dict[str, str] = {}
    for feedback in pack["publisher_feedback"]:
        issue = feedback["main_issue"]
        issue_id = issue_nodes.setdefault(issue, f"issue:{_slug(issue)}")
        if not any(node["id"] == issue_id for node in nodes):
            nodes.append(_graph_node(issue_id, "issue", issue, severity=feedback.get("severity")))
            edges.append(_graph_edge(run_node, "detects_issue", issue_id))
        dataset_id = f"dataset:{feedback['datasetKey']}"
        edges.append(
            _graph_edge(
                dataset_id,
                "has_quality_issue",
                issue_id,
                records_affected=feedback.get("records_affected"),
                severity=feedback.get("severity"),
            )
        )

    claim_nodes = []
    for status, claims in [
        ("supported", pack["claim_guardrails"]["supported_claims"]),
        ("weak", pack["claim_guardrails"]["weak_claims"]),
        ("blocked", pack["claim_guardrails"]["unsupported_claims"]),
        ("requires_verification", pack["claim_guardrails"]["required_verification"]),
    ]:
        for claim in claims:
            claim_id = f"claim:{_slug(status + '-' + claim)[:88]}"
            claim_nodes.append((claim_id, status, claim))
            nodes.append(_graph_node(claim_id, "claim", claim, status=status))
            edges.append(_graph_edge(run_node, f"{status}_claim", claim_id))
            if status in {"blocked", "requires_verification"}:
                for issue_id in issue_nodes.values():
                    edges.append(_graph_edge(issue_id, "limits_claim", claim_id))

    action_nodes = []
    for action in pack["next_actions"]:
        action_id = f"action:{_slug(action)[:88]}"
        action_nodes.append((action_id, action))
        nodes.append(_graph_node(action_id, "action", action))
        edges.append(_graph_edge(run_node, "recommends_action", action_id))

    artifact_nodes = []
    for name in [
        "passport.html",
        "decision_memo.md",
        "submission_readiness.md",
        "validation_summary.md",
        "run.json",
        "citations.md",
        "publisher_feedback.md",
        "evidence_pack.zip",
    ]:
        artifact_id = f"artifact:{name}"
        artifact_nodes.append(artifact_id)
        nodes.append(_graph_node(artifact_id, "artifact", name))
        edges.append(_graph_edge(run_node, "produces_artifact", artifact_id))

    graph = {
        "summary": {
            "title": "EcoGenesis Evidence Graph Memory",
            "run_id": run_id,
            "taxon": taxon_label,
            "region_name": summary["region_name"],
            "purpose": readiness["purpose"],
            "purpose_label": readiness["purpose_label"],
            "score": readiness["score"],
            "records_used": summary["records_used"],
            "datasets_used": summary["datasets_used"],
            "created_at": run["finished_at"],
        },
        "node_counts": {
            "runs": 1,
            "taxa": 1,
            "regions": 1,
            "datasets": len(dataset_nodes),
            "issues": len(issue_nodes),
            "claims": len(claim_nodes),
            "actions": len(action_nodes),
            "artifacts": len(artifact_nodes),
        },
        "nodes": nodes,
        "edges": edges,
        "memory_cards": _memory_cards(pack),
    }
    vault = _build_vault(pack, graph, claim_nodes, action_nodes)
    return {"graph": graph, "vault": vault}


def build_artifacts(pack: dict[str, Any]) -> dict[str, str]:
    return {
        "evidence_pack.json": json.dumps(pack, indent=2, ensure_ascii=False),
        "run.json": json.dumps(pack["run"], indent=2, ensure_ascii=False),
        "source_summary.json": json.dumps(pack["source_summary"], indent=2, ensure_ascii=False),
        "demo_scenario.json": json.dumps(_demo_scenario(pack), indent=2, ensure_ascii=False),
        "decision_memo.json": json.dumps(pack["decision_memo"], indent=2, ensure_ascii=False),
        "decision_memo.md": _decision_memo_md(pack),
        "submission_readiness.json": json.dumps(pack["submission_readiness"], indent=2, ensure_ascii=False),
        "submission_readiness.md": _submission_readiness_md(pack),
        "validation_summary.json": json.dumps(pack["validation_summary"], indent=2, ensure_ascii=False),
        "validation_summary.md": _validation_summary_md(pack),
        "impact_brief.md": _impact_brief_md(pack),
        "video_script.md": _video_script_md(pack),
        "records.geojson": json.dumps(pack["records_geojson"], indent=2, ensure_ascii=False),
        "quality_metrics.csv": _quality_csv(pack["quality_metrics"]),
        "gap_priorities.csv": _gap_priorities_csv(pack),
        "readiness_scorecard.csv": _readiness_scorecard_csv(pack),
        "dataset_contributions.csv": _dataset_csv(pack["dataset_contributions"]),
        "publisher_feedback.csv": _publisher_feedback_csv(pack["publisher_feedback"]),
        "publisher_issue_templates.md": _publisher_issue_templates_md(pack),
        "derived_dataset_recipe.json": json.dumps(pack["citation_autopilot"]["derived_dataset_recipe"], indent=2, ensure_ascii=False),
        "evidence_graph.json": json.dumps(pack["graph_memory"]["graph"], indent=2, ensure_ascii=False),
        "graph_memory.md": _graph_memory_md(pack),
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
    fields = ["datasetKey", "severity", "fix_priority", "records_affected", "main_issue", "suggested_fix"]
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
        "decision_memo": pack["decision_memo"],
        "validation_summary": pack["validation_summary"],
        "submission_readiness": pack["submission_readiness"],
        "evidence_graph": pack["graph_memory"]["graph"],
        "known_limitations": [
            "GBIF-mediated occurrence records are heterogeneous and reflect variable sampling effort.",
            "No-evidence grid cells are not absence observations.",
            "Occurrence counts alone do not establish abundance or population trends.",
            "Fixture and fallback runs are reproducible demo artifacts, not publication citation bases.",
        ],
    }


def _decision_memo_md(pack: dict[str, Any]) -> str:
    memo = pack["decision_memo"]
    lines = [
        "# Decision Memo",
        "",
        f"Verdict: **{memo['verdict']}**",
        "",
        "## 1. Question",
        "",
        memo["question"],
        "",
        "## 2. Evidence Basis",
        "",
        memo["data_basis"],
        "",
        "## 3. Fitness For Purpose",
        "",
        memo["fitness_for_purpose"],
        "",
        "## 4. Safe Claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in memo["safe_claims"])
    lines.extend(["", "## 5. Blocked Claims", ""])
    lines.extend(f"- {claim}" for claim in memo["blocked_claims"])
    lines.extend(["", "## Main Limitations", ""])
    lines.extend(f"- {item}" for item in memo["main_limitations"])
    lines.extend(
        [
            "",
            "## Recommended Next Action",
            "",
            memo["recommended_next_action"],
            "",
            "## Plain-Language Summary",
            "",
            memo["plain_language_summary"],
            "",
            "## Who Benefits",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in memo["user_value"])
    lines.extend(
        [
            "",
            "## Citation Gate",
            "",
            f"- Status: {memo['citation_gate']['status']}",
            f"- Publication ready: {memo['citation_gate']['publication_ready']}",
            f"- Message: {memo['citation_gate']['message']}",
        ]
    )
    return "\n".join(lines) + "\n"


def _submission_readiness_md(pack: dict[str, Any]) -> str:
    readiness = pack["submission_readiness"]
    lines = [
        "# Submission Readiness",
        "",
        f"Stage: **{readiness['stage']}**",
        f"Ready checks: **{readiness['ready_count']}/{readiness['total_count']}**",
        "",
        "## Checklist",
        "",
        "| Ready | Item | Evidence | Next step |",
        "| --- | --- | --- | --- |",
    ]
    for item in readiness["checklist"]:
        marker = "yes" if item["ready"] else "not yet"
        lines.append(f"| {marker} | {item['label']} | {item['evidence']} | {item['next_step']} |")
    lines.extend(["", "## Accepted Research Comments", ""])
    lines.extend(f"- {item}" for item in readiness["accepted_research_comments"])
    lines.extend(["", "## Next 72 Hours", ""])
    lines.extend(f"- {item}" for item in readiness["next_72_hours"])
    return "\n".join(lines) + "\n"


def _validation_summary_md(pack: dict[str, Any]) -> str:
    validation = pack["validation_summary"]
    case = validation["current_case"]
    lines = [
        "# Validation Summary",
        "",
        f"Current case: **{case['taxon']} - {case['region_name']} - {case['purpose_label']}**",
        f"Score: **{case['score']}/100**",
        f"Source mode: **{case['source_mode']}**",
        f"Passed checks: **{validation['passed_checks']}/{validation['total_checks']}**",
        "",
        "## Checks",
        "",
        "| Passed | Check | Metric | Why it matters |",
        "| --- | --- | ---: | --- |",
    ]
    for check in validation["checks"]:
        lines.append(
            f"| {'yes' if check['passed'] else 'not yet'} | {check['label']} | {check['metric']} | {check['why_it_matters']} |"
        )
    lines.extend(["", "## Measurable Outcomes", ""])
    lines.extend(f"- {item}" for item in validation["measurable_outcomes"])
    lines.extend(["", "## Recommended Demo Suite", ""])
    for scenario in validation["recommended_demo_suite"]:
        lines.append(
            f"- **{scenario['id']}**: {scenario['taxon']} in {scenario['region_name']} for {scenario['purpose']} - {scenario['shows']}"
        )
    lines.extend(["", "## Remaining Validation Work", ""])
    lines.extend(f"- {item}" for item in validation["remaining_validation_work"])
    return "\n".join(lines) + "\n"


def _impact_brief_md(pack: dict[str, Any]) -> str:
    summary = pack["passport"]
    memo = pack["decision_memo"]
    return "\n".join(
        [
            "# Impact Brief",
            "",
            f"EcoGenesis Evidence Atlas turns GBIF-mediated records for **{summary['taxon']}** in **{summary['region_name']}** into a bounded evidence decision memo.",
            "",
            "## What It Solves",
            "",
            "- Users often see GBIF points but do not know whether they can support a specific decision.",
            "- Empty map cells are easy to misuse as absences.",
            "- Citation, DOI and datasetKey provenance are often handled after analysis instead of during analysis.",
            "- Dataset publishers rarely receive concise, prioritized feedback from downstream reuse.",
            "",
            "## What The Current Run Gives",
            "",
            f"- Verdict: {memo['verdict']}",
            f"- Records used: {summary['records_used']}",
            f"- Datasets used: {summary['datasets_used']}",
            f"- Evidence readiness: {pack['evidence_readiness']['score']}/100",
            f"- Recommended action: {memo['recommended_next_action']}",
            "",
            "## Value For GBIF",
            "",
            "- Promotes responsible reuse of GBIF-mediated occurrence data.",
            "- Preserves datasetKey-level attribution and contribution counts.",
            "- Makes data gaps and publisher-side quality issues visible.",
            "- Produces reusable open-science artifacts rather than a screenshot-only result.",
            "",
            "## Value For EcoGenesis",
            "",
            "- Turns the app into a trust layer and knowledge workbench, not just a map.",
            "- Adds reusable exports that can support future RAG, review, collaboration and publishing workflows.",
            "- Gives each run a portable evidence memory that can be compared with future runs.",
        ]
    ) + "\n"


def _video_script_md(pack: dict[str, Any]) -> str:
    summary = pack["passport"]
    memo = pack["decision_memo"]
    readiness = pack["submission_readiness"]
    lines = [
        "# Three-Minute Demo Script",
        "",
        "## 0:00-0:20 Problem",
        "",
        "GBIF users can find occurrence records quickly, but they still need to know what the data can responsibly support, what it cannot support, and how to cite it.",
        "",
        "## 0:20-0:55 Generate Passport",
        "",
        f"Show the default run for {summary['taxon']} in {summary['region_name']}. Point to the decision memo verdict: {memo['verdict']}.",
        "",
        "## 0:55-1:30 Evidence Map",
        "",
        "Show occurrence points, quality caveats, no-evidence cells and survey-priority cells. Say explicitly that no-evidence cells are not absences.",
        "",
        "## 1:30-2:05 Claims And Citation",
        "",
        "Open Safe Claims and Citation. Show supported claims, blocked absence/distribution/trend claims, DOI completion flow and derived dataset recipe.",
        "",
        "## 2:05-2:35 Publisher Feedback And Graph Memory",
        "",
        "Open Publisher Fixes and Evidence Memory. Show datasetKey-level fixes and the offline Markdown vault.",
        "",
        "## 2:35-3:00 Export And Submission Readiness",
        "",
        f"Download the Evidence Pack. Show Submission Readiness at {readiness['ready_count']}/{readiness['total_count']} checks and name the remaining DOI-backed publication case as the honest final step.",
    ]
    return "\n".join(lines) + "\n"


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
        "## DOI Completion Checklist",
        "",
    ]
    for item in citation["doi_completion_flow"]:
        marker = "x" if item["ready"] else " "
        lines.append(f"- [{marker}] **{item['label']}**: {item['action']}")
    lines.extend([
        "",
        "## Suggested Methods Text",
        "",
        citation["methods_text"],
        "",
        "## Journal-Ready Methods Text",
        "",
        citation["journal_methods_text"],
        "",
        "## Dataset Contributions",
        "",
        "| datasetKey | Records | License |",
        "| --- | ---: | --- |",
    ])
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
        "| Priority | Severity | datasetKey | Records affected | Main issue | Suggested fix |",
        "| ---: | --- | --- | ---: | --- | --- |",
    ]
    for row in pack["publisher_feedback"]:
        lines.append(
            f"| {row.get('fix_priority')} | {row.get('severity')} | {row['datasetKey']} | {row['records_affected']} | {row['main_issue']} | {row['suggested_fix']} |"
        )
    return "\n".join(lines) + "\n"


def _publisher_issue_templates_md(pack: dict[str, Any]) -> str:
    if not pack["publisher_feedback"]:
        return "\n".join(
            [
                "# Publisher Issue Templates",
                "",
                "No publisher-facing data quality issues were detected by this run.",
                "",
                "If users inspect the records manually and find issues, keep `datasetKey`, `gbifID`, issue type, coordinates and event dates in the report.",
            ]
        ) + "\n"
    lines = [
        "# Publisher Issue Templates",
        "",
        "These templates are designed for polite, evidence-backed feedback to GBIF data publishers or node data managers.",
        "They preserve `datasetKey`, affected-record counts and the specific quality concern detected by the Evidence Passport.",
        "",
    ]
    for row in pack["publisher_feedback"]:
        lines.extend(
            [
                f"## Priority {row.get('fix_priority')}: {row['datasetKey']}",
                "",
                f"Severity: `{row.get('severity')}`",
                f"Records affected: `{row.get('records_affected')}`",
                f"Main issue: `{row.get('main_issue')}`",
                "",
                "Suggested message:",
                "",
                "```text",
                row.get("publisher_issue_template") or _fallback_issue_template(row),
                "```",
                "",
                f"Suggested fix: {row.get('suggested_fix')}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def _fallback_issue_template(row: dict[str, Any]) -> str:
    return (
        f"Hello, this EcoGenesis Evidence Passport detected {row.get('records_affected')} records in dataset "
        f"{row.get('datasetKey')} with the issue '{row.get('main_issue')}'. Suggested fix: {row.get('suggested_fix')}"
    )


def _passport_md(pack: dict[str, Any]) -> str:
    summary = pack["passport"]
    readiness = pack["evidence_readiness"]
    citation = pack["citation_autopilot"]
    source = pack["source_summary"]
    memo = pack["decision_memo"]
    submission = pack["submission_readiness"]
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
        "## Decision Memo",
        "",
        f"**Verdict:** {memo['verdict']}",
        "",
        f"**Question:** {memo['question']}",
        "",
        f"**Evidence basis:** {memo['data_basis']}",
        "",
        f"**Fitness for purpose:** {memo['fitness_for_purpose']}",
        "",
        f"**Recommended next action:** {memo['recommended_next_action']}",
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
    lines.extend(["", "## Graph Memory", "", "- Evidence graph: evidence_graph.json", "- Human-readable summary: graph_memory.md", "- Offline vault: evidence_vault.zip"])
    lines.extend(
        [
            "",
            "## Submission Readiness",
            "",
            f"- Stage: {submission['stage']}",
            f"- Ready checks: {submission['ready_count']}/{submission['total_count']}",
            "- Detailed checklist: submission_readiness.md",
            "- Validation summary: validation_summary.md",
            "- Demo script: video_script.md",
        ]
    )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in pack["next_actions"])
    return "\n".join(lines) + "\n"


def _graph_memory_md(pack: dict[str, Any]) -> str:
    graph = pack["graph_memory"]["graph"]
    summary = graph["summary"]
    lines = [
        "# Evidence Graph Memory",
        "",
        f"Run: `{summary['run_id']}`",
        f"Taxon: **{summary['taxon']}**",
        f"Region: **{summary['region_name']}**",
        f"Purpose: **{summary['purpose_label']}**",
        f"Readiness: **{summary['score']}/100**",
        "",
        "## What This Adds",
        "",
        "This graph memory turns the passport from a one-off report into a connected evidence node. It links the run to taxa, regions, datasets, quality issues, claims, actions and export artifacts.",
        "",
        "## Node Counts",
        "",
        "| Node type | Count |",
        "| --- | ---: |",
    ]
    for key, value in graph["node_counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Memory Cards", ""])
    for card in graph["memory_cards"]:
        lines.extend([f"### {card['title']}", "", card["body"], ""])
    lines.extend(["## Key Edges", "", "| Source | Relation | Target |", "| --- | --- | --- |"])
    for edge in graph["edges"][:24]:
        lines.append(f"| {edge['source']} | {edge['relation']} | {edge['target']} |")
    lines.extend(
        [
            "",
            "## Vault",
            "",
            "Open `evidence_vault.zip` to inspect the Markdown memory bundle. It is Obsidian-compatible, but every note is a normal Markdown file.",
        ]
    )
    return "\n".join(lines) + "\n"


def _passport_html(pack: dict[str, Any]) -> str:
    summary = pack["passport"]
    readiness = pack["evidence_readiness"]
    quality = pack["quality_metrics"]
    citation = pack["citation_autopilot"]
    source = pack["source_summary"]
    memo = pack["decision_memo"]
    submission = pack["submission_readiness"]
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
    safe_claims = _list_html(memo["safe_claims"])
    blocked_claims = _list_html(memo["blocked_claims"])
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
    .memo-grid {{ display: grid; gap: 14px; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .memo-card {{ background: #f7faf6; border: 1px solid #dde8df; border-radius: 8px; padding: 14px; }}
    .badge {{ background: #eef6ed; border: 1px solid #c9dec7; border-radius: 999px; display: inline-block; font-size: .78rem; font-weight: 800; padding: 4px 9px; }}
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
    @media (max-width: 760px) {{ .hero, .claims, .memo-grid {{ display: block; }} .kpis {{ grid-template-columns: 1fr; }} }}
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
      <h2>Decision Memo</h2>
      <p><span class="badge">{_escape(memo['verdict'])}</span></p>
      <div class="memo-grid">
        <div class="memo-card"><h3>Question</h3><p>{_escape(memo['question'])}</p></div>
        <div class="memo-card"><h3>Evidence Basis</h3><p>{_escape(memo['data_basis'])}</p></div>
        <div class="memo-card"><h3>Fitness</h3><p>{_escape(memo['fitness_for_purpose'])}</p></div>
        <div class="memo-card"><h3>Next Action</h3><p>{_escape(memo['recommended_next_action'])}</p></div>
      </div>
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
    <section class="claims">
      <div><h2>Decision-Safe Claims</h2>{safe_claims}</div>
      <div><h2>Blocked Claims</h2>{blocked_claims}</div>
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
    <section>
      <h2>Submission Readiness</h2>
      <p><strong>{submission['ready_count']}/{submission['total_count']}</strong> checks ready · {_escape(submission['stage'])}</p>
      <p>See <code>submission_readiness.md</code>, <code>validation_summary.md</code>, <code>impact_brief.md</code> and <code>video_script.md</code> in the export pack.</p>
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


def _graph_node(node_id: str, node_type: str, label: str, **properties: Any) -> dict[str, Any]:
    return {"id": node_id, "type": node_type, "label": label, "properties": properties}


def _graph_edge(source: str, relation: str, target: str, **properties: Any) -> dict[str, Any]:
    return {"source": source, "relation": relation, "target": target, "properties": properties}


def _memory_cards(pack: dict[str, Any]) -> list[dict[str, str]]:
    summary = pack["passport"]
    feedback_count = len(pack["publisher_feedback"])
    blocked_count = len(pack["claim_guardrails"]["unsupported_claims"])
    cards = [
        {
            "title": "Connected run memory",
            "body": (
                f"This run links {summary['records_used']} records, {summary['datasets_used']} datasets, "
                f"{blocked_count} blocked claims and {len(pack['next_actions'])} next actions."
            ),
        },
        {
            "title": "Dataset memory",
            "body": (
                f"{feedback_count} publisher feedback rows are connected to datasetKey-level provenance, "
                "so recurring quality blockers can be tracked across future runs."
            ),
        },
        {
            "title": "Claim memory",
            "body": "Blocked absence, distribution and trend claims are stored as graph nodes instead of disappearing into a static report.",
        },
        {
            "title": "Judge-friendly vault",
            "body": "The vault is a normal Markdown bundle that can be opened offline and reviewed without running the web application.",
        },
    ]
    return cards


def _build_vault(
    pack: dict[str, Any],
    graph: dict[str, Any],
    claim_nodes: list[tuple[str, str, str]],
    action_nodes: list[tuple[str, str]],
) -> dict[str, str]:
    summary = pack["passport"]
    run = pack["run"]
    readiness = pack["evidence_readiness"]
    run_file = f"runs/{run['run_id']}.md"
    taxon_file = f"taxa/{_slug(summary.get('accepted_name') or summary['taxon'])}.md"
    region_file = f"regions/{_slug(summary['region_name'])}.md"
    purpose_file = f"purposes/{readiness['purpose']}.md"
    files: dict[str, str] = {
        "index.md": _vault_index(pack, graph, run_file, taxon_file, region_file, purpose_file),
        run_file: _vault_run_note(pack, taxon_file, region_file, purpose_file, claim_nodes, action_nodes),
        taxon_file: _vault_simple_note(
            "taxon",
            summary.get("accepted_name") or summary["taxon"],
            {"taxonKey": summary.get("taxonKey"), "match_confidence": summary.get("match_confidence")},
            [("Current run", f"../{run_file}")],
            [f"Accepted name: {summary.get('accepted_name') or summary['taxon']}"],
        ),
        region_file: _vault_simple_note(
            "region",
            summary["region_name"],
            {"bbox": summary.get("bbox")},
            [("Current run", f"../{run_file}")],
            [f"BBox: `{summary.get('bbox')}`"],
        ),
        purpose_file: _vault_simple_note(
            "purpose",
            readiness["purpose_label"],
            {"purpose": readiness["purpose"], "score": readiness["score"]},
            [("Current run", f"../{run_file}")],
            [readiness.get("interpretation", "")],
        ),
        "methods/gbif-citation-checklist.md": _vault_methods_note(pack),
    }
    for dataset in pack["dataset_contributions"]:
        path = f"datasets/{_slug(dataset['datasetKey'])}.md"
        files[path] = _vault_dataset_note(dataset, run_file, pack["publisher_feedback"])
    for feedback in pack["publisher_feedback"]:
        path = f"issues/{_slug(feedback['main_issue'])}.md"
        files.setdefault(path, _vault_issue_note(feedback["main_issue"], run_file, pack["publisher_feedback"]))
    for claim_id, status, claim in claim_nodes:
        path = f"claims/{_slug(claim_id.split(':', 1)[1])}.md"
        files[path] = _vault_claim_note(status, claim, run_file)
    for action_id, action in action_nodes:
        path = f"actions/{_slug(action_id.split(':', 1)[1])}.md"
        files[path] = _vault_action_note(action, run_file)
    return files


def _vault_index(
    pack: dict[str, Any],
    graph: dict[str, Any],
    run_file: str,
    taxon_file: str,
    region_file: str,
    purpose_file: str,
) -> str:
    summary = pack["passport"]
    readiness = pack["evidence_readiness"]
    lines = [
        _frontmatter(
            {
                "type": "vault_index",
                "run_id": pack["run"]["run_id"],
                "taxon": summary["taxon"],
                "region": summary["region_name"],
                "purpose": readiness["purpose"],
            }
        ),
        "# EcoGenesis Evidence Vault",
        "",
        "This vault is a human-readable memory layer for the Evidence Passport.",
        "",
        "## Core Links",
        "",
        f"- Run: {_md_link(pack['run']['run_id'], run_file)}",
        f"- Taxon: {_md_link(summary.get('accepted_name') or summary['taxon'], taxon_file)}",
        f"- Region: {_md_link(summary['region_name'], region_file)}",
        f"- Purpose: {_md_link(readiness['purpose_label'], purpose_file)}",
        "",
        "## Graph Summary",
        "",
    ]
    for key, value in graph["node_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Review Files",
            "",
            "- `../passport.html`",
            "- `../decision_memo.md`",
            "- `../submission_readiness.md`",
            "- `../validation_summary.md`",
            "- `../citations.md`",
            "- `../publisher_feedback.md`",
            "- `../run.json`",
        ]
    )
    return "\n".join(lines) + "\n"


def _vault_run_note(
    pack: dict[str, Any],
    taxon_file: str,
    region_file: str,
    purpose_file: str,
    claim_nodes: list[tuple[str, str, str]],
    action_nodes: list[tuple[str, str]],
) -> str:
    summary = pack["passport"]
    readiness = pack["evidence_readiness"]
    lines = [
        _frontmatter(
            {
                "type": "run",
                "run_id": pack["run"]["run_id"],
                "taxon": summary["taxon"],
                "region": summary["region_name"],
                "purpose": readiness["purpose"],
                "score": readiness["score"],
                "records_used": summary["records_used"],
                "datasets_used": summary["datasets_used"],
            }
        ),
        f"# Run: {summary['taxon']} - {summary['region_name']} - {readiness['purpose_label']}",
        "",
        f"Taxon: {_md_link(summary.get('accepted_name') or summary['taxon'], '../' + taxon_file)}",
        f"Region: {_md_link(summary['region_name'], '../' + region_file)}",
        f"Purpose: {_md_link(readiness['purpose_label'], '../' + purpose_file)}",
        "",
        "## Decision Memo",
        "",
        f"- Verdict: {pack['decision_memo']['verdict']}",
        f"- Question: {pack['decision_memo']['question']}",
        f"- Next action: {pack['decision_memo']['recommended_next_action']}",
        "",
        "## Readiness",
        "",
        f"- Score: {readiness['score']}/100",
        f"- Interpretation: {readiness.get('interpretation', '')}",
        "",
        "## Datasets",
        "",
    ]
    for dataset in pack["dataset_contributions"]:
        lines.append(f"- {_md_link(dataset['datasetKey'], '../datasets/' + _slug(dataset['datasetKey']) + '.md')} ({dataset['record_count']} records)")
    lines.extend(["", "## Claims", ""])
    for claim_id, status, claim in claim_nodes:
        lines.append(f"- {status}: {_md_link(claim, '../claims/' + _slug(claim_id.split(':', 1)[1]) + '.md')}")
    lines.extend(["", "## Actions", ""])
    for action_id, action in action_nodes:
        lines.append(f"- {_md_link(action, '../actions/' + _slug(action_id.split(':', 1)[1]) + '.md')}")
    return "\n".join(lines) + "\n"


def _vault_dataset_note(dataset: dict[str, Any], run_file: str, feedback_rows: list[dict[str, Any]]) -> str:
    related_feedback = [row for row in feedback_rows if row["datasetKey"] == dataset["datasetKey"]]
    lines = [
        _frontmatter(
            {
                "type": "dataset",
                "datasetKey": dataset["datasetKey"],
                "publisher": dataset.get("publisher"),
                "license": dataset.get("license"),
                "record_count": dataset.get("record_count"),
            }
        ),
        f"# Dataset: {dataset['datasetKey']}",
        "",
        f"Current run: {_md_link('run', '../' + run_file)}",
        "",
        "## Contribution",
        "",
        f"- Records used: {dataset.get('record_count')}",
        f"- License: {dataset.get('license') or 'unknown'}",
        f"- Main issues: {dataset.get('main_issues') or 'none_detected'}",
        "",
        "## Publisher Feedback",
        "",
    ]
    if related_feedback:
        for row in related_feedback:
            lines.append(f"- P{row.get('fix_priority')} {row.get('severity')}: {row['main_issue']} - {row['suggested_fix']}")
    else:
        lines.append("- No publisher feedback rows generated for this dataset.")
    return "\n".join(lines) + "\n"


def _vault_issue_note(issue: str, run_file: str, feedback_rows: list[dict[str, Any]]) -> str:
    related = [row for row in feedback_rows if row["main_issue"] == issue]
    lines = [
        _frontmatter({"type": "issue", "issue": issue, "affected_datasets": len({row["datasetKey"] for row in related})}),
        f"# Issue: {issue}",
        "",
        f"Current run: {_md_link('run', '../' + run_file)}",
        "",
        "## Affected Datasets",
        "",
    ]
    for row in related:
        lines.append(f"- {_md_link(row['datasetKey'], '../datasets/' + _slug(row['datasetKey']) + '.md')}: {row['records_affected']} records, {row.get('severity')} severity")
    return "\n".join(lines) + "\n"


def _vault_claim_note(status: str, claim: str, run_file: str) -> str:
    return "\n".join(
        [
            _frontmatter({"type": "claim", "status": status}),
            f"# Claim: {claim}",
            "",
            f"Status: **{status}**",
            f"Current run: {_md_link('run', '../' + run_file)}",
            "",
            "This claim is stored as graph memory so future runs can reuse or challenge it.",
        ]
    ) + "\n"


def _vault_action_note(action: str, run_file: str) -> str:
    return "\n".join(
        [
            _frontmatter({"type": "action"}),
            f"# Action: {action}",
            "",
            f"Current run: {_md_link('run', '../' + run_file)}",
            "",
            "Use this action as a review or follow-up task for the evidence workflow.",
        ]
    ) + "\n"


def _vault_methods_note(pack: dict[str, Any]) -> str:
    citation = pack["citation_autopilot"]
    lines = [
        _frontmatter({"type": "method", "topic": "gbif_citation_checklist"}),
        "# GBIF Citation Checklist",
        "",
        citation["gbif_download_warning"],
        "",
        "## Checklist",
        "",
    ]
    for item in citation["doi_completion_flow"]:
        marker = "x" if item["ready"] else " "
        lines.append(f"- [{marker}] {item['label']}: {item['action']}")
    lines.extend(["", "## Methods Text", "", citation["methods_text"], "", "## Journal Methods Text", "", citation["journal_methods_text"]])
    return "\n".join(lines) + "\n"


def _vault_simple_note(
    note_type: str,
    title: str,
    metadata: dict[str, Any],
    links: list[tuple[str, str]],
    body_lines: list[str],
) -> str:
    lines = [_frontmatter({"type": note_type, "title": title, **metadata}), f"# {title}", ""]
    if links:
        lines.extend(["## Links", ""])
        for label, target in links:
            lines.append(f"- {_md_link(label, target)}")
        lines.append("")
    lines.extend(["## Notes", ""])
    lines.extend(f"- {line}" for line in body_lines if line)
    return "\n".join(lines) + "\n"


def _frontmatter(values: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in values.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def _md_link(label: Any, target: str) -> str:
    return f"[{str(label).replace('[', '(').replace(']', ')')}]({target})"


def _slug(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    text = re.sub(r"[^a-z0-9а-яё]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "unknown"
