from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Any

from .schemas import BarcodeCompilerRequest, BarcodeGapEvidence, DiagnosticKmerEvidence, ReferenceHit, SequenceRecord, TaxonLineageItem


REPO_ROOT = Path(__file__).resolve().parents[3]
REFERENCE_ROOT = Path(os.getenv("REFERENCE_DATA_DIR", REPO_ROOT / "references")).resolve()
DEFAULT_REFERENCE_ID = "aedes_coi_mini"
DNA_ALPHABET = set("ACGTRYSWKMBDHVN")


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
        "reference_root": str(REFERENCE_ROOT),
    }


def list_reference_datasets() -> list[dict[str, Any]]:
    datasets = []
    if not REFERENCE_ROOT.exists():
        return datasets
    for manifest_path in sorted(REFERENCE_ROOT.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        fasta_path = manifest_path.parent / manifest["fasta"]
        datasets.append(
            {
                "id": manifest["id"],
                "title": manifest["title"],
                "marker": manifest.get("marker"),
                "source": manifest.get("source"),
                "license": manifest.get("license"),
                "fasta": str(fasta_path),
                "records": len(manifest.get("references", {})),
                "sha256": sha256_file(fasta_path) if fasta_path.exists() else None,
            }
        )
    return datasets


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
        hits.append(
            {
                "taxon": entry.taxon,
                "rank": entry.rank,
                "identity": round(float(raw["identity"]), 6),
                "query_coverage": round(float(raw["query_coverage"]), 6),
                "aligned_length": int(raw["aligned_length"]),
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
        "occurrenceID": f"urn:ecogenesis:reference-search:{sequence_id}",
        "basisOfRecord": "MaterialSample",
        "scientificName": top_taxon,
        "eventDate": datetime.now(timezone.utc).date().isoformat(),
        "marker": reference_dataset.get("marker") or manifest.get("marker") or "COI-5P",
        "referenceDatabase": reference_dataset["title"],
        "methodOrSOP": f"EcoGenesis reference search using {search_result['backend_used']} over {reference_dataset['id']}",
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
    manifest_path = REFERENCE_ROOT / reference_dataset / "manifest.json"
    if not manifest_path.exists():
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
    if not query or not reference:
        return 0.0, 0.0, 0
    best_matches = -1
    best_aligned = 0
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
    identity = (best_matches / best_aligned) * 100 if best_aligned else 0.0
    coverage = (best_aligned / len(query)) * 100 if query else 0.0
    return round(identity, 6), round(coverage, 6), best_aligned


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


def normalize_sequence(sequence: str) -> str:
    clean = "".join(str(sequence or "").split()).upper().replace("-", "")
    if not clean:
        raise ValueError("sequence cannot be empty")
    invalid = sorted(set(clean) - DNA_ALPHABET)
    if invalid:
        raise ValueError(f"sequence contains unsupported characters: {''.join(invalid)}")
    return clean


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
