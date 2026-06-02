from __future__ import annotations

import csv
import html
import io
import json
from typing import Any


def build_barcode_artifacts(pack: dict[str, Any]) -> dict[str, str]:
    return {
        "evidence_pack.json": json.dumps(pack, indent=2, ensure_ascii=False),
        "run.json": json.dumps(pack["run"], indent=2, ensure_ascii=False),
        "reference_manifest.json": json.dumps(pack["reference_manifest"], indent=2, ensure_ascii=False),
        "sequence_safety_table.csv": sequence_safety_csv(pack),
        "safe_taxonomic_assignments.csv": safe_assignments_csv(pack),
        "review_taxonomic_hints.csv": review_hints_csv(pack),
        "ambiguous_sequences.csv": filtered_sequences_csv(pack, {"ambiguous", "genus-safe", "higher-rank-safe"}),
        "barcode_gap_report.csv": barcode_gap_csv(pack),
        "diagnostic_kmer_report.csv": diagnostic_kmer_csv(pack),
        "gbif_backbone_matches.csv": gbif_matches_csv(pack),
        "publication_blockers.csv": blockers_csv(pack),
        "repair_plan.csv": table_csv(pack.get("repair_plan", [])),
        "metadata_bottlenecks.csv": table_csv(pack.get("metadata_bottlenecks", [])),
        "reference_gap_index.csv": table_csv(pack.get("reference_gap_index", [])),
        "hard_gate_audit.csv": table_csv(pack.get("hard_gate_audit", [])),
        "naive_top_hit_overclaims.csv": table_csv(pack.get("naive_top_hit_overclaims", [])),
        "dwc_occurrence_core_template.csv": occurrence_core_csv(pack, publishable_only=False),
        "dwc_occurrence_core_publishable.csv": occurrence_core_csv(pack, publishable_only=True),
        "dwc_occurrence_core_gbif_ready.csv": occurrence_core_csv(pack, publishable_only=True),
        "dwc_occurrence_core_review.csv": occurrence_core_csv(pack, publishable_only=False),
        "dwc_occurrence_core_review_or_repair.csv": occurrence_review_or_repair_csv(pack),
        "dna_derived_extension_template.csv": dna_extension_csv(pack, publishable_only=False),
        "dna_derived_extension_publishable.csv": dna_extension_csv(pack, publishable_only=True),
        "dna_derived_extension_gbif_ready.csv": dna_extension_csv(pack, publishable_only=True),
        "molecular_evidence_report.html": molecular_report_html(pack),
        "methods_text.md": methods_text_md(pack),
        "citations.md": citations_md(pack),
        "evidence_graph.json": json.dumps(pack["evidence_graph"], indent=2, ensure_ascii=False),
        "nexus_v3_summary.json": json.dumps(pack["nexus_v3"], indent=2, ensure_ascii=False),
        "external_tool_adapter_matrix.csv": external_tool_adapter_matrix_csv(),
        "proof_by_failure_modes.md": proof_by_failure_modes_md(pack),
    }


def sequence_safety_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        top = record["top_hit"] or {}
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "decisionClass": record["decision_class"],
                "taxonomicStatus": record["taxonomic_status"],
                "publicationStatus": record["publication_status"],
                "publicationStage": record["publication_stage"],
                "candidateTaxon": record["candidate_taxon"]["name"],
                "candidateRank": record["candidate_taxon"]["rank"],
                "publishedTaxon": record["published_taxon"]["name"],
                "publishedRank": record["published_taxon"]["rank"],
                "matchType": record["match_type"],
                "topHit": top.get("taxon"),
                "identity": top.get("identity"),
                "queryCoverage": top.get("query_coverage"),
                "barcodeGap": record["barcode_gap"].get("gap"),
                "diagnosticKmerSupport": record["diagnostic_kmers"].get("support_count"),
                "diagnosticPFalsePositive": record["diagnostic_kmers"].get("p_false_positive"),
                "blockers": "; ".join(record["blockers"]),
            }
        )
    return write_csv(rows)


