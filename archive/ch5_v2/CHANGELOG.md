# CHANGELOG — results_ch5_v2

Built 10 Nov 2026 with `build_termination_v2.py` (DATING_RULE = `effective_year`, POPULATION_RULE = `recount`). No existing file was modified; every output is new and sits in this folder.

## 1. `exits_coded_11_v2.csv` (from `validation/exits_coded_11.csv`)

All 11 records changed. New columns: `termination_status`, `effective_year`, `legal_basis`, `link_to`, `notes_v2`.

| code | exit_type_v1 | score | exit_type_v2 | termination_status | effective_year | legal_basis | link_to |
|---|---|---|---|---|---|---|---|
| 730307 | renumbered | Non évalué | renumbered | linked, followed as one measure |  |  | 710110 |
| 300112 | unclear | Non évalué | repealed | TERMINATED | 2012 | Loi n° 2011-1978 (LFR 2011), art. 65 |  |
| 180104 | repealed | Non évalué | ended_before_2011 | DROP from population |  |  |  |
| 700101 | unclear | 0 | still_in_force | NOT terminated, censored 2026 |  |  |  |
| 320111 | expired | Non évalué | ended_before_2011 | DROP from population |  |  |  |
| 800206 | unclear | 1 | repealed | TERMINATED | 2020 | Loi n° 2019-1479 (LF 2020), art. 60; effective 1 July 2020 |  |
| 720202 | unclear | 2 | still_in_force | NOT terminated, censored 2026 |  |  |  |
| 140124 | repealed | Non évalué | ended_before_2011 | DROP from population |  |  |  |
| 570101 | reclassified | Non évalué | reclassified | NOT terminated, censored at last annex |  |  |  |
| 570102 | reclassified | Non évalué | reclassified | NOT terminated, censored at last annex |  |  |  |
| 920301 | unclear | 0 | still_in_force | NOT terminated, censored 2026 |  |  |  |

## 2. Population (recount rule) vs chapter population

- Dropped as ended before 2011 (hand-coded): 180104, 320111, 140124 (all not scored).
- In the chapter population, not in v2 (16): 2011 edition gives an end before 2011, later editions extend it: 110218 (1), 110228 (0), 110236 (0), 110240 (1), 110245 (0), 130204 (1), 130208 (1), 130209 (1), 130214 (1), 210316 (3), 210318 (0), 230403 (0), 230602 (1), 320131 (0), 800108 (0), 950103 (not scored).
- In v2, not in the chapter population (19): 2011 edition gives no end or an end ≥ 2011, latest dated end ≤ 2011: 070202 (not scored), 090103 (0), 110229 (not scored), 110233 (not scored), 110247 (0), 110253 (0), 110255 (0), 120135 (0), 140201 (1), 150514 (not scored), 190210 (not scored), 230204 (1), 230303 (not scored), 230404 (0), 320102 (0), 320123 (not scored), 320125 (not scored), 330103 (3), 730209 (not scored).

## 3. Termination outcomes changed vs the chapter code (measures in both populations)

`chapter` = outcome produced by the chapter code (*Master Thesis_4 Matching*, cells 6 and 18): end date 2012–2026 taken from the latest *dated* edition, or any exit from the annex. `v2` = this rebuild.

