# 1.3 – The parliamentary corpus (section 4.1.3)

Records, amendments linked to measures, interventions.

| Folder | Step | Main outputs (`data/intermediate/`) |
|---|---|---|
| `1_download/` | Download the Assembly open data (amendments, legislative files, plenary records 2017–2026), the DILA plenary records 2011–2017 and the Finance Committee minutes 2012–2026; manifests in `1_download/manifests/` | files in `data/raw/` |
| `2_amendments/` | Parse amendments; match them to measures on the tax-code article; each candidate link checked by a language model, which also labels the direction of the amendment; no hand validation (a 100-pair sample was prepared but not coded) | `amendments_classified.csv` (7,861 amendment–measure pairs), `pairs_*.parquet`, `measures_with_bands.csv` |
| `3_blocks_and_turns/` | Split plenary and committee records into blocks (one per amendment discussed); link blocks to matched amendments; build the speaking turns | `committee_blocks*.parquet`, `debate_blocks*.parquet`, `*_matched*.parquet`, `turns.parquet` (5,340 turns on 129 measures) |

Supports 4.1.3 and 6.1 (the two bases of Chapter 6): the complete committee and plenary records are
searched in 4.2.3; the corpus of interventions linked to measures (`turns.parquet`; 3,352 distinct
interventions on 129 measures in `arguments_v3_dedup.csv`) is read in 4.2.4 and 4.2.5. The corpus is used only to locate debates, which are then read. Each subfolder's
README lists its scripts, source notebook cells and known caveats.
