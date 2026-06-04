# Data Licenses

EcoGenesis Evidence Atlas does not redistribute live GBIF data by default. Demo fixtures are small synthetic GBIF-like examples used for repeatable testing.

The included `references/aedes_coi_mini/` FASTA and manifest are synthetic EcoGenesis workflow examples, licensed CC0-1.0 for testing and demonstration. They are not a curated production barcode reference database and must not be cited as biological evidence for real-world taxonomic conclusions.

The included `references/ncbi_aedes_coi_small/` and `references/ncbi_quercus_rbcl_small/` packs contain small NCBI GenBank public sequence-record examples used for workflow validation. EcoGenesis preserves accession IDs, source URLs, GBIF backbone keys and an access date in each manifest. NCBI does not impose additional restrictions on the use or distribution of GenBank records, but users should still verify original submitter/source record terms and cite/accession records appropriately before publication. These packs are intentionally small and are not curated production reference libraries.

When running online mode, users must follow the licenses and citation requirements attached to each GBIF-mediated dataset. Evidence packs preserve `datasetKey`, license, publisher and record counts so users can create a DOI-backed GBIF download or derived dataset citation before publication.

Primary references:

- GBIF citation guidelines: https://www.gbif.org/citation-guidelines
- GBIF API documentation: https://techdocs.gbif.org/en/openapi/
- GBIF Species API `/species/match`: https://techdocs.gbif.org/en/openapi/v1/species#/Searching%20names/matchNames
- NCBI GenBank overview: https://www.ncbi.nlm.nih.gov/genbank/
