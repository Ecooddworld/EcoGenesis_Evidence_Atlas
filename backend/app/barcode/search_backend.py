from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import os
import re
from pathlib import Path
from typing import Any

import requests

from .schemas import BarcodeCompilerRequest, BarcodeGapEvidence, DiagnosticKmerEvidence, ReferenceHit, SequenceRecord, TaxonLineageItem


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REFERENCE_ID = "aedes_coi_mini"
DNA_ALPHABET = set("ACGTRYSWKMBDHVN")
GBIF_LINEAGE_RANKS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]


@dataclass(frozen=True)
class ReferenceEntry:
    reference_id: str
    sequence: str
    taxon: str
    rank: str
    gbif_taxon_key: int | None
    lineage: list[dict[str, Any]]


def search_status() -> dict[str, Any]:
    vsearch_path = shutil.which("vsearch")
    blastn_path = shutil.which("blastn")
    return {
        "status": "ready" if vsearch_path or blastn_path else "degraded",
        "preferred_backend": "vsearch" if vsearch_path else "blastn" if blastn_path else "python-local",
        "available_backends": {
            "vsearch": bool(vsearch_path),
            "blastn": bool(blastn_path),
            "python-local": True,
        },
        "binaries": {
            "vsearch": vsearch_path,
            "blastn": blastn_path,
        },
        "message": (
            "External reference search is available."
            if vsearch_path or blastn_path
            else "External VSEARCH/BLAST+ binary was not found; deterministic local mini-search is available for tests and demos."
        ),
        "reference_root": str(bundled_reference_root()),
        "user_reference_root": str(user_reference_root()),
    }