def safe_assignments_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        if record["decision_class"] not in {"species-safe", "genus-safe", "higher-rank-safe"}:
            continue
        if record["published_taxon"]["rank"] == "none":
            continue
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "acceptedScientificName": record["published_taxon"]["name"],
                "taxonRank": record["published_taxon"]["rank"],
                "decisionClass": record["decision_class"],
                "basis": "deterministic identity/coverage, ambiguity LCA, barcode gap, diagnostic k-mer and GBIF metadata gates",
            }
        )
    return write_csv(rows)


def review_hints_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        if record["published_taxon"]["rank"] != "none":
            continue
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "decisionClass": record["decision_class"],
                "candidateTaxon": record["candidate_taxon"]["name"],
                "candidateRank": record["candidate_taxon"]["rank"],
                "publicationStage": record["publication_stage"],
                "reviewReason": "; ".join(record["blockers"]),
            }
        )
    return write_csv(rows)


def filtered_sequences_csv(pack: dict[str, Any], statuses: set[str]) -> str:
    rows = [
        {
            "sequenceID": record["sequence_id"],
            "taxonomicStatus": record["taxonomic_status"],
            "decisionClass": record["decision_class"],
            "candidateTaxon": record["candidate_taxon"]["name"],
            "candidateRank": record["candidate_taxon"]["rank"],
            "publishedTaxon": record["published_taxon"]["name"],
            "publishedRank": record["published_taxon"]["rank"],
            "indistinguishableHits": "; ".join(hit["taxon"] for hit in record["indistinguishable_hits"]),
            "blockers": "; ".join(record["blockers"]),
        }
        for record in pack["records"]
        if record["taxonomic_status"] in statuses
    ]
    return write_csv(rows)


def barcode_gap_csv(pack: dict[str, Any]) -> str:
    return write_csv(
        [
            {
                "sequenceID": record["sequence_id"],
                "status": record["barcode_gap"]["status"],
                "intraMaxDistance": record["barcode_gap"].get("intra_max_distance"),
                "interMinDistance": record["barcode_gap"].get("inter_min_distance"),
                "barcodeGap": record["barcode_gap"].get("gap"),
            }
            for record in pack["records"]
        ]
    )


def diagnostic_kmer_csv(pack: dict[str, Any]) -> str:
    return write_csv(
        [
            {
                "sequenceID": record["sequence_id"],
                "status": record["diagnostic_kmers"]["status"],
                "k": record["diagnostic_kmers"].get("k"),
                "queryWindowCount": record["diagnostic_kmers"].get("query_window_count"),
                "diagnosticKmerCount": record["diagnostic_kmers"].get("diagnostic_kmer_count"),
                "supportCount": record["diagnostic_kmers"].get("support_count"),
                "supportRate": record["diagnostic_kmers"].get("support_rate"),
                "expectedRandomHits": record["diagnostic_kmers"].get("expected_random_hits"),
                "pFalsePositive": record["diagnostic_kmers"].get("p_false_positive"),
                "alpha": record["diagnostic_kmers"].get("alpha"),
            }
            for record in pack["records"]
        ]
    )


def gbif_matches_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        for hit in record["hits"]:
            rows.append(
                {
                    "sequenceID": record["sequence_id"],
                    "taxon": hit["taxon"],
                    "rank": hit["rank"],
                    "gbifTaxonKey": hit.get("gbif_taxon_key"),
                    "identity": hit["identity"],
                    "queryCoverage": hit["query_coverage"],
                    "referenceDatabase": hit.get("reference_database"),
                    "referenceID": hit.get("reference_id"),
                }
            )
    return write_csv(rows)


def blockers_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        for blocker in record["blockers"]:
            rows.append({"sequenceID": record["sequence_id"], "blocker": blocker})
    return write_csv(rows)


def table_csv(rows: list[dict[str, Any]]) -> str:
    return write_csv(rows)


