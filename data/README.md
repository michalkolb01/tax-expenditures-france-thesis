# Data

All sources are public. Raw files are **not** redistributed in this package
because of their size; download them into `data/raw/` with the scripts in
`1_data/1_3_parliamentary_corpus/1_download/`, which record every file in a manifest (URL, date of
download, size, checksum). The manifests used for the thesis are in
`1_data/1_3_parliamentary_corpus/1_download/manifests/`.

## Raw sources (`data/raw/`)

| Folder | Content | Period | Publisher | Manifest |
|---|---|---|---|---|
| `vmt_tome2/` | *Évaluation des voies et moyens*, tome II (annex to each finance bill listing every tax expenditure), PDF and spreadsheets | bills for 2009–2026 | Ministry of the Economy and Finance | `pdf_checklist.csv` (hand check of the PDF parsing) |
| `guillaume_2011/` | Report of the Comité d'évaluation des dépenses fiscales et des niches sociales (2011), with the score of each measure | 2011 | Ministry of the Economy and Finance | — |
| `an_portal/` | Assembly open data: amendments (`amendements_leg14–17.xml.zip`), legislative files (`dossiers_leg*`), plenary records (`debats_leg15–17.xml.zip`), meetings, deputies | 14th–17th legislatures (2012–2026) | Assemblée nationale | `manifest_an_portal.csv` |
| `dila_debats/` | Plenary verbatim records (`.taz`: tar archives compressed with Unix `compress`) | 2011–2017 | DILA | `manifest_dila.csv` |
| `committee_cr/`, `committee_cr_14/` | Finance Committee minutes (*comptes rendus*), legislatures 15–17 and 14 | 2012–2026 | Assemblée nationale | `manifest_committee.csv`, `manifest_committee_14.csv` |

The tome II files and the 2011 report were saved by hand (no download script); the amendment archives of
legislatures 15 and 16 were downloaded by hand (see `1_data/1_3_parliamentary_corpus/1_download/README.md`).

## Intermediate datasets (`data/intermediate/`)

Built by the pipeline. The files used for the thesis are included where
their size allows; the others can be rebuilt or downloaded from the
author's archive.

| File | Built by | Content | Included |
|---|---|---|---|
| `guillaume_all.csv` | `1_data/1_2_panel_2009_2026/` | The 470 measures of the 2011 report: code, tax, label, evaluator, cost in 2011, beneficiaries, mission, score | yes |
| `vm_2009_2019.parquet`, `vm_2020_2026.parquet` | `1_data/1_2_panel_2009_2026/` | Annex panel, one row per measure and edition (PDF years 2009–2019, spreadsheet years 2020–2026) | yes |
| `tax_expenditures_panel_2009_2026.xlsx` | `1_data/1_2_panel_2009_2026/` | Panel of all tax expenditures, one row per measure and year, with the 2011 score | yes |
| `termination_dataset_v35.csv` | `1_data/1_2_panel_2009_2026/03_build_termination_v35.py` | One row per measure open in 2011 (379): score, termination year, route, censoring | yes |
| `amendments_classified.csv` | `1_data/1_3_parliamentary_corpus/2_amendments/` | 7,861 amendment–measure pairs with the direction of each amendment | yes |
| `amendments_14.parquet`, `amendments_15_17.parquet` | `1_data/1_3_parliamentary_corpus/2_amendments/` | All amendments, with articles cited and finance-bill labels | no (101 MB, 385 MB): rebuild |
| `committee_blocks.parquet`, `committee_blocks_14.parquet` | `1_data/1_3_parliamentary_corpus/3_blocks_and_turns/` | Complete Finance Committee minutes split into blocks (one per amendment discussed) | yes |
| `committee_matched.parquet`, `committee_matched_14.parquet` | `1_data/1_3_parliamentary_corpus/3_blocks_and_turns/` | Committee blocks linked to a matched amendment | yes |
| `debate_blocks.parquet`, `debate_blocks_14.parquet`, `debate_blocks_17.parquet` | `1_data/1_3_parliamentary_corpus/3_blocks_and_turns/` | Complete plenary records split into blocks | no (84 MB, 53 MB, 13 MB): rebuild or download |
| `debate_matched.parquet`, `debate_matched_14.parquet` | `1_data/1_3_parliamentary_corpus/3_blocks_and_turns/` | Plenary blocks linked to a matched amendment | yes |
| `turns.parquet` | `1_data/1_3_parliamentary_corpus/3_blocks_and_turns/` | Speaking turns linked to measures through amendments (5,340 turns) | yes |
| `arguments_v3_dedup.csv` | `archive/argument_classification/` | One row per distinct intervention (3,352 on 129 measures): intervention identifier `idx` (row of `turns.parquet`), measure code, and the columns of the earlier automated classification | yes (see below) |

## The corpus of interventions

The corpus on which sections 6.3 and 6.4 draw is `turns.parquet`: every
speaking turn in the committee and plenary debates on an amendment matched
to a tax expenditure, each linked to a measure through that amendment. It is
a corpus of texts linked to measures; it is read by hand. After removing
repeated texts there are 3,352 distinct interventions on 129 measures.

`arguments_v3_dedup.csv` is kept only because
`2_methods/2_4_arguments/01_build_reading_workbook.py` builds the reading workbook
from it. That script uses the intervention identifier (`idx`, to fetch the
text from `turns.parquet`) and the measure code; it uses the earlier
classification to drop interventions coded off-topic or purely procedural
(`categorie`, `niveau`), and shows the earlier position and category in the
reading sheets as a guide. The classification code is archived in
`archive/argument_classification/`.

Sections 6.2.1 and 6.2.2 do not use this corpus: they search the complete
records (all of `data/raw/` plus the committee blocks), so as to include
debates not tied to an amendment. See "Two bases in Chapter 6" in the main README.
