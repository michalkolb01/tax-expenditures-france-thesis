# 1.1 – The 2011 evaluation and its scores (section 4.1.1)

| Script | Input | Output | Supports |
|---|---|---|---|
| `01_parse_guillaume_2011.py` | `data/raw/guillaume_2011/*.pdf` (Annex IV of the report) | `data/intermediate/guillaume_all.csv` (470 measures: 449 numbered, 21 not), `guillaume_scored_0_1.csv` | 4.1.1: 125 / 99 / 46 / 69 measures scored 0–3, 131 not scored (checked against the report's own totals) |
| `02_table_5_1.py` | `data/intermediate/guillaume_all.csv` | `tables/table5_1_scores_costs_2011.csv` | Table 5.1: cost in 2011 by score, 11,764 / 28,236 / 11,393 / 9,305 / 4,935; total 65,633 € m (over the 470 measures examined by the committee) |

Source notebook: *Master Thesis_2 TEs* (cells 2–12); Table 5.1 from the Chapter 5 analysis notebook.
The raw folder is called `guillaume` in the notebook; the script uses `guillaume_2011/` (same file).