def occurrence_core_csv(pack: dict[str, Any], *, publishable_only: bool) -> str:
    rows = []
    for record in pack["records"]:
        if publishable_only and record["published_taxon"]["rank"] == "none":
            continue
        metadata = record["metadata"]
        taxon = record["published_taxon"]
        rows.append(
            {
                "occurrenceID": metadata.get("occurrenceID"),
                "basisOfRecord": metadata.get("basisOfRecord") or "MaterialSample",
                "scientificName": "" if taxon["rank"] == "none" else taxon["name"],
                "taxonRank": "" if taxon["rank"] == "none" else taxon["rank"],
                "eventDate": metadata.get("eventDate"),
                "countryCode": metadata.get("countryCode"),
                "decimalLatitude": metadata.get("decimalLatitude"),
                "decimalLongitude": metadata.get("decimalLongitude"),
                "geodeticDatum": metadata.get("geodeticDatum"),
                "coordinateUncertaintyInMeters": metadata.get("coordinateUncertaintyInMeters"),
                "verbatimIdentification": record["candidate_taxon"]["name"],
                "candidateTaxonRank": record["candidate_taxon"]["rank"],
                "publicationStage": record["publication_stage"],
                "identificationRemarks": identification_remarks(record, pack),
            }
        )
    return write_csv(rows)


def occurrence_review_or_repair_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        if record["published_taxon"]["rank"] != "none":
            continue
        metadata = record["metadata"]
        rows.append(
            {
                "occurrenceID": metadata.get("occurrenceID"),
                "basisOfRecord": metadata.get("basisOfRecord") or "MaterialSample",
                "verbatimIdentification": record["candidate_taxon"]["name"],
                "candidateTaxonRank": record["candidate_taxon"]["rank"],
                "decisionClass": record["decision_class"],
                "publicationStage": record["publication_stage"],
                "blockers": "; ".join(record["blockers"]),
                "repairActions": "; ".join(record["actions"]),
            }
        )
    return write_csv(rows)


def dna_extension_csv(pack: dict[str, Any], *, publishable_only: bool) -> str:
    rows = []
    for record in pack["records"]:
        if publishable_only and record["published_taxon"]["rank"] == "none":
            continue
        metadata = record["metadata"]
        top = record["top_hit"] or {}
        rows.append(
            {
                "occurrenceID": metadata.get("occurrenceID"),
                "sequenceID": record["sequence_id"],
                "DNA_sequence_md5": record["sequence_md5"],
                "target_gene": metadata.get("marker"),
                "otu_db": metadata.get("referenceDatabase"),
                "otu_class_appr": metadata.get("methodOrSOP"),
                "otu_seq_comp_appr": f"identity={top.get('identity')}; queryCoverage={top.get('query_coverage')}",
                "identificationReferences": "https://www.gbif.org/tools/sequence-id",
                "identificationRemarks": identification_remarks(record, pack),
            }
        )
    return write_csv(rows)


def identification_remarks(record: dict[str, Any], pack: dict[str, Any]) -> str:
    top = record["top_hit"] or {}
    return (
        f"{record['decision_class']} by {pack['run']['ruleset_version']}; "
        f"match={record['match_type']}; top={top.get('taxon')} "
        f"identity={top.get('identity')} coverage={top.get('query_coverage')}; "
        f"candidate rank={record['candidate_taxon']['rank']}; "
        f"published rank={record['published_taxon']['rank']}; "
        f"publication stage={record['publication_stage']}."
    )


