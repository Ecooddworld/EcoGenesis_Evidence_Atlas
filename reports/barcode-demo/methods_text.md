# Methods

This run used **Barcode-to-GBIF Evidence Compiler** ruleset `barcode-gbif-compiler-v1`.

For each DNA barcode/metabarcoding sequence, the compiler evaluated percent identity, query coverage, a 95% ambiguity test over mismatch-rate standard errors, lowest common ancestor of indistinguishable hits, barcode gap, diagnostic k-mer support and GBIF publication metadata readiness.

Species-level output is fail-closed: a sequence is `species-safe` only when the exact match gate, ambiguity/LCA gate, positive barcode gap gate, diagnostic k-mer gate and publication-readiness gates all pass.

Reference context: COI Animals / BOLD public clustered reference. Marker: COI-5P.
