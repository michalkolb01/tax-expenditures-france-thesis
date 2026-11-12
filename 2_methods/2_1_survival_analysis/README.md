# 2.1 – Survival analysis (section 4.2.1)

| Script | Output | Supports |
|---|---|---|
| `01_kaplan_meier.py` | `tables/termination_shares_by_score.csv`, `routes_by_score.csv`, `route_by_basis.csv`, `km_survival_by_score.csv` | 5.1: 379 measures (95 / 81 / 42 / 60; 101 not scored). 5.2: terminated by 2026 41/95, 33/81, 10/42, 15/60, 38/101 (137); routes 111 end dates / 26 suppressions (grouped by `mechanism`); 13 scored measures with a closure scheduled in 2011; Kaplan–Meier curves |
| `02_figure_5_1.py` | `figures/fig5_1_survival_by_score.pdf` (+ PNG) | Figure 5.1 |

Input: `data/intermediate/termination_dataset_v35.csv` (built in `1_data/1_2_panel_2009_2026/`).
Source: analysis notebook `Untitled9.ipynb` (cells 13–20, 31, 34). Figure 5.1 needs the Latin Modern
fonts (see "Steps to run in Colab" in the main README).