def molecular_report_html(pack: dict[str, Any]) -> str:
    nexus = pack.get("nexus_v3", {})
    conversion = nexus.get("conversion_metrics", {})
    repair_rows = "\n".join(
        f"<tr><td>{html.escape(row['repairAction'])}</td><td>{row['unlockableRecords']}</td><td>{html.escape(row['estimatedCost'])}</td><td>{html.escape(row['exampleRecords'])}</td></tr>"
        for row in pack.get("repair_plan", [])[:8]
    )
    overclaim_rows = "\n".join(
        f"<tr><td>{html.escape(row['sequenceID'])}</td><td>{html.escape(str(row['naiveClaim']))}</td><td>{html.escape(row['compilerDecision'])}</td><td>{html.escape(row['safeRank'])} {html.escape(row['safeTaxon'])}</td></tr>"
        for row in pack.get("naive_top_hit_overclaims", [])[:8]
    )
    hard_gate_failures = pack["metrics"].get("hard_gate_failures", 0)
    rows = "\n".join(
        f"<tr><td>{html.escape(record['sequence_id'])}</td><td>{html.escape(record['decision_class'])}</td>"
        f"<td>{html.escape(record['candidate_taxon']['name'])}</td><td>{html.escape(record['candidate_taxon']['rank'])}</td>"
        f"<td>{html.escape(record['published_taxon']['name'])}</td><td>{html.escape(record['published_taxon']['rank'])}</td>"
        f"<td>{html.escape(record['publication_stage'])}</td>"
        f"<td>{html.escape('; '.join(record['blockers']) or 'none')}</td></tr>"
        for record in pack["records"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <link rel="icon" href="data:," />
  <title>{html.escape(pack['summary']['title'])}</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 32px; color: #17201a; }}
    h1 {{ max-width: 880px; }}
    .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 24px 0; }}
    .nexus {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin: 24px 0; }}
    .card {{ border: 1px solid #d7e2dc; border-radius: 8px; padding: 14px; background: #f8fbf8; }}
    .ok {{ background:#ecf8ef; border-color:#b7dac0; }}
    .warn {{ background:#fff8e8; border-color:#e6c776; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d7e2dc; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef5ef; }}
  </style>
</head>
<body>
  <p><strong>EcoGenesis</strong> / GBIF Ebbe Nielsen Challenge 2026</p>
  <h1>{html.escape(pack['summary']['project_title'])}</h1>
  <p>{html.escape(pack['summary']['verdict'])}</p>
  <section class="summary">
    <div class="card"><strong>{pack['metrics']['processed_records']}</strong><br />processed</div>
    <div class="card"><strong>{pack['metrics']['species_safe_records']}</strong><br />species-safe</div>
    <div class="card"><strong>{pack['metrics']['blocked_species_claims']}</strong><br />blocked species claims</div>
    <div class="card"><strong>{pack['metrics']['publication_repair_efficiency']}</strong><br />repair explainability</div>
  </section>
  <h2>Nexus V3 conversion audit</h2>
  <section class="nexus">
    <div class="card"><strong>{conversion.get('MECY_molecular_evidence_conversion_yield', 0)}</strong><br />MECY conversion yield</div>
    <div class="card"><strong>{conversion.get('SRY_safe_rank_yield', 0)}</strong><br />safe-rank yield</div>
    <div class="card"><strong>{conversion.get('OPR_overclaim_prevention_rate', 0)}</strong><br />overclaim prevention</div>
    <div class="card"><strong>{conversion.get('RY_repairable_yield', 0)}</strong><br />repairable yield</div>
    <div class="card {'ok' if hard_gate_failures == 0 else 'warn'}"><strong>{hard_gate_failures}</strong><br />hard-gate failures</div>
  </section>
  <h2>Top repair actions</h2>
  <table>
    <thead><tr><th>Repair action</th><th>Unlockable records</th><th>Cost</th><th>Examples</th></tr></thead>
    <tbody>{repair_rows or '<tr><td colspan="4">No repair actions required.</td></tr>'}</tbody>
  </table>
  <h2>Naive top-hit overclaims prevented</h2>
  <table>
    <thead><tr><th>Sequence</th><th>Naive species claim</th><th>Compiler decision</th><th>Safe taxon</th></tr></thead>
    <tbody>{overclaim_rows or '<tr><td colspan="4">No unsafe top-hit species claims found in this run.</td></tr>'}</tbody>
  </table>
  <h2>Sequence decisions</h2>
  <table>
    <thead><tr><th>Sequence</th><th>Decision</th><th>Candidate taxon</th><th>Candidate rank</th><th>Published taxon</th><th>Published rank</th><th>Publication stage</th><th>Blockers</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""


def methods_text_md(pack: dict[str, Any]) -> str:
    return f"""# Methods

This run used **EcoGenesis Nexus V3 / Barcode-to-GBIF Evidence Compiler** ruleset `{pack['run']['ruleset_version']}`.

## Purpose

The workflow converts DNA barcode, metabarcoding or Sequence ID / BLAST-style results into rank-aware molecular occurrence evidence for GBIF-oriented review. It is a downstream evidence compiler, not a replacement for GBIF Sequence ID, BOLD, UNITE, PR2, GTDB, BLAST+ or VSEARCH.

## Input Evidence

For each DNA sequence, the compiler consumed:

- sequence identifier and nucleotide sequence;
- reference-hit metrics: taxon, rank, lineage, percent identity, query coverage, aligned length, bit score and e-value when supplied;
- barcode-gap evidence: maximum within-taxon distance and minimum outside-taxon distance;
- diagnostic k-mer evidence and false-positive threshold;
- Darwin Core Occurrence metadata and DNA-derived workflow metadata.

Reference context: **{pack['summary']['reference_database']}**. Marker: **{pack['summary']['marker']}**.

## Deterministic Gates

For each DNA barcode/metabarcoding sequence, the compiler evaluated percent identity, query coverage, a 95% ambiguity test over mismatch-rate standard errors, lowest common ancestor of indistinguishable hits, barcode gap, diagnostic k-mer support, diagnostic false-positive probability and GBIF publication metadata readiness.

Species-level output is fail-closed: a sequence is `species-safe` only when the exact match gate, ambiguity/LCA gate, positive barcode gap gate, diagnostic k-mer gate and publication-readiness gates all pass.

The pack separates `candidate_taxon` from `published_taxon`: blocked or weak records can remain useful as review hints, but they are not emitted as publishable Darwin Core species records.

## Naive Top-Hit Comparison

The `naive_top_hit_overclaims.csv` export lists records where a naive workflow would have published the top hit as a species, but EcoGenesis blocked, downgraded or moved the record to review. This is the core overclaim-prevention audit.

## Repair Optimization

The `repair_plan.csv` export ranks repair actions by unlockable record count. Metadata repairs are separated from molecular/reference blockers so publishers can see whether records need field repair, reference curation or new laboratory work.

Nexus V3 audit files in this Evidence Pack add:

- `hard_gate_audit.csv` for species-safe consistency checks;
- `naive_top_hit_overclaims.csv` for overclaim prevention evidence;
- `reference_gap_index.csv` for marker/reference bottlenecks;
- `repair_plan.csv` for publisher repair prioritization;
- `metadata_bottlenecks.csv` for field-level publication blockers.

## Claim Boundaries

The output is sequence-derived occurrence evidence under supplied reference context. It does not prove living presence, absence, population trend, true distribution, phenotype truth or ecological causality. Empty or low-evidence cells must be treated as no-evidence cells, not absence.
"""


def citations_md(pack: dict[str, Any]) -> str:
    manifest = pack.get("reference_manifest", {})
    return f"""# Citations And Source Links

## Project And Tool Citation

EcoGenesis Nexus V3 / Barcode-to-GBIF Evidence Compiler. Ruleset `{pack['run']['ruleset_version']}`. Run ID `{pack['run']['run_id']}`. Request fingerprint `{pack['run']['request_fingerprint']}`.

## Reference Dataset Used In This Run

- Database: {manifest.get('db_name') or pack['summary']['reference_database']}
- Version: {manifest.get('db_version') or 'not supplied'}
- Source: {manifest.get('source') or 'not supplied'}
- DOI or URL: {manifest.get('doi_or_url') or 'not supplied'}
- License: {manifest.get('license') or 'not supplied'}
- SHA-256: {manifest.get('sha256') or manifest.get('manifest_sha256') or 'not supplied'}

## GBIF And Methods Links

- GBIF Sequence ID: https://www.gbif.org/tools/sequence-id
- GBIF DNA-derived data publishing guide: https://docs.gbif.org/publishing-dna-derived-data/en/
- GBIF occurrence dataset quality requirements: https://www.gbif.org/data-quality-requirements-occurrences
- GBIF 2026 Ebbe Nielsen Challenge rules: https://www.gbif.org/awards/ebbe-2026-rules

Retain reference database names, versions, sequence identifiers and GBIF taxon keys when publishing or reviewing derived molecular occurrence evidence.

## DOI Caveat For Formal GBIF Use

API-derived evidence packs and local reference-search examples are useful for review and reproducibility, but formal GBIF-mediated occurrence publication should attach an appropriate GBIF download DOI, derived dataset citation or source reference dataset DOI where applicable.
"""


def proof_by_failure_modes_md(pack: dict[str, Any]) -> str:
    return """# Proof By Failure Modes

The compiler blocks species-level claims when any required gate fails:

- identity below 99% or coverage below 80%;
- statistically indistinguishable competitor collapses the safe taxon to genus or higher;
- barcode gap is missing or non-positive;
- diagnostic k-mer support is missing, zero or above the configured false-positive probability threshold;
- required Occurrence core or DNA-derived metadata is missing.

Therefore `species-safe` is not a blind top-hit label. It means the record passed all frozen molecular evidence and GBIF-readiness gates in this run.

## Nexus V3 Hard-Gate Audit

The `hard_gate_audit.csv` export verifies the contradiction condition explicitly:

If a record is emitted as `species-safe`, then the exact match gate, ambiguity/LCA gate, barcode gap gate, diagnostic k-mer gate, Occurrence core gate and DNA metadata gate must all pass.

If any of those gates fail while `species-safe` is emitted, `hardGateViolation=true`. A valid run must have zero hard-gate failures.
"""


def external_tool_adapter_matrix_csv() -> str:
    return write_csv(
        [
            {
                "tool": "GBIF Sequence ID",
                "role": "Reference-hit source",
                "normalizedFields": "sequenceID; topTaxon; identity; queryCoverage; matchType; GBIF backbone taxon",
                "claimPolicy": "Never publish top hit directly; pass through Nexus hard gates.",
            },
            {
                "tool": "BLAST+",
                "role": "Alignment and candidate hits",
                "normalizedFields": "pident; qcov; bitscore; evalue; alignedLength; subjectID",
                "claimPolicy": "Use as supplied H(s); species claim still requires ambiguity/LCA and reference support.",
            },
            {
                "tool": "VSEARCH / DADA2 / QIIME 2",
                "role": "ASV and metabarcoding upstream pipeline",
                "normalizedFields": "ASV id; sequence; taxonomy; confidence; read/count context",
                "claimPolicy": "Add assay evidence gates before ecological or monitoring claims.",
            },
            {
                "tool": "BOLD / UNITE / PR2 / GTDB",
                "role": "Reference database context",
                "normalizedFields": "database name; version; marker; reference taxon; lineage",
                "claimPolicy": "Report reference gaps and reference completeness caveats.",
            },
            {
                "tool": "MAFFT + IQ-TREE / EPA-ng",
                "role": "Optional phylogenetic placement",
                "normalizedFields": "placement; support; clade; tree version",
                "claimPolicy": "Can support or caveat safe rank; does not override failed metadata gates.",
            },
            {
                "tool": "Cutadapt / fastp",
                "role": "Sequence QC and trimming",
                "normalizedFields": "trimmed length; quality; primer status; ambiguous bases",
                "claimPolicy": "Feeds QC blockers and repair actions.",
            },
        ]
    )


def write_csv(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    if not rows:
        return ""
    fields = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()
