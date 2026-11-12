# 03 – Debate corpus

Splits the plenary records (DILA 2011–2017, Assembly open data 2017–2026) and the Finance Committee minutes into blocks, one per amendment discussed, then into speaking turns, and links each turn to a measure through the amendment.

Scripts, in execution order (all write to `data/intermediate/`; raw sources in `data/raw/`, see `00_acquisition/`):

1. `01_plenary_15_17.py` — plenary records of legislatures 15-17 (Assembly open data, `raw/an_portal/debats_leg*.xml.zip`) → `debate_blocks_17.parquet`, `debate_avis_17.parquet`, `debate_blocks.parquet`, `debate_avis.parquet` (blocks and the commission/government opinions), `debate_matched.parquet` (blocks linked to one amendment of `amendments_15_17.parquet` and to a measure through `amendments_classified.csv`). From *6_Debates*.
2. `02_plenary_14.py` — DILA plenary records of legislature 14 (`raw/dila_debats/`) → `debate_blocks_14.parquet`, `debate_avis_14.parquet`, `debate_matched_14.parquet` (input `amendments_14.parquet`, `amendments_classified.csv`). From *7_Committee*.
3. `03_committee.py` — Finance Committee minutes (`raw/committee_cr/`, `raw/committee_cr_14/` and their manifests) → `committee_blocks.parquet`, `committee_matched.parquet` (leg 15-17), `committee_blocks_14.parquet`, `committee_matched_14.parquet` (leg 14). From *7_Committee*.
4. `04_build_turns.py` — `debate_blocks.parquet`, `debate_matched.parquet`, `committee_matched.parquet`, `measures_with_bands.csv` → `turns.parquet` (5,340 speaking turns on 129 measures: speaker, text, measure, venue, 2011 score). From *7_Committee*.

The output is a corpus of texts (speaking turns) linked to measures through the amendments they discuss; it carries no coding of the content. The automated argument classification built on it is archived in `archive/argument_classification/` and is not used in the thesis.

Known caveats

- `committee_blocks.parquet` was written once, with the second version of the committee parser; `committee_matched.parquet` (879 rows) re-parses the minutes with an improved closing pattern ("Suivant l'avis ..., la commission adopte ...") but does not save those blocks. The two files rest on slightly different block boundaries; the committee turns in `turns.parquet` come from `committee_matched.parquet`.
- `turns.parquet` does not include legislature 14: `debate_matched_14.parquet` and `committee_matched_14.parquet` are built but not used downstream.
- `turns.parquet` has no amendment uid or date column; its row index is the key (`idx`) of the archived argument files and must not be reordered.
- Plenary and committee blocks are kept only when they resolve to exactly one amendment (leg 14 plenary: best word overlap between block and exposé among candidates).
- `amendments_classified.csv` was called `classified_combined.csv` in the notebooks. `finance_dossiers.csv`, read in dead cells of *6_Debates*, has no writer and is not used.
- In *6_Debates*, an exploratory cell broke the legislature-17 dates of `debate_avis.parquet`, repaired in a later cell; the script keeps the repair, which is a no-op when run in order.
- `debate_avis.parquet` stores missing opinions as the string "None" (all text columns cast to str).
