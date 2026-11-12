# 1.2 – The panel of tax expenditures, 2009–2026 (section 4.1.2)

Inventories, population, termination and censoring.

| Order | Script | Output | Supports |
|---|---|---|---|
| 1 | `01_parse_voies_et_moyens.py` | `data/intermediate/vm_2009_2019.parquet` (6,018 measure-years, PDF editions), `vm_2020_2026.parquet` (3,285, spreadsheets), `vm_bilan_2009_2019.csv` | 4.1.2 (the inventories); PDF parser checked against the 2020 spreadsheet |
| 2 | `02_build_panel_xlsx.py` | `data/intermediate/tax_expenditures_panel_2009_2026.xlsx` (851 measures, 9,303 measure-years) | 4.1.2; names and scores used in 6.3 and 6.4 |
| 3 | `03_build_termination_v35.py` | `tables/termination_dataset_v35.csv` (also copied to `data/intermediate/`), population drops, frozen end dates, diagnostics | 4.1.2 and 5.1: population of 379 measures (278 scored: 95 / 81 / 42 / 60; 101 not scored); termination and censoring rules |
| 4 | `04_export_termination_panel.py` | `termination_panel_by_year.xlsx` (sheets Measures, Year by year, Excluded, Notes) | 4.1.2: the dataset for reading by hand; 470 → 379 traced in `Excluded` |

`CHANGELOG.md` documents v3.5 from the code: population rule, dating rule, censoring rules, the two
columns `mechanism` (how a measure ended) and `basis` (where the year comes from), and every hand-coded
decision with its legal basis. `data/` holds the hand-coded exit lists (`exits_to_code_v2.csv`,
`exits_coded_11_v2.csv`, `uncoded_exits.csv`) and `pdf_checklist.csv` (hand check of the PDF parsing).

Inputs: `data/raw/vmt_tome2/vm_YYYY.pdf|xlsx|xls` (saved by hand, no download script) and
`data/intermediate/guillaume_all.csv` (1.1). `03_build_termination_v35.py` is the author's frozen
script; only its path lines were changed for the package.

Source notebooks: *Master Thesis_3 Tome II* (c2–c14, c19, c23); panel workbook from `Untitled9.ipynb` c3.
Known caveats: 2020 legal-article check 457/468 (the notebook's text says 455); 2016 has a parsed legal
reference for only 424 of 525 measures; renumberings and reclassifications are handled in the
termination build (`CHANGELOG.md`), not in the panel.
