# 01 – Inventory panel

Parses the annexes Évaluation des voies et moyens, tome II (bills for 2009–2026) and the 2011 scores, and links measures across years by their code (renumberings and reclassifications handled by hand; see ch5/CHANGELOG.md).

Scripts, in order:

1. `01_parse_guillaume_2011.py` – Annex IV of the 2011 report → `guillaume_all.csv` (470 measures: 449 numbered, 21 unnumbered) and `guillaume_scored_0_1.csv` (224). Stops unless the counts match the report's own totals (score 0: 125, 1: 99, 2: 46, 3: 69, not evaluated: 131). From *2_TEs* c2–c12.
2. `02_parse_voies_et_moyens.py` – *Voies et moyens* tome II, PDF for 2009–2019 and spreadsheets for 2020–2026 → `vm_2009_2019.parquet` (6,018 measure-years, 718 measures), `vm_2020_2026.parquet` (3,285, 577), `vm_bilan_2009_2019.csv` (372 rows: legislative changes listed at the start of each edition). Checks the PDF reader against the 2020 spreadsheet. From *3_TomeII* c2–c14, c19, c23.
3. `03_build_panel_xlsx.py` – both parquets + 2011 scores → `tax_expenditures_panel_2009_2026.xlsx` (851 measures, 9,303 measure-years). From `Untitled9.ipynb` c3.

Inputs: `data/raw/guillaume_2011/*.pdf`; `data/raw/vmt_tome2/vm_YYYY.pdf` (2009–2026), `vm_2020.xlsx`–`vm_2024.xlsx`, `vm_2025.xls`, `vm_2026.xls`. Outputs go to `data/intermediate/`. The package's `tax_expenditures_panel_2009_2026.xlsx` and the two `vm_*.parquet` files (with `guillaume_all.csv`) are the outputs of this step.

Known caveats

- The notebooks read `raw/guillaume/` and `raw/voies_et_moyens/`; the scripts use the folder names of data/README.md (`guillaume_2011/`, `vmt_tome2/`), with the same file names.
- 2020 check (PDF vs spreadsheet): 468/468 measures, creation year 468/468, beneficiary counts 214/214, legal articles 457/468 (the notebook's Result text says 455; the cell output, with the final reference parser, says 457). The 2009–2019 PDFs cannot be checked otherwise.
- 2009 lists fewer measures (511): a coverage effect of that edition, not attrition. In 2016 only 424 of 525 measures have a parsed legal reference.
- The `articles` column was rewritten in a later session with the final version of the reference parser (3_TomeII c23); the script reapplies it at the end, which changes nothing in a fresh run.
- Dropped as descriptive/exploratory: the survival count of the 215 condemned measures per year (3_TomeII c16, `survival_curve.csv`, read by no later notebook) and the legislative action on them (c21, `suppressions_proposed.csv`, exploratory).
- Renumberings and reclassifications are not handled here (see ch5/CHANGELOG.md).