def list_reference_datasets() -> list[dict[str, Any]]:
    datasets = []
    seen = set()
    for root, source_type in reference_roots():
        if not root.exists():
            continue
        for manifest_path in sorted(root.glob("*/manifest.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["id"] in seen:
                continue
            seen.add(manifest["id"])
            fasta_path = manifest_path.parent / manifest["fasta"]
            datasets.append(
                {
                    "id": manifest["id"],
                    "title": manifest["title"],
                    "marker": manifest.get("marker"),
                    "source": manifest.get("source"),
                    "source_type": source_type,
                    "license": manifest.get("license"),
                    "doi_or_url": manifest.get("doi_or_url"),
                    "usage_scope": manifest.get("usage_scope"),
                    "accessed_at": manifest.get("accessed_at"),
                    "gbif_backbone_enrichment": manifest.get("gbif_backbone_enrichment"),
                    "example_queries": manifest.get("example_queries", []),
                    "fasta": str(fasta_path),
                    "records": len(manifest.get("references", {})),
                    "sha256": sha256_file(fasta_path) if fasta_path.exists() else None,
                }
            )
    return datasets


def create_user_reference_dataset(
    *,
    fasta_text: str,
    dataset_id: str | None = None,
    title: str | None = None,
    marker: str | None = None,
    source: str | None = None,
    license: str | None = None,
    doi_or_url: str | None = None,
) -> dict[str, Any]:
    parsed = parse_fasta_text(fasta_text)
    if not parsed:
        raise ValueError("FASTA file does not contain any reference sequences.")

    digest = hashlib.sha256(fasta_text.encode("utf-8")).hexdigest()
    safe_id = unique_user_dataset_id(dataset_id or title or f"uploaded_reference_{digest[:10]}")
    dataset_title = title or f"Uploaded reference dataset {safe_id}"
    directory = user_reference_root() / safe_id
    directory.mkdir(parents=True, exist_ok=False)
    fasta_name = f"{safe_id}.fasta"
    normalized_fasta = []
    references: dict[str, dict[str, Any]] = {}
    sequences_by_taxon: dict[str, list[str]] = {}
    total_windows = 0
    enrichment_summary = {
        "status": "disabled" if not gbif_backbone_enrichment_enabled() else "attempted",
        "base_url": gbif_base_url(),
        "enriched_records": 0,
        "fallback_records": 0,
        "warnings": [],
    }
    for header, sequence in parsed:
        reference_id, taxon, rank, gbif_taxon_key = parse_reference_header(header)
        normalized = normalize_sequence(sequence)
        enrichment = uploaded_reference_taxon_context(taxon=taxon, rank=rank, gbif_taxon_key=gbif_taxon_key)
        canonical_taxon = enrichment["taxon"]
        normalized_fasta.append(f">{reference_id} {canonical_taxon}\n{normalized}\n")
        sequences_by_taxon.setdefault(canonical_taxon, []).append(normalized)
        references[reference_id] = {
            "taxon": canonical_taxon,
            "rank": enrichment["rank"],
            "gbif_taxon_key": enrichment["gbif_taxon_key"],
            "lineage": enrichment["lineage"],
            "gbif_backbone_match": enrichment["match"],
        }
        if enrichment["match"]["status"] == "enriched":
            enrichment_summary["enriched_records"] += 1
        else:
            enrichment_summary["fallback_records"] += 1
            if enrichment["match"].get("message"):
                enrichment_summary["warnings"].append(f"{reference_id}: {enrichment['match']['message']}")
        total_windows += max(len(normalized) - 14, 1)

    (directory / fasta_name).write_text("".join(normalized_fasta), encoding="utf-8")
    barcode_gap_by_taxon, diagnostic_kmers_by_taxon = reference_evidence_from_sequences(sequences_by_taxon)
    diagnostic_kmer_k = next(
        (len(items[0]) for items in diagnostic_kmers_by_taxon.values() if items),
        None,
    )
    manifest = {
        "id": safe_id,
        "title": dataset_title,
        "version": datetime.now(timezone.utc).date().isoformat(),
        "marker": marker or "COI-5P",
        "fasta": fasta_name,
        "source": source or "user_uploaded_reference_fasta",
        "doi_or_url": doi_or_url,
        "license": license or "user_supplied_license_not_declared",
        "reference_total_windows": total_windows,
        "references": references,
        "barcode_gap_by_taxon": barcode_gap_by_taxon,
        "diagnostic_kmers_by_taxon": diagnostic_kmers_by_taxon,
        "diagnostic_kmer_k": diagnostic_kmer_k,
        "gbif_backbone_enrichment": enrichment_summary,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sha256": sha256_file(directory / fasta_name),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return next(dataset for dataset in list_reference_datasets() if dataset["id"] == safe_id)


def search_reference(
    *,
    sequence: str,
    sequence_id: str = "query-sequence",
    reference_dataset: str = DEFAULT_REFERENCE_ID,
    backend: str = "auto",
    max_hits: int = 5,
) -> dict[str, Any]:
    clean_sequence = normalize_sequence(sequence)
    manifest, fasta_path, entries = load_reference_dataset(reference_dataset)
    if not entries:
        raise ValueError(f"Reference dataset {reference_dataset!r} has no entries.")

    selected_backend = resolve_backend(backend)
    if selected_backend == "vsearch":
        raw_hits = run_vsearch(clean_sequence, sequence_id, fasta_path, max_hits=max_hits)
    elif selected_backend == "blastn":
        raw_hits = run_blastn(clean_sequence, sequence_id, fasta_path, max_hits=max_hits)
    else:
        raw_hits = run_python_local_search(clean_sequence, entries, max_hits=max_hits)

    entry_by_id = {entry.reference_id: entry for entry in entries}
    hits = []
    for raw in raw_hits:
        entry = entry_by_id.get(raw["reference_id"])
        if not entry:
            continue
        alignment = best_ungapped_alignment(clean_sequence, entry.sequence)
        hits.append(
            {
                "taxon": entry.taxon,
                "rank": entry.rank,
                "identity": round(float(raw["identity"]), 6),
                "query_coverage": round(float(raw["query_coverage"]), 6),
                "aligned_length": int(raw["aligned_length"]),
                "query_start": raw.get("query_start") or alignment["query_start"],
                "query_end": raw.get("query_end") or alignment["query_end"],
                "reference_start": raw.get("reference_start") or alignment["reference_start"],
                "reference_end": raw.get("reference_end") or alignment["reference_end"],
                "mismatch_count": raw.get("mismatch_count") if raw.get("mismatch_count") is not None else alignment["mismatch_count"],
                "gap_count": raw.get("gap_count") if raw.get("gap_count") is not None else alignment["gap_count"],
                "bit_score": round(float(raw.get("bit_score") or raw["identity"] * raw["query_coverage"]), 6),
                "evalue": raw.get("evalue"),
                "reference_id": entry.reference_id,
                "reference_database": manifest["title"],
                "gbif_taxon_key": entry.gbif_taxon_key,
                "lineage": entry.lineage,
            }
        )

    return {
        "query": {
            "sequence_id": sequence_id,
            "sequence_length": len(clean_sequence),
            "sequence_md5": hashlib.md5(clean_sequence.encode("utf-8")).hexdigest(),
        },
        "reference_dataset": {
            "id": manifest["id"],
            "title": manifest["title"],
            "marker": manifest.get("marker"),
            "source": manifest.get("source"),
            "license": manifest.get("license"),
            "sha256": sha256_file(fasta_path),
        },
        "backend_requested": backend,
        "backend_used": selected_backend,
        "searched_at": datetime.now(timezone.utc).isoformat(),
        "hits": hits,
        "warnings": backend_warnings(selected_backend),
    }


def build_fragment_graph(
    *,
    sequence: str,
    sequence_id: str = "fragment-001",
    reference_dataset: str = "ncbi_aedes_coi_small",
    backend: str = "auto",
    max_hits: int = 50,
) -> dict[str, Any]:
    search_result = search_reference(
        sequence=sequence,
        sequence_id=sequence_id,
        reference_dataset=reference_dataset,
        backend=backend,
        max_hits=max_hits,
    )
    hits = search_result["hits"]
    informative_hits = [
        hit for hit in hits
        if float(hit.get("identity") or 0) > 90 and float(hit.get("query_coverage") or 0) >= 80
    ]
    informative_lineages = [lineage_for_hit(hit) for hit in informative_hits]
    kingdoms = unique_names_for_rank(informative_lineages, "kingdom")
    safe_taxon = lowest_common_taxon(informative_lineages)
    classification_status = classify_fragment_graph(
        hits=hits,
        informative_hits=informative_hits,
        kingdoms=kingdoms,
        safe_taxon=safe_taxon,
    )
    nodes, edges = fragment_graph_nodes_edges(
        sequence_id=sequence_id,
        search_result=search_result,
        hits=hits,
        informative_hits=informative_hits,
        safe_taxon=safe_taxon,
        classification_status=classification_status,
    )
    informative_taxa = {
        (hit.get("rank") or "unknown", hit.get("taxon") or hit.get("reference_id"))
        for hit in informative_hits
    }
    segments = build_segment_map(
        sequence=normalize_sequence(sequence),
        sequence_id=sequence_id,
        hits=hits,
        informative_hits=informative_hits,
        safe_taxon=safe_taxon,
        classification_status=classification_status,
        reference_dataset=search_result["reference_dataset"],
        backend_used=search_result["backend_used"],
    )

    return {
        "query": search_result["query"],
        "reference_dataset": search_result["reference_dataset"],
        "backend_requested": search_result["backend_requested"],
        "backend_used": search_result["backend_used"],
        "searched_at": search_result["searched_at"],
        "source_monitor": source_monitor_for_graph(search_result),
        "classification": {
            "status": classification_status,
            "safe_taxon": safe_taxon,
            "kingdoms": kingdoms,
            "taxa_count": len(informative_taxa),
            "informative_hits": len(informative_hits),
            "rank_distribution": rank_distribution(informative_lineages),
            "caveat": "Graph is limited to the selected reference dataset.",
        },
        "claim_boundary": fragment_claim_boundary(classification_status, safe_taxon),
        "segments": segments,
        "nodes": nodes,
        "edges": edges,
        "hits": hits,
        "warnings": search_result["warnings"],
    }


def source_monitor_for_graph(search_result: dict[str, Any]) -> list[dict[str, Any]]:
    backend = search_result["backend_used"]
    return [
        {
            "source": "local_reference_dataset",
            "status": "done",
            "detail": search_result["reference_dataset"]["id"],
            "cached": True,
        },
        {
            "source": backend,
            "status": "review_only" if backend == "python-local" else "done",
            "detail": "deterministic mini-search" if backend == "python-local" else "external aligner available in runtime",
            "cached": False,
        },
    ]


def build_segment_map(
    *,
    sequence: str,
    sequence_id: str,
    hits: list[dict[str, Any]],
    informative_hits: list[dict[str, Any]],
    safe_taxon: dict[str, Any],
    classification_status: str,
    reference_dataset: dict[str, Any],
    backend_used: str,
) -> list[dict[str, Any]]:
    query_length = len(sequence)
    aligned_hits = [
        hit for hit in hits
        if hit.get("query_start") and hit.get("query_end") and int(hit["query_end"]) >= int(hit["query_start"])
    ]
    if not aligned_hits:
        return [
            segment_evidence(
                sequence=sequence,
                sequence_id=sequence_id,
                start=1,
                end=query_length,
                hits=[],
                safe_taxon={"rank": "none", "name": "No safe taxon", "taxon_key": None},
                status="no-match" if not hits else "weak",
                reference_dataset=reference_dataset,
                backend_used=backend_used,
            )
        ]

    breakpoints = {1, query_length + 1}
    for hit in aligned_hits:
        breakpoints.add(max(1, int(hit["query_start"])))
        breakpoints.add(min(query_length + 1, int(hit["query_end"]) + 1))
    ordered = sorted(breakpoints)
    segments = []
    for index, start in enumerate(ordered[:-1], start=1):
        end = ordered[index] - 1
        if end < start:
            continue
        overlapping = [
            hit for hit in aligned_hits
            if int(hit["query_start"]) <= end and int(hit["query_end"]) >= start
        ]
        overlapping_informative = [
            hit for hit in overlapping
            if hit in informative_hits or (
                float(hit.get("identity") or 0) > 90 and float(hit.get("query_coverage") or 0) >= 80
            )
        ]
        lineages = [lineage_for_hit(hit) for hit in overlapping_informative]
        segment_safe_taxon = lowest_common_taxon(lineages) if lineages else {"rank": "none", "name": "No safe taxon", "taxon_key": None}
        status = classify_fragment_graph(
            hits=overlapping,
            informative_hits=overlapping_informative,
            kingdoms=unique_names_for_rank(lineages, "kingdom"),
            safe_taxon=segment_safe_taxon,
        )
        if len(ordered) == 2:
            status = classification_status
            segment_safe_taxon = safe_taxon
        segments.append(
            segment_evidence(
                sequence=sequence,
                sequence_id=sequence_id,
                start=start,
                end=end,
                hits=overlapping,
                safe_taxon=segment_safe_taxon,
                status=status,
                reference_dataset=reference_dataset,
                backend_used=backend_used,
            )
        )
    return segments


def segment_evidence(
    *,
    sequence: str,
    sequence_id: str,
    start: int,
    end: int,
    hits: list[dict[str, Any]],
    safe_taxon: dict[str, Any],
    status: str,
    reference_dataset: dict[str, Any],
    backend_used: str,
) -> dict[str, Any]:
    segment_sequence = sequence[start - 1 : end]
    length = len(segment_sequence)
    taxa = sorted({hit.get("taxon") or hit.get("reference_id") for hit in hits if hit.get("taxon") or hit.get("reference_id")})
    segment_hits = [segment_hit_summary(hit, start, end, length) for hit in hits]
    best_identity = max((float(hit.get("identity") or 0) for hit in hits), default=0.0)
    best_coverage = max((float(item.get("query_coverage_percent") or 0) for item in segment_hits), default=0.0)
    specificity = taxonomic_specificity([hit.get("taxon") or hit.get("reference_id") for hit in hits])
    blockers = segment_blockers(status=status, length=length, backend_used=backend_used, low_complexity=low_complexity_score(segment_sequence))
    return {
        "segment_id": f"{sequence_id}:{start}-{end}",
        "sequence_id": sequence_id,
        "segment_start": start,
        "segment_end": end,
        "segment_length": length,
        "sequence_sha256": hashlib.sha256(segment_sequence.encode("utf-8")).hexdigest(),
        "segment_class": segment_length_class(length),
        "ambiguity_base_count": sum(1 for base in segment_sequence if base not in {"A", "C", "G", "T"}),
        "low_complexity_score": low_complexity_score(segment_sequence),
        "match_summary": {
            "best_identity": round(best_identity, 6),
            "best_query_coverage": round(best_coverage, 6),
            "indistinguishable_taxa_count": len(taxa),
            "all_indistinguishable_taxa": taxa,
            "safe_lca": safe_taxon,
            "taxonomic_specificity": specificity,
            "reference_completeness": {
                "status": "selected_reference_only",
                "reference_dataset_id": reference_dataset.get("id"),
                "reference_dataset_title": reference_dataset.get("title"),
                "taxa_with_segment": len(taxa),
            },
            "claim_boundary": fragment_claim_boundary(status, safe_taxon)["supported"],
        },
        "known_annotations": known_segment_annotations(length=length, reference_dataset=reference_dataset, backend_used=backend_used),
        "blockers": blockers,
        "hits": segment_hits,
    }


def segment_hit_summary(hit: dict[str, Any], start: int, end: int, segment_length: int) -> dict[str, Any]:
    hit_start = int(hit.get("query_start") or start)
    hit_end = int(hit.get("query_end") or end)
    overlap_start = max(start, hit_start)
    overlap_end = min(end, hit_end)
    overlap = max(0, overlap_end - overlap_start + 1)
    identity = float(hit.get("identity") or 0)
    estimated_mismatches = round(overlap * max(0.0, 1 - identity / 100))
    ref_start = hit.get("reference_start")
    if ref_start:
        reference_overlap_start = int(ref_start) + max(0, overlap_start - hit_start)
    else:
        reference_overlap_start = None
    return {
        "reference_id": hit.get("reference_id"),
        "taxon": hit.get("taxon"),
        "rank": hit.get("rank"),
        "identity_percent": round(identity, 6),
        "query_coverage_percent": round((overlap / max(segment_length, 1)) * 100, 6),
        "reference_coverage_percent": round((overlap / max(int(hit.get("aligned_length") or overlap or 1), 1)) * 100, 6),
        "mismatch_count": hit.get("mismatch_count") if hit.get("mismatch_count") is not None else estimated_mismatches,
        "gap_count": hit.get("gap_count") if hit.get("gap_count") is not None else 0,
        "query_start": overlap_start,
        "query_end": overlap_end,
        "reference_start": reference_overlap_start,
        "reference_end": reference_overlap_start + overlap - 1 if reference_overlap_start else None,
        "gbif_taxon_key": hit.get("gbif_taxon_key"),
    }


def segment_length_class(length: int) -> str:
    if length < 30:
        return "too_short_review_only"
    if length < 80:
        return "mini_fragment"
    if length < 250:
        return "mini_barcode"
    return "barcode_or_longer"


def known_segment_annotations(*, length: int, reference_dataset: dict[str, Any], backend_used: str) -> list[dict[str, Any]]:
    marker = reference_dataset.get("marker") or "marker not declared"
    annotations = [
        {
            "type": "marker_region",
            "label": f"{marker} matched region",
            "source": "reference manifest",
            "provenance": reference_dataset.get("id"),
            "evidence_level": "coordinate_overlap_hint",
        },
        {
            "type": "evidence_mode",
            "label": segment_length_class(length).replace("_", " "),
            "source": "EcoGenesis length policy",
            "provenance": "local deterministic classifier",
            "evidence_level": "claim_boundary",
        },
    ]
    if backend_used == "python-local":
        annotations.append(
            {
                "type": "source_caveat",
                "label": "python-local mini-search is review-only",
                "source": "EcoGenesis runtime",
                "provenance": "search-status",
                "evidence_level": "publication_blocker",
            }
        )
    return annotations


def segment_blockers(*, status: str, length: int, backend_used: str, low_complexity: float) -> list[str]:
    blockers = []
    if length < 30:
        blockers.append("segment too short for taxonomic claim")
    if status in {"weak", "no-match", "cross-kingdom-conserved"}:
        blockers.append(warning_for_fragment_status(status, status != "no-match", status != "weak"))
    if backend_used == "python-local":
        blockers.append("review only: production aligner was not used")
    if low_complexity >= 0.85:
        blockers.append("low-complexity segment; review primer/contamination possibility")
    return dedupe_strings(blockers)


def fragment_claim_boundary(status: str, safe_taxon: dict[str, Any]) -> dict[str, Any]:
    safe_name = safe_taxon.get("name") or "No safe taxon"
    safe_rank = safe_taxon.get("rank") or "none"
    if status == "species-diagnostic":
        supported = f"Species-level molecular assignment candidate for {safe_name} within this selected reference dataset."
    elif status == "genus-shared":
        supported = f"Genus-level fragment evidence for {safe_name}; species-level claims are blocked."
    elif status == "higher-rank-shared":
        supported = f"{safe_rank.title()}-level fragment evidence for {safe_name}; lower-rank claims are blocked."
    elif status == "cross-kingdom-conserved":
        supported = "Conserved or cross-kingdom review signal only; no taxonomic assignment should be exported."
    elif status == "no-match":
        supported = "No claim from this selected reference dataset."
    else:
        supported = "Review-only fragment evidence; improve length, quality or reference coverage."
    return {
        "supported": supported,
        "not_supported": [
            "natural occurrence, absence, abundance or distribution",
            "phenotype/function/ecological role unless a curated coordinate-based annotation is attached",
            "global species truth outside the selected reference dataset",
        ],
    }


def taxonomic_specificity(taxa: list[str | None]) -> float:
    clean_taxa = [taxon for taxon in taxa if taxon]
    if not clean_taxa:
        return 0.0
    counts = {taxon: clean_taxa.count(taxon) for taxon in set(clean_taxa)}
    if len(counts) == 1:
        return 1.0
    total = len(clean_taxa)
    entropy = -sum((count / total) * math.log(count / total, 2) for count in counts.values())
    max_entropy = math.log(len(counts), 2)
    return round(1 - (entropy / max_entropy), 6) if max_entropy else 1.0


def low_complexity_score(sequence: str) -> float:
    if not sequence:
        return 0.0
    return round(max(sequence.count(base) for base in set(sequence)) / len(sequence), 6)


def dedupe_strings(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def lineage_for_hit(hit: dict[str, Any]) -> list[dict[str, Any]]:
    lineage = [
        {
            "rank": str(item.get("rank") or "").strip().lower() or "unranked",
            "name": item.get("name") or item.get("canonicalName") or "unknown lineage",
            "taxon_key": item.get("taxon_key"),
        }
        for item in hit.get("lineage", [])
        if item.get("name")
    ]
    hit_rank = str(hit.get("rank") or "species").strip().lower()
    hit_taxon = hit.get("taxon")
    if hit_taxon and hit_rank not in {item["rank"] for item in lineage}:
        lineage.append({"rank": hit_rank, "name": hit_taxon, "taxon_key": hit.get("gbif_taxon_key")})
    if not lineage and hit_taxon:
        lineage.append({"rank": hit_rank, "name": hit_taxon, "taxon_key": hit.get("gbif_taxon_key")})
    return lineage


def unique_names_for_rank(lineages: list[list[dict[str, Any]]], rank: str) -> list[str]:
    names = []
    seen = set()
    for lineage in lineages:
        for item in lineage:
            if item.get("rank") != rank:
                continue
            name = item.get("name") or "unknown"
            key = name.lower()
            if key not in seen:
                seen.add(key)
                names.append(name)
    return names


def lowest_common_taxon(lineages: list[list[dict[str, Any]]]) -> dict[str, Any]:
    if not lineages:
        return {"rank": "none", "name": "No safe taxon", "taxon_key": None}

    rank_maps = []
    for lineage in lineages:
        by_rank = {}
        for item in lineage:
            rank = str(item.get("rank") or "").strip().lower()
            if rank in GBIF_LINEAGE_RANKS:
                by_rank[rank] = item
        rank_maps.append(by_rank)

    candidate: dict[str, Any] | None = None
    for rank in GBIF_LINEAGE_RANKS:
        ranked_items = [rank_map.get(rank) for rank_map in rank_maps]
        if any(item is None for item in ranked_items):
            break
        normalized_names = {str(item["name"]).strip().lower() for item in ranked_items if item}
        if len(normalized_names) != 1:
            break
        item = ranked_items[0] or {}
        candidate = {
            "rank": rank,
            "name": item.get("name"),
            "taxon_key": item.get("taxon_key"),
        }

    return candidate or {"rank": "none", "name": "No shared taxon in selected reference dataset", "taxon_key": None}


def classify_fragment_graph(
    *,
    hits: list[dict[str, Any]],
    informative_hits: list[dict[str, Any]],
    kingdoms: list[str],
    safe_taxon: dict[str, Any],
) -> str:
    if not hits:
        return "no-match"
    if not informative_hits:
        return "weak"
    if len(kingdoms) > 1:
        return "cross-kingdom-conserved"
    rank = safe_taxon.get("rank")
    if rank == "species":
        return "species-diagnostic"
    if rank == "genus":
        return "genus-shared"
    if rank in {"family", "order", "class", "phylum", "kingdom"}:
        return "higher-rank-shared"
    return "weak"


def rank_distribution(lineages: list[list[dict[str, Any]]]) -> dict[str, int]:
    distribution: dict[str, set[str]] = {rank: set() for rank in GBIF_LINEAGE_RANKS}
    for lineage in lineages:
        for item in lineage:
            rank = str(item.get("rank") or "").strip().lower()
            name = item.get("name")
            if rank in distribution and name:
                distribution[rank].add(str(name))
    return {rank: len(names) for rank, names in distribution.items() if names}


def fragment_graph_nodes_edges(
    *,
    sequence_id: str,
    search_result: dict[str, Any],
    hits: list[dict[str, Any]],
    informative_hits: list[dict[str, Any]],
    safe_taxon: dict[str, Any],
    classification_status: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}

    fragment_id = f"fragment:{sanitize_graph_id(sequence_id)}"
    dataset_id = f"reference_dataset:{sanitize_graph_id(search_result['reference_dataset']['id'])}"
    add_node(nodes, fragment_id, "fragment", "Query fragment", sequence_id=sequence_id, sequence_length=search_result["query"]["sequence_length"])
    add_node(
        nodes,
        dataset_id,
        "reference_dataset",
        search_result["reference_dataset"]["title"],
        dataset_id=search_result["reference_dataset"]["id"],
        marker=search_result["reference_dataset"].get("marker"),
    )
    add_edge(edges, fragment_id, dataset_id, "searched_against")

    informative_reference_ids = {hit.get("reference_id") for hit in informative_hits}
    for index, hit in enumerate(hits):
        reference_id = hit.get("reference_id") or f"hit-{index + 1}"
        hit_id = f"hit:{sanitize_graph_id(reference_id)}"
        add_node(
            nodes,
            hit_id,
            "reference_hit",
            hit.get("taxon") or reference_id,
            reference_id=reference_id,
            identity=hit.get("identity"),
            coverage=hit.get("query_coverage"),
            aligned_length=hit.get("aligned_length"),
            match_type=match_type_for_graph(hit),
            informative=reference_id in informative_reference_ids,
        )
        add_edge(edges, fragment_id, hit_id, "matches_reference", identity=hit.get("identity"), coverage=hit.get("query_coverage"))
        previous_taxon_id = None
        lineage = lineage_for_hit(hit)
        for item in lineage:
            taxon_id = taxon_graph_id(item)
            is_safe_taxon = (
                safe_taxon.get("rank") == item.get("rank")
                and str(safe_taxon.get("name") or "").lower() == str(item.get("name") or "").lower()
            )
            add_node(
                nodes,
                taxon_id,
                item.get("rank") or "unranked",
                item.get("name") or "unknown lineage",
                rank=item.get("rank"),
                taxon_key=item.get("taxon_key"),
                is_safe_taxon=is_safe_taxon,
            )
            if previous_taxon_id:
                add_edge(edges, previous_taxon_id, taxon_id, "parent_taxon")
            previous_taxon_id = taxon_id
        if previous_taxon_id:
            add_edge(edges, hit_id, previous_taxon_id, "belongs_to_taxon")

    if safe_taxon.get("rank") not in {None, "none"} and safe_taxon.get("name"):
        safe_id = f"safe_lca:{sanitize_graph_id(safe_taxon['rank'])}:{sanitize_graph_id(safe_taxon['name'])}"
        add_node(nodes, safe_id, "safe_lca", f"Safe LCA: {safe_taxon['name']}", **safe_taxon)
        add_edge(edges, fragment_id, safe_id, "safe_lca_of")
        safe_taxon_id = taxon_graph_id(safe_taxon)
        if safe_taxon_id in nodes:
            add_edge(edges, safe_id, safe_taxon_id, "safe_lca_of")

    warning_label = warning_for_fragment_status(classification_status, bool(hits), bool(informative_hits))
    warning_id = f"warning:{classification_status}"
    add_node(nodes, warning_id, "warning", warning_label, status=classification_status)
    add_edge(edges, fragment_id, warning_id, "limited_by")

    return list(nodes.values()), list(edges.values())


def add_node(nodes: dict[str, dict[str, Any]], node_id: str, node_type: str, label: str, **properties: Any) -> None:
    existing = nodes.get(node_id)
    if existing:
        existing.update({key: value for key, value in properties.items() if value is not None})
        if properties.get("is_safe_taxon"):
            existing["is_safe_taxon"] = True
        return
    nodes[node_id] = {
        "id": node_id,
        "type": node_type,
        "label": label,
        **{key: value for key, value in properties.items() if value is not None},
    }


def add_edge(edges: dict[tuple[str, str, str], dict[str, Any]], source: str, target: str, edge_type: str, **properties: Any) -> None:
    key = (source, target, edge_type)
    edges[key] = {
        "source": source,
        "target": target,
        "type": edge_type,
        **{item_key: value for item_key, value in properties.items() if value is not None},
    }


def taxon_graph_id(item: dict[str, Any]) -> str:
    return f"taxon:{sanitize_graph_id(item.get('rank') or 'unranked')}:{sanitize_graph_id(item.get('name') or 'unknown')}"


def sanitize_graph_id(value: Any) -> str:
    return re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(value or "unknown").strip()).strip("_") or "unknown"


def match_type_for_graph(hit: dict[str, Any]) -> str:
    identity = float(hit.get("identity") or 0)
    coverage = float(hit.get("query_coverage") or 0)
    if identity >= 99 and coverage >= 80:
        return "exact"
    if identity > 90 and coverage >= 80:
        return "close"
    return "weak"


def warning_for_fragment_status(status: str, has_hits: bool, has_informative_hits: bool) -> str:
    if status == "species-diagnostic":
        return "Species-level claim is supported only inside this selected reference dataset."
    if status == "genus-shared":
        return "Fragment is shared across species; use the genus-level claim."
    if status == "higher-rank-shared":
        return "Fragment is shared above genus; avoid species and genus claims."
    if status == "cross-kingdom-conserved":
        return "Fragment appears across kingdoms in this reference set; treat it as conserved or contaminated until reviewed."
    if has_hits and not has_informative_hits:
        return "Hits exist, but identity or coverage is too weak for a safe taxonomic claim."
    if not has_hits:
        return "No reference hits were returned for this selected reference dataset."
    return "Graph is limited by the selected reference dataset."


def compiler_request_from_search(
    search_result: dict[str, Any],
    *,
    sequence: str,
    sequence_id: str,
    project_title: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> BarcodeCompilerRequest:
    reference_dataset = search_result["reference_dataset"]
    manifest, _, _ = load_reference_dataset(reference_dataset["id"])
    clean_sequence = normalize_sequence(sequence)
    top_taxon = search_result["hits"][0]["taxon"] if search_result["hits"] else ""
    record_metadata = {
        "marker": reference_dataset.get("marker") or manifest.get("marker") or "COI-5P",
        "referenceDatabase": reference_dataset["title"],
        "methodOrSOP": f"EcoGenesis reference search using {search_result['backend_used']} over {reference_dataset['id']}",
        "analysisCreatedAt": datetime.now(timezone.utc).isoformat(),
        "candidateScientificName": top_taxon,
        "referenceSearchBackend": search_result["backend_used"],
        "referenceDatasetID": reference_dataset["id"],
    }
    record_metadata.update(metadata or {})
    hits = [
        ReferenceHit(
            taxon=hit["taxon"],
            rank=hit["rank"],
            identity=hit["identity"],
            query_coverage=hit["query_coverage"],
            aligned_length=hit["aligned_length"],
            bit_score=hit["bit_score"],
            evalue=hit.get("evalue"),
            reference_id=hit["reference_id"],
            reference_database=hit["reference_database"],
            gbif_taxon_key=hit.get("gbif_taxon_key"),
            lineage=[TaxonLineageItem(**item) for item in hit.get("lineage", [])],
        )
        for hit in search_result["hits"]
    ]
    top = hits[0] if hits else None
    barcode_gap = None
    diagnostic = None
    if top:
        barcode_gap_values = manifest.get("barcode_gap_by_taxon", {}).get(top.taxon)
        if barcode_gap_values:
            barcode_gap = BarcodeGapEvidence(
                intra_max_distance=barcode_gap_values.get("intra_max_distance"),
                inter_min_distance=barcode_gap_values.get("inter_min_distance"),
            )
        kmers = manifest.get("diagnostic_kmers_by_taxon", {}).get(top.taxon, [])
        if kmers:
            diagnostic = DiagnosticKmerEvidence(
                diagnostic_kmers=kmers,
                reference_total_windows=manifest.get("reference_total_windows", 1_000),
                epsilon=0.01,
                alpha=0.01,
                k=manifest.get("diagnostic_kmer_k"),
            )

    return BarcodeCompilerRequest(
        project_title=project_title or f"Reference search: {sequence_id}",
        marker=reference_dataset.get("marker") or manifest.get("marker") or "COI-5P",
        reference_database=reference_dataset["title"],
        method_or_sop=f"EcoGenesis reference search + Nexus V3 hard-gate compiler ({search_result['backend_used']})",
        reference_manifest={
            "db_name": reference_dataset["title"],
            "db_version": manifest.get("version"),
            "source": manifest.get("source", "example_reference_dataset"),
            "accessed_at": datetime.now(timezone.utc).date().isoformat(),
            "doi_or_url": manifest.get("doi_or_url"),
            "license": manifest.get("license"),
            "sha256": reference_dataset.get("sha256"),
        },
        records=[
            SequenceRecord(
                sequence_id=sequence_id,
                sequence=clean_sequence,
                metadata=record_metadata,
                hits=hits,
                barcode_gap=barcode_gap,
                diagnostic=diagnostic,
            )
        ],
    )


def load_reference_dataset(reference_dataset: str) -> tuple[dict[str, Any], Path, list[ReferenceEntry]]:
    safe_id = sanitize_dataset_id(reference_dataset)
    manifest_path = None
    for root, _source_type in reference_roots():
        candidate = root / safe_id / "manifest.json"
        if candidate.exists():
            manifest_path = candidate
            break
    if not manifest_path:
        raise FileNotFoundError(f"Reference dataset not found: {reference_dataset}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fasta_path = manifest_path.parent / manifest["fasta"]
    fasta_entries = read_fasta(fasta_path)
    metadata = manifest.get("references", {})
    entries = []
    for reference_id, sequence in fasta_entries.items():
        meta = metadata.get(reference_id, {})
        entries.append(
            ReferenceEntry(
                reference_id=reference_id,
                sequence=normalize_sequence(sequence),
                taxon=meta.get("taxon") or reference_id,
                rank=meta.get("rank") or "species",
                gbif_taxon_key=meta.get("gbif_taxon_key"),
                lineage=meta.get("lineage", []),
            )
        )
    return manifest, fasta_path, entries


def resolve_backend(backend: str) -> str:
    requested = (backend or "auto").strip().lower()
    if requested in {"python", "python-local", "local"}:
        return "python-local"
    if requested == "vsearch":
        return "vsearch" if shutil.which("vsearch") else "python-local"
    if requested in {"blast", "blastn", "blast+"}:
        return "blastn" if shutil.which("blastn") else "python-local"
    if shutil.which("vsearch"):
        return "vsearch"
    if shutil.which("blastn"):
        return "blastn"
    return "python-local"


def run_vsearch(sequence: str, sequence_id: str, fasta_path: Path, *, max_hits: int) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory() as tmpdir:
        query_path = Path(tmpdir) / "query.fasta"
        out_path = Path(tmpdir) / "hits.tsv"
        query_path.write_text(f">{sequence_id}\n{sequence}\n", encoding="utf-8")
        command = [
            "vsearch",
            "--usearch_global",
            str(query_path),
            "--db",
            str(fasta_path),
            "--id",
            "0.5",
            "--userout",
            str(out_path),
            "--userfields",
            "query+target+id+alnlen+qcov+bits+evalue",
            "--maxaccepts",
            str(max_hits),
            "--maxrejects",
            "0",
            "--quiet",
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        return parse_external_tsv(out_path)


def run_blastn(sequence: str, sequence_id: str, fasta_path: Path, *, max_hits: int) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory() as tmpdir:
        query_path = Path(tmpdir) / "query.fasta"
        query_path.write_text(f">{sequence_id}\n{sequence}\n", encoding="utf-8")
        command = [
            "blastn",
            "-query",
            str(query_path),
            "-subject",
            str(fasta_path),
            "-outfmt",
            "6 qseqid sseqid pident length qcovhsp bitscore evalue",
            "-max_target_seqs",
            str(max_hits),
        ]
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        return parse_external_lines(completed.stdout.splitlines())


def parse_external_tsv(out_path: Path) -> list[dict[str, Any]]:
    if not out_path.exists():
        return []
    return parse_external_lines(out_path.read_text(encoding="utf-8").splitlines())


def parse_external_lines(lines: list[str]) -> list[dict[str, Any]]:
    hits = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        hits.append(
            {
                "reference_id": parts[1],
                "identity": float(parts[2]),
                "aligned_length": int(float(parts[3])),
                "query_coverage": float(parts[4]),
                "bit_score": float(parts[5]),
                "evalue": float(parts[6]) if parts[6] not in {"*", ""} else None,
            }
        )
    return sorted(hits, key=lambda item: (item["bit_score"], item["identity"], item["query_coverage"]), reverse=True)


def run_python_local_search(sequence: str, entries: list[ReferenceEntry], *, max_hits: int) -> list[dict[str, Any]]:
    hits = []
    for entry in entries:
        identity, coverage, aligned_length = best_ungapped_identity(sequence, entry.sequence)
        hits.append(
            {
                "reference_id": entry.reference_id,
                "identity": identity,
                "query_coverage": coverage,
                "aligned_length": aligned_length,
                "bit_score": identity * coverage,
                "evalue": None,
            }
        )
    return sorted(hits, key=lambda item: (item["bit_score"], item["identity"], item["query_coverage"]), reverse=True)[:max_hits]


def best_ungapped_identity(query: str, reference: str) -> tuple[float, float, int]:
    alignment = best_ungapped_alignment(query, reference)
    return alignment["identity"], alignment["query_coverage"], alignment["aligned_length"]


def best_ungapped_alignment(query: str, reference: str) -> dict[str, Any]:
    if not query or not reference:
        return {
            "identity": 0.0,
            "query_coverage": 0.0,
            "aligned_length": 0,
            "query_start": None,
            "query_end": None,
            "reference_start": None,
            "reference_end": None,
            "match_count": 0,
            "mismatch_count": 0,
            "gap_count": 0,
        }
    best_matches = -1
    best_aligned = 0
    best_offset = 0
    for offset in range(-len(reference) + 1, len(query)):
        q_start = max(0, offset)
        r_start = max(0, -offset)
        aligned = min(len(query) - q_start, len(reference) - r_start)
        if aligned <= 0:
            continue
        matches = sum(1 for index in range(aligned) if query[q_start + index] == reference[r_start + index])
        if matches > best_matches or (matches == best_matches and aligned > best_aligned):
            best_matches = matches
            best_aligned = aligned
            best_offset = offset
    q_start = max(0, best_offset)
    r_start = max(0, -best_offset)
    identity = (best_matches / best_aligned) * 100 if best_aligned else 0.0
    coverage = (best_aligned / len(query)) * 100 if query else 0.0
    mismatches = max(best_aligned - best_matches, 0)
    return {
        "identity": round(identity, 6),
        "query_coverage": round(coverage, 6),
        "aligned_length": best_aligned,
        "query_start": q_start + 1 if best_aligned else None,
        "query_end": q_start + best_aligned if best_aligned else None,
        "reference_start": r_start + 1 if best_aligned else None,
        "reference_end": r_start + best_aligned if best_aligned else None,
        "match_count": best_matches if best_matches > 0 else 0,
        "mismatch_count": mismatches,
        "gap_count": 0,
    }


def read_fasta(path: Path) -> dict[str, str]:
    entries: dict[str, list[str]] = {}
    current_id = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            current_id = stripped[1:].split()[0]
            entries[current_id] = []
        elif current_id:
            entries[current_id].append(stripped)
    return {key: "".join(parts) for key, parts in entries.items()}


def parse_fasta_text(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, list[str]]] = []
    current_header = None
    current_parts: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            if current_header is not None:
                entries.append((current_header, current_parts))
            current_header = stripped[1:].strip()
            current_parts = []
        elif current_header is not None:
            current_parts.append(stripped)
        else:
            raise ValueError("FASTA sequence data must start with a header line beginning with '>'.")
    if current_header is not None:
        entries.append((current_header, current_parts))
    return [(header, "".join(parts)) for header, parts in entries if "".join(parts).strip()]


def normalize_sequence(sequence: str) -> str:
    clean = "".join(str(sequence or "").split()).upper().replace("-", "")
    if not clean:
        raise ValueError("sequence cannot be empty")
    invalid = sorted(set(clean) - DNA_ALPHABET)
    if invalid:
        raise ValueError(f"sequence contains unsupported characters: {''.join(invalid)}")
    return clean


def bundled_reference_root() -> Path:
    return Path(os.getenv("REFERENCE_DATA_DIR", REPO_ROOT / "references")).resolve()


def user_reference_root() -> Path:
    default_root = Path(os.getenv("EVIDENCE_DATA_DIR", "./data")).resolve() / "reference-datasets"
    return Path(os.getenv("USER_REFERENCE_DATA_DIR", default_root)).resolve()


def reference_roots() -> list[tuple[Path, str]]:
    return [(user_reference_root(), "uploaded"), (bundled_reference_root(), "bundled")]


def sanitize_dataset_id(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or "").strip()).strip("._-").lower()
    if not safe:
        raise ValueError("reference dataset id cannot be empty")
    return safe[:80]


def unique_user_dataset_id(value: str) -> str:
    base = sanitize_dataset_id(value)
    candidate = base
    index = 2
    root = user_reference_root()
    while (root / candidate).exists() or (bundled_reference_root() / candidate).exists():
        candidate = f"{base}_{index}"
        index += 1
    return candidate


def parse_reference_header(header: str) -> tuple[str, str, str, int | None]:
    parts = [part.strip() for part in header.split("|")]
    if len(parts) >= 2:
        reference_id = sanitize_reference_id(parts[0])
        taxon = parts[1] or reference_id
        rank = parts[2] if len(parts) >= 3 and parts[2] else "species"
        gbif_taxon_key = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else None
        return reference_id, taxon, rank, gbif_taxon_key

    tokens = header.split(maxsplit=1)
    reference_id = sanitize_reference_id(tokens[0] if tokens else "reference")
    taxon = tokens[1].strip() if len(tokens) > 1 else reference_id
    return reference_id, taxon, "species", None


def sanitize_reference_id(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(value or "").strip()).strip("._-:")
    return safe or "reference"


def uploaded_reference_lineage(*, taxon: str, rank: str, gbif_taxon_key: int | None) -> list[dict[str, Any]]:
    normalized_rank = str(rank or "species").strip().lower()
    words = [word for word in str(taxon or "").split() if word]
    if normalized_rank == "species" and len(words) >= 2:
        return [
            {"rank": "genus", "name": words[0], "taxon_key": None},
            {"rank": "species", "name": taxon, "taxon_key": gbif_taxon_key},
        ]
    return [{"rank": normalized_rank, "name": taxon, "taxon_key": gbif_taxon_key}]


def uploaded_reference_taxon_context(*, taxon: str, rank: str, gbif_taxon_key: int | None) -> dict[str, Any]:
    fallback = {
        "taxon": taxon,
        "rank": str(rank or "species").strip().lower(),
        "gbif_taxon_key": gbif_taxon_key,
        "lineage": uploaded_reference_lineage(taxon=taxon, rank=rank, gbif_taxon_key=gbif_taxon_key),
        "match": {
            "status": "fallback",
            "usageKey": gbif_taxon_key,
            "matchType": None,
            "confidence": None,
            "message": "GBIF backbone enrichment disabled or unavailable; inferred lineage from FASTA header.",
        },
    }
    if not gbif_backbone_enrichment_enabled():
        fallback["match"]["status"] = "disabled"
        fallback["match"]["message"] = "GBIF backbone enrichment disabled by GBIF_BACKBONE_ENRICH_UPLOADS."
        return fallback

    try:
        response = requests.get(
            f"{gbif_base_url()}/species/match",
            params={"name": taxon},
            timeout=float(os.getenv("GBIF_BACKBONE_TIMEOUT_SECONDS", "8")),
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        fallback["match"]["message"] = f"GBIF backbone enrichment failed: {exc}"
        return fallback

    confidence = payload.get("confidence") or 0
    match_type = payload.get("matchType")
    if not payload.get("usageKey") or match_type in {"NONE", "HIGHERRANK"} or confidence < 80:
        fallback["match"]["message"] = (
            f"GBIF backbone match was not precise enough "
            f"(matchType={match_type}, confidence={confidence})."
        )
        fallback["match"]["matchType"] = match_type
        fallback["match"]["confidence"] = confidence
        fallback["match"]["usageKey"] = payload.get("usageKey") or gbif_taxon_key
        return fallback

    normalized_rank = str(payload.get("rank") or rank or "species").strip().lower()
    canonical_taxon = payload.get("canonicalName") or payload.get("scientificName") or taxon
    lineage = gbif_match_lineage(payload, rank=normalized_rank, taxon=canonical_taxon)
    return {
        "taxon": canonical_taxon,
        "rank": normalized_rank,
        "gbif_taxon_key": payload.get("usageKey") or gbif_taxon_key,
        "lineage": lineage or fallback["lineage"],
        "match": {
            "status": "enriched",
            "usageKey": payload.get("usageKey"),
            "acceptedUsageKey": payload.get("acceptedUsageKey"),
            "matchType": match_type,
            "confidence": confidence,
            "scientificName": payload.get("scientificName"),
            "canonicalName": payload.get("canonicalName"),
            "gbifStatus": payload.get("status"),
            "message": "GBIF backbone lineage attached from /species/match.",
        },
    }


def gbif_match_lineage(payload: dict[str, Any], *, rank: str, taxon: str) -> list[dict[str, Any]]:
    lineage = []
    for lineage_rank in GBIF_LINEAGE_RANKS:
        name = payload.get(lineage_rank)
        key = payload.get(f"{lineage_rank}Key")
        if name:
            lineage.append({"rank": lineage_rank, "name": name, "taxon_key": key})
    if rank not in {item["rank"] for item in lineage} and taxon:
        lineage.append({"rank": rank, "name": taxon, "taxon_key": payload.get("usageKey")})
    return lineage


def gbif_backbone_enrichment_enabled() -> bool:
    return os.getenv("GBIF_BACKBONE_ENRICH_UPLOADS", "true").strip().lower() not in {"0", "false", "no", "off"}


def gbif_base_url() -> str:
    return os.getenv("GBIF_BASE_URL", "https://api.gbif.org/v1").rstrip("/")


def reference_evidence_from_sequences(sequences_by_taxon: dict[str, list[str]]) -> tuple[dict[str, dict[str, float]], dict[str, list[str]]]:
    barcode_gap_by_taxon: dict[str, dict[str, float]] = {}
    diagnostic_kmers_by_taxon: dict[str, list[str]] = {}
    all_taxa = sorted(sequences_by_taxon)
    for taxon, sequences in sequences_by_taxon.items():
        intra = 0.0
        for index, first in enumerate(sequences):
            for second in sequences[index + 1 :]:
                intra = max(intra, sequence_distance(first, second))
        inter_values = [
            sequence_distance(first, second)
            for other_taxon in all_taxa
            if other_taxon != taxon
            for first in sequences
            for second in sequences_by_taxon[other_taxon]
        ]
        if inter_values:
            barcode_gap_by_taxon[taxon] = {
                "intra_max_distance": round(intra, 6),
                "inter_min_distance": round(min(inter_values), 6),
            }

        taxon_kmers = set().union(*(kmers_for_sequence(sequence) for sequence in sequences))
        other_kmers = set().union(
            *(
                kmers_for_sequence(sequence)
                for other_taxon in all_taxa
                if other_taxon != taxon
                for sequence in sequences_by_taxon[other_taxon]
            )
        ) if len(all_taxa) > 1 else set()
        diagnostic = sorted(taxon_kmers - other_kmers)
        if diagnostic:
            diagnostic_kmers_by_taxon[taxon] = diagnostic[:50]
    return barcode_gap_by_taxon, diagnostic_kmers_by_taxon


def sequence_distance(first: str, second: str) -> float:
    if not first or not second:
        return 1.0
    aligned = min(len(first), len(second))
    mismatches = sum(1 for index in range(aligned) if first[index] != second[index])
    mismatches += abs(len(first) - len(second))
    return mismatches / max(len(first), len(second))


def kmers_for_sequence(sequence: str, k: int = 15) -> set[str]:
    if not sequence:
        return set()
    effective_k = min(k, len(sequence))
    return {sequence[index : index + effective_k] for index in range(0, len(sequence) - effective_k + 1)}


def backend_warnings(backend_used: str) -> list[str]:
    if backend_used == "python-local":
        return [
            "External VSEARCH/BLAST+ was not used for this run. Install vsearch/blastn or use Docker V3 for external search.",
            "Local mini-search is for demo, tests and small reference examples; production analysis should use a curated reference database and external aligner.",
        ]
    return []


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