| code | score | chapter | v2 | v2 basis |
|---|---|---|---|---|
| 060108 | 0 | terminated 2020 (closure) | censored 2026 | still listed in 2026 |
| 060202 | 0 | terminated 2026 (closure) | censored 2026 | still listed in 2026 |
| 300104 | 0 | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 700101 | 0 | terminated 2015 (delisting) | censored 2026 | hand-coded: still in force |
| 730220 | 0 | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 800115 | 0 | terminated 2020 (delisting) | censored 2019 | renumbered, no successor, censored at exit |
| 800207 | 0 | terminated 2020 (delisting) | censored 2019 | renumbered, no successor, censored at exit |
| 800208 | 0 | terminated 2020 (delisting) | censored 2019 | renumbered, no successor, censored at exit |
| 800302 | 0 | terminated 2021 (delisting) | censored 2026 | still listed in 2026 |
| 800404 | 0 | terminated 2021 (delisting) | censored 2026 | still listed in 2026 |
| 800406 | 0 | terminated 2015 (closure) | censored 2019 | uncoded exit, censored at exit |
| 920301 | 0 | terminated 2025 (delisting) | censored 2026 | hand-coded: still in force |
| 960102 | 0 | terminated 2013 (delisting) | censored 2012 | reclassified, censored at exit |
| 060106 | 1 | terminated 2015 (closure) | censored 2026 | still listed in 2026 |
| 140119 | 1 | terminated 2014 (closure) | censored 2026 | still listed in 2026 |
| 180102 | 1 | terminated 2026 (closure) | censored 2026 | still listed in 2026 |
| 230409 | 1 | terminated 2014 (closure) | censored 2026 | still listed in 2026 |
| 700102 | 1 | terminated 2021 (delisting) | censored 2026 | still listed in 2026 |
| 730219 | 1 | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 800206 | 1 | terminated 2019 (delisting) | terminated 2020 | hand-coded repeal |
| 800403 | 1 | terminated 2021 (delisting) | censored 2026 | still listed in 2026 |
| 120101 | 2 | terminated 2012 (closure) | censored 2026 | still listed in 2026 |
| 220103 | 2 | terminated 2013 (delisting) | censored 2026 | still listed in 2026 |
| 720202 | 2 | terminated 2022 (delisting) | censored 2026 | hand-coded: still in force |
| 800101 | 2 | terminated 2020 (delisting) | censored 2019 | renumbered, no successor, censored at exit |
| 800102 | 2 | terminated 2020 (delisting) | censored 2019 | renumbered, no successor, censored at exit |
| 800103 | 2 | terminated 2021 (delisting) | censored 2026 | still listed in 2026 |
| 800109 | 2 | terminated 2012 (closure) | censored 2019 | uncoded exit, censored at exit |
| 110244 | 3 | terminated 2026 (closure) | censored 2026 | still listed in 2026 |
| 120133 | 3 | terminated 2016 (closure) | censored 2026 | still listed in 2026 |
| 250101 | 3 | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 560104 | 3 | terminated 2013 (delisting) | censored 2012 | reclassified, censored at exit |
| 730203 | 3 | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 730303 | 3 | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 740106 | 3 | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 800114 | 3 | terminated 2021 (delisting) | censored 2026 | still listed in 2026 |
| 960101 | 3 | terminated 2013 (delisting) | censored 2012 | reclassified, censored at exit |
| 050109 | not scored | terminated 2020 (closure) | censored 2026 | still listed in 2026 |
| 060101 | not scored | terminated 2013 (delisting) | censored 2012 | reclassified, censored at exit |
| 090108 | not scored | terminated 2020 (closure) | censored 2026 | still listed in 2026 |
| 100112 | not scored | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 110216 | not scored | terminated 2016 (closure) | censored 2026 | still listed in 2026 |
| 120307 | not scored | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 120308 | not scored | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 140110 | not scored | terminated 2013 (closure) | censored 2020 | uncoded exit, censored at exit |
| 160102 | not scored | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 190101 | not scored | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 210308 | not scored | terminated 2021 (closure) | censored 2026 | still listed in 2026 |
| 210322 | not scored | terminated 2019 (closure) | censored 2026 | still listed in 2026 |
| 300109 | not scored | terminated 2020 (closure) | censored 2026 | still listed in 2026 |
| 300112 | not scored | terminated 2013 (delisting) | terminated 2012 | hand-coded repeal |
| 300204 | not scored | terminated 2026 (closure) | censored 2026 | still listed in 2026 |
| 560103 | not scored | terminated 2013 (delisting) | censored 2012 | reclassified, censored at exit |
| 570101 | not scored | terminated 2024 (delisting) | censored 2023 | reclassified, censored at exit |
| 570102 | not scored | terminated 2024 (delisting) | censored 2023 | reclassified, censored at exit |
| 730204 | not scored | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 730215 | not scored | terminated 2020 (delisting) | censored 2019 | reclassified, censored at exit |
| 730307 | not scored | terminated 2021 (delisting) | censored 2026 | still listed in 2026 |

## 4. Flags (no recoding done)

- **800115** is coded `renumbered` in `exits_to_code_v2.csv`, but VM PLF 2020 p.31 lists it as **declassified**. Both rules censor it at 2019, so results are unaffected.
- **920301**: from PLF 2020 the code belongs to a different measure (TOCE exclusion created in 2020). Only the 2010–2014 rows are used for the Guillaume measure.
- **800406**: the label in its last edition (PLF 2019, 'gazole non routier pour le ferroviaire') differs from the Guillaume label (pure vegetable oils): possible code reuse, not resolved.
- **570101, 570102**: no successor code in the 2020–2026 panel; no 2024–2026 measure cites CGI art. 809/810.
- **800207, 800208, 800102, 800101**: renumbered, no successor found (editions checked: PLF 2019; PLF 2020 pp.30–31 and the concordance tables; PLF 2021 pp.33–35). Censored at 2019.
