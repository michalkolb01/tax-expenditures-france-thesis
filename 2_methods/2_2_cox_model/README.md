# 2.2 – Cox model (section 4.2.2)

| Script | Output | Supports |
|---|---|---|
| `01_cox_models.py` | `tables/cox_models.csv`, `cox_with_controls.csv`, `terminations_per_year.csv`, `ph_tests.csv` | 5.3: HR 0.773 per score point (0.642–0.930, p = 0.006), reported as 0.77; with controls 0.786 (0.653–0.946), reported as 0.79; without the 13 scheduled closures 0.762. 5.4: terminations per year; Cox by period 0.623 (p = 0.009) for 2011–2014 and 0.849 (p = 0.146) from 2015 |
| `02_figures_5_2_5_3.py` | `figures/fig5_2_cox_hazard_ratios`, `fig5_3_terminations_per_year` (PDF + PNG) | Figures 5.2 and 5.3 |

Models: lifelines `CoxPHFitter` (Efron's method for tied event times; the data are annual). Controls:
households as beneficiaries, log cost in 2011, no cost estimate, age of the measure in 2011, income-tax
measure. `ph_tests.csv` gives the proportional-hazards tests on the scaled Schoenfeld residuals
(Kaplan–Meier time transform): score p = 0.72 (main model), p = 0.71 (controls model); global
p = 0.72 and p = 0.46.

Inputs: `data/intermediate/termination_dataset_v35.csv`, `guillaume_all.csv`, `vm_2009_2019.parquet`.
Source: analysis notebook `Untitled9.ipynb` (cells 11, 29, 31, 35). Figures need the Latin Modern fonts.
