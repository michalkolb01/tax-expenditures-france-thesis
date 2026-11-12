# Chapter 5 – Termination

Builds the termination dataset (379 measures open in 2011, version 3.5, frozen) and runs the
survival analysis: shares terminated, routes, Kaplan–Meier, Cox models, timing, Table 5.1 and
Figures 5.1–5.3.

| Order | Script | Produces |
|---|---|---|
| 1 | `build_termination_v35.py` | `tables/termination_dataset_v35.csv` (also copied to `data/intermediate/`), shares, Cox per point, diagnostics, frozen end dates, population drops |
| 2 | `02_survival_models.py` | Table 5.1; shares terminated; routes (111 end date / 26 suppression); route × basis; 13 scheduled closures; Cox: main 0.773, with controls 0.786, without scheduled closures 0.762, by period 0.623 / 0.849; terminations per year |
| 3 | `03_figures.py` | `figures/fig5_1_survival_by_score`, `fig5_2_cox_hazard_ratios`, `fig5_3_terminations_per_year` (PDF + PNG, Latin Modern) |
| 4 | `export_termination_panel.py` | `termination_panel_by_year.xlsx` (sheets Measures, Year by year, Excluded, Notes) |

```bash
python ch5/build_termination_v35.py
python ch5/02_survival_models.py
python ch5/03_figures.py
python ch5/export_termination_panel.py
```

Inputs: `data/intermediate/vm_2009_2019.parquet`, `vm_2020_2026.parquet` and `guillaume_all.csv`
(from `01_inventory_panel/`); `data/exits_to_code_v2.csv` (exit type of measures leaving the annex).
Rules, censoring and every hand-coded decision with its legal basis: `CHANGELOG.md`.

`build_termination_v35.py` is the author's frozen script; only its path lines were changed for the
package (marked `[replication package]`). `02_survival_models.py` and `03_figures.py` are taken from
the analysis notebook (`Untitled9.ipynb`, cells 11, 13–20, 29, 31, 34, 35).

`data/exits_coded_11_v2.csv` and `data/uncoded_exits.csv` document hand coding done for v2 and carried
into v3.5. The v2 dataset and its reports are in `archive/ch5_v2/` (not used in the thesis).

Notes
* Table 5.1 covers the 470 measures examined by the committee (the whole report), not only the 379 followed.
* The chapter's 111 / 26 split groups the `mechanism` column; the `basis` column gives 121 / 16
  (see `tables/route_by_basis.csv` and `CHANGELOG.md` §2).
* Figures need the Latin Modern fonts; they were not rendered in the environment where this package
  was assembled (fonts unavailable), see the main README.
