# Final Video Script: CSV Upload -> Score -> Evidence Pack

Target length: 3-5 minutes
Language: English
Goal: show inputs, process and outputs clearly enough for GBIF judges.

## 0:00-0:20 — Problem

Voiceover:

> DNA barcode and metabarcoding workflows often return a top species hit. But a top hit is not automatically a validated species occurrence or a dataset accepted for GBIF publication. The sequence may be short, ambiguous, unsupported by representative barcode-gap evidence, missing locally unique sequence signal, or blocked by missing publication metadata.

Visual:

- Show title: Molecular Evidence Conversion & Repair Engine for GBIF.
- Show short line: “From Sequence ID / BLAST-style outputs to bounded results and GBIF validation candidates.”

## 0:20-0:45 — What The Tool Does

Voiceover:

> Barcode-to-GBIF Evidence Compiler is a deterministic downstream compiler. It does not replace GBIF Sequence ID or expert validation. It takes Sequence ID, BLAST, BOLD, UNITE or lab-pipeline CSV results and tells the user which configured rules passed, what must be downgraded, and what must be repaired before external validation or publication.

Visual:

- Open the app.
- Show `Judge overview`.
- Show the evidence-gate path.

## 0:45-1:30 — Upload CSV

Voiceover:

> The main workflow starts with a CSV upload. The required fields are sequenceID and sequence. Match fields such as topTaxon, topIdentity, topCoverage, competitor hit, barcode gap and locally unique k-mers make bounded-rank rule results possible. Reference completeness and sequence QC remain explicit requirements.

Visual:

- Open `Run compiler`.
- Click `Download CSV template`.
- Upload `examples/aedes_good.csv`.
- Show preview and input-check summary.

## 1:30-2:10 — Generate From CSV

Voiceover:

> After the input checks, the user generates an Evidence Pack. The basic CSV remains review-only because audited reference-completeness and sequence-QC evidence are not supplied. This is deliberate fail-closed behavior, not a failed demo.

Visual:

- Click `Generate from CSV`.
- Show decision memo.
- Show the review-only `ambiguous` result and its blockers.
- Show the validation-candidate count and sequence decisions table.

## 2:10-2:50 — Show Blocked And Downgraded Claims

Voiceover:

> The important part is not that one example passes. The important part is fail-closed behavior. Ambiguous records are downgraded to genus. Weak coverage blocks species claims. Missing occurrence metadata blocks publication even when the taxonomic evidence is strong.

Visual:

- Briefly show or describe:
  - `examples/aedes_ambiguous.csv` -> `genus rule-pass` (`genus-safe` compatibility token)
  - `examples/aedes_missing_metadata.csv` -> `not-publishable`
  - `examples/aedes_weak_coverage.csv` -> `weak`
- Show filters: `Validation candidates`, `Review`, `Blocked`.

## 2:50-3:30 — Evidence Pack Outputs

Voiceover:

> The output is not just a label. The tool exports sequence safety tables, publication blockers, Darwin Core templates, DNA-derived extension templates, a molecular evidence report, methods text, citations, an evidence graph and a zipped Evidence Pack.

Visual:

- Show `Download outputs`.
- Show `evidence_pack.zip`.
- Show `sequence_safety_table.csv`.
- Show `publication_blockers.csv`.
- Show `dwc_occurrence_core_validation_candidates.csv`.
- Show `molecular_evidence_report.html`.

## 3:30-4:10 — Methods And Audits

Voiceover:

> The method is transparent. Species-level output is only allowed when fixed gates pass. Ambiguous top hits are collapsed to the lowest common ancestor. The system blocks overclaiming instead of hiding uncertainty in a generic score.

Visual:

- Open `Methods & Audits`.
- Show formula sections and failure-mode invariants.

## 4:10-4:40 — GBIF Context

Voiceover:

> The repository also includes a GBIF occurrence-audit layer. It checks GBIF API availability when live network mode is enabled, uses GBIF-mediated records for context tests, and demonstrates bounded claim language around no-evidence cells, sampling gaps and citation readiness. Those occurrence rows are not linked to the molecular rows.

Visual:

- Open `Regression & Audits`.
- Show 1000 records / 100 claims summary.

## 4:40-5:00 — Closing

Voiceover:

> This project changes the workflow from “top hit equals species” to reproducible evidence conversion: bounded rank results, blockers, repair actions and candidates for external GBIF/IPT validation.

Visual:

- Return to overview.
- Show final project title and public demo URL.

## Required Final Checks Before Upload

- Video plays without login.
- Captions or transcript are available.
- No copyrighted music or restricted media are used.
- The video demonstrates inputs, process and outputs.
- The public video URL is pasted into `gbif-entry-form-draft.md`.
