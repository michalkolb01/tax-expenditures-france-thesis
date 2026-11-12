# Data

All sources are public. Raw files are **not** redistributed in this package
because of their size; download them into `data/raw/` with the scripts in
`00_acquisition/`, which record every file in a manifest (URL, date of
download, size). The manifests used for the thesis are in
`00_acquisition/manifests/`.

## Raw sources (`data/raw/`)

| Folder | Content | Period | Publisher | Manifest |
|---|---|---|---|---|
| `vmt_tome2/` | *Évaluation des voies et moyens*, tome II (annex to each finance bill listing every tax expenditure), PDF | bills for 2009–2026 | Ministry of the Economy and Finance | `pdf_checklist.csv` |
| `guillaume_2011/` | Report of the Comité d'évaluation des dépenses fiscales et des niches sociales (2011), with the score of each measure | 2011 | Ministry of the Economy and Finance | — |
| `amendments/` | Amendments to finance bills, Assemblée nationale open data (XML/JSON) | 14th–17th legislatures (2012–2026) | Assemblée nationale | — |
| `dila_debats/` | Plenary verbatim records (`.taz`: tar archives compressed with Unix `compress`) | 2011–2017 | DILA | `manifest_dila.csv` |
| `an_portal/` | Plenary verbatim records, `debats_leg15.xml.zip`, `debats_leg16.xml.zip`, `debats_leg17.xml.zip` | 2017–2026 | Assemblée nationale open data | `manifest_an_portal.csv` |
| `committee/` | Finance Committee minutes (*comptes rendus*) | 2012–2026 | Assemblée nationale | `manifest_committee.csv`, `manifest_committee_14.csv` |

## Intermediate datasets (`data/intermediate/`)

Built by the pipeline. The files used for the thesis are included where
their size allows; the others can be rebuilt or downloaded from the
author's archive.

| File | Built by | Content | Included |
|---|---|---|---|
| `tax_expenditures_panel_2009_2026.xlsx` | `01_inventory_panel/` | Panel of all tax expenditures, one row per measure and year, with the 2011 score | yes |
| `termination_dataset_v2.csv` | `ch5/build_termination_v35.py` | One row per measure open in 2011: score, termination year, route, censoring | to add |
| `amendments_classified.csv` | `02_amendments/` | 7,861 amendment–measure pairs with the direction of each amendment | yes |
| `committee_blocks.parquet`, `committee_blocks_14.parquet` | `03_debate_corpus/` | Finance Committee minutes split into blocks (one per amendment discussed) | yes |
| `debate_blocks.parquet`, `debate_blocks_14.parquet`, `debate_blocks_17.parquet` | `03_debate_corpus/` | Plenary records split into blocks | no (84 MB, 53 MB, 13 MB): rebuild or download |
| `turns.parquet` | `03_debate_corpus/` | Speaking turns linked to measures through amendments (5,340 turns) | yes |
| `arguments_v3_dedup.csv` | `04_argument_classification/` | 3,352 distinct interventions on 129 measures, with the automated classification used as a finding aid | yes |

## The debate corpus ("social corpus")

The corpus of interventions on which section 6.3 draws is
`turns.parquet` + `arguments_v3_dedup.csv`: every speaking turn in the
committee and plenary debates on an amendment matched to a tax expenditure,
deduplicated (3,352 distinct interventions on 129 measures). Sections 6.2.1
and 6.2.2 search the complete records instead (all of `data/raw/` plus the
committee blocks), so as to include debates not tied to an amendment.
