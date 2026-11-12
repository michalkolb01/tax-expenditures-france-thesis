# 2.4 – Reading the arguments in the corpus (section 4.2.4)

| Script | Output | Supports |
|---|---|---|
| `01_build_reading_workbook.py` | `data/ch6_reading_workbook.xlsx`, `data/ch6_reading_selection.csv` | 6.3: selection of 23 measures and 648 passages, read by hand |

Inputs: `data/intermediate/turns.parquet` (texts), `arguments_v3_dedup.csv` (intervention identifier,
measure code; the earlier classification is used to drop interventions coded off-topic or purely
procedural, and the earlier position and category are shown in the reading sheets as a guide),
`tax_expenditures_panel_2009_2026.xlsx` (names and 2011 scores). Selection rule, fixed in advance: the 9
measures with the most interventions and every measure scored 0 or 1 with at least 20 interventions; up
to the 40 longest substantive interventions per measure.
