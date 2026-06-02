# EcoGenesis Nexus

## A Molecular Evidence Triage, Taxonomic Safety and Repair Engine for GBIF DNA-derived Data

EcoGenesis Nexus is an open, repeatable pre-publication engine for DNA-derived biodiversity data. It receives raw sequences, ASV/OTU tables, GBIF Sequence ID outputs, BLAST/VSEARCH/MMseqs2-style hit tables or qPCR/ddPCR detection tables and converts each molecular detection into the safest publishable GBIF claim.

The system does not simply copy the top sequence hit. It computes the safe taxonomic rank, explains ambiguity, classifies marker regions and diagnostic fragments, separates taxonomic evidence from GBIF publication readiness, blocks unsafe species-level overclaims and ranks the repair actions that would unlock the largest number of reusable records.

## Why it matters

GBIF is increasingly important for DNA-derived occurrence data, but molecular records are hard to publish safely. A sequence may be short, ambiguous, shared by several species, unsupported by reference libraries or blocked by missing occurrence metadata. EcoGenesis Nexus turns this uncertainty into an explicit evidence passport rather than hiding it in a single species name.

## Core questions answered

For every sequence or molecular detection, EcoGenesis answers:

1. What is the deepest taxonomic claim that can be safely made?
2. Which species-level claims must be blocked or downgraded?
3. Which sequence regions are diagnostic, conserved or low-information?
4. Which reference-library gaps prevent species-safe classification?
5. Which GBIF/DNA-derived metadata fields are missing?
6. Which repair actions unlock the most GBIF-ready records?
7. What Darwin Core and DNA-derived extension rows can be exported now?

## Main outputs

- Evidence passports for every sequence.
- Safe taxonomic assignments at species, genus or higher rank.
- Segment atlas showing diagnostic and conserved DNA windows.
- Publication blockers and repair plan.
- Reference-gap metrics.
- Darwin Core Occurrence export.
- GBIF DNA-derived extension export.
- Machine-readable evidence graph.
- Human-readable methods, citations and report.

## Innovation

EcoGenesis Nexus combines four layers that are usually separate:

1. sequence-to-reference matching;
2. taxonomic ambiguity and lowest-common-ancestor safety;
3. DNA marker / fragment evidence interpretation;
4. GBIF publication readiness and repair optimization.

The result is a practical GBIF-network tool: it helps publishers release more useful DNA-derived biodiversity records while reducing unsafe species-level claims.

## One-line pitch

EcoGenesis Nexus helps GBIF get more DNA-derived records without getting more unsafe species claims.
