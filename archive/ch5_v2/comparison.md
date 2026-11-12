# Chapter 5 terminations — v2 compared with the chapter and the recount

Rules used: population = **recount rule** (open in 2011 if the 2011 edition gives no end date or an end ≥ 2011), minus 180104, 320111, 140124. Dating rule = **effective year of termination**: for end-date closures, the end of eligibility in the latest edition in which the measure appears (an end in 2026 or later = censored at 2026); for the two hand-coded repeals, the effective year (300112: 2012; 800206: 2020). Real terminations only: exits from the annex without an end date are censored at their last annex year unless hand-coded as a repeal. Renumbered measures are followed through their successor code. Time origin 2011; terminations dated 2011 get duration 0.01.

## 1. Termination shares by Guillaume score

| score | chapter (n, share) | recount n | v2 main (n, terminated, share) | v2 without the 19 | v2 without the 3 uncoded | v2 chapter rule |
|---|---|---|---|---|---|---|
| 0 | 99, 52% | 99 | 99, 46, 46% | 92, 39, 42% | 98, 46, 47% | 99, 42, 42% |
| 1 | 86, 47% | 81 | 81, 35, 43% | 79, 33, 42% | 81, 35, 43% | 86, 37, 43% |
| 2 | 45, 29% | 45 | 45, 12, 27% | 45, 12, 27% | 44, 12, 27% | 45, 12, 27% |
| 3 | 61, 20% | 61 | 61, 14, 23% | 60, 13, 22% | 61, 14, 23% | 61, 14, 23% |
| not scored | 100, 41% | 108 | 105, 37, 35% | 96, 28, 29% | 104, 37, 36% | 97, 29, 30% |

The 19 measures whose latest end is ≤ 2011 are terminated in 2011. 10 of them are flagged by the 2011-end dummy.

## 2. Cox model, score per point (scored measures only)

| model | HR (95% CI) | p | N | events | dummy |
|---|---|---|---|---|---|
| main | 0.729 (0.607–0.875) | 0.0007 | 286 | 107 |  |
| main + 2011-end dummy | 0.719 (0.598–0.864) | 0.0004 | 286 | 107 | dummy HR 5.451, p = 0.0 |
| main without 3 uncoded | 0.728 (0.607–0.874) | 0.0006 | 284 | 107 |  |
| main without 3 uncoded + 2011-end dummy | 0.724 (0.603–0.870) | 0.0006 | 284 | 107 | dummy HR 5.974, p = 0.0 |
| main without the 19 | 0.755 (0.625–0.912) | 0.0035 | 276 | 97 |  |
| chapter rule | 0.768 (0.640–0.922) | 0.0047 | 291 | 105 |  |
| chapter rule + 2011-end dummy | 0.761 (0.633–0.914) | 0.0035 | 291 | 105 | dummy HR 4.268, p = 0.0001 |

Reference values: chapter HR **0.69 (0.58–0.83)**; independent recount HR **0.825 (0.693–0.982), N 286, 105 events**.

- **v2 vs the recount.** v2 has the same N (286 scored measures: the recount rule, and the 3 dropped measures are not scored). v2 has 107 events against 105. The recount (*Untitled9*, cell 5) also differs in three ways: (a) it counts as events only end dates in 2012–2025 and treats an end of 2011 as censored at 2026, where v2 terminates those measures in 2011; (b) it treats 800206 (score 1, repealed 2020) as censored at its last annex year, where v2 counts it as an event; (c) it controls for households, log cost, no cost estimate, age and income tax. Its HR is the adjusted one, so it is not directly comparable with the unadjusted v2 HR.
- **v2 vs the chapter.** The chapter HR (0.69) is stronger than any v2 specification; the chapter-rule v2 gives 0.768. The chapter code's event definition counts every exit from the annex as a termination (see §4). That inflates events most among the measures that were reclassified or renumbered.

## 3. 2011-end dummy (2011 edition gives an end of eligibility in 2011)

Under the recount rule: score 0: 4, score 1: 7, score 2: 2, score 3: 2, not scored: 8 — total 23 (15 scored, used in the Cox models).

## 4. Measures that switch from terminated (chapter code) to censored (v2)

Main population, measures in both populations: **56** switch. By score: 0: 13, 1: 7, 2: 7, 3: 9, not scored: 20. No measure switches the other way.

| reason in v2 | 0 | 1 | 2 | 3 | not scored | total |
|---|---|---|---|---|---|---|
| hand-coded: still in force | 2 | 0 | 1 | 0 | 0 | 3 |
| reclassified, censored at exit | 3 | 1 | 0 | 6 | 11 | 21 |
| renumbered, no successor, censored at exit | 3 | 0 | 2 | 0 | 0 | 5 |
| still listed in 2026 | 4 | 6 | 3 | 3 | 8 | 24 |
| uncoded exit, censored at exit | 1 | 0 | 1 | 0 | 1 | 3 |
| total | 13 | 7 | 7 | 9 | 20 | 56 |

On the chapter population (robustness), 61 switch: 0: 17, 1: 8, 2: 7, 3: 9, not scored: 20.
'still listed in 2026' under a chapter closure: the latest *dated* edition gave an end in 2012–2026, but the latest edition gives no end date or an end of 2026. Under the chapter rule's own dating (end 2026 = terminated), part of these would stay terminated.

## 5. Why group sizes differ (chapter 86/100 vs recount 81/108 for score 1 / not scored)

No measure has a different score in the two counts: both use `guillaume_all.csv`, which has no duplicate codes. The difference is the definition of 'open in 2011':
- chapter code: drop a measure if the end date in the **latest dated edition** is ≤ 2011;
- recount: keep a measure if the **2011 edition** gives no end date or an end ≥ 2011.
16 measures are only in the chapter population. The 2011 edition gives an end before 2011, which later editions extended; 7 of them have score 1. 19 are only in the recount population: the 2011 edition gives an end of 2011 or none, and a later edition dates the end at or before 2011; 2 have score 1 (140201, 230204) and 9 are not scored. Score 1: 86 − 7 + 2 = 81. Not scored: 100 − 1 + 9 = 108.

### The score-1 measures kept only under the chapter rule (not changed; for your decision)

You asked for 5. The net difference is 5, but 7 measures are involved: 7 leave and 2 enter.

| code | end_2011_edition | later_annexes | latest_end | outcome_under_chapter_rule | name |
|---|---|---|---|---|---|
| 110218 | 2010 | 2012–2026 (15 editions) | non borné | censored 2026 | Réduction d'impôt au titre de la souscription de parts de fonds communs de place |
| 110240 | 2010 | 2012–2026 (15 editions) | 2027 | censored 2026 | Crédit d'impôt au titre des dépenses engagées par les exploitants agricoles pour |
| 130204 | 1999 | 2012–2026 (15 editions) | 2025 | terminated 2025 | Déduction dégressive sur les revenus des logements neufs loués à usage d'habitat |
| 130208 | 2009 | 2012–2026 (15 editions) | 2025 | terminated 2025 | Déduction dégressive sur les revenus des logements loués à usage d'habitation pr |
| 130209 | 2003 | 2012–2026 (15 editions) | 2025 | terminated 2025 | Déduction dégressive sur les revenus des logements neufs loués à usage d'habitat |
| 130214 | 2009 | 2012–2026 (15 editions) | 2025 | terminated 2025 | Déduction spécifique sur les revenus des logements neufs à usage d'habitation pr |
| 230602 | 2010 | 2012–2026 (15 editions) | 2027 | censored 2026 | Exonération totale ou partielle des bénéfices réalisés par les entreprises nouve |

## 6. Reclassified (19) and renumbered (12) measures from `exits_to_code_v2.csv`

| exit_type | treatment | 0 | 1 | 2 | 3 | not scored | total |
|---|---|---|---|---|---|---|---|
| reclassified | censored 2012 | 1 | 0 | 0 | 2 | 2 | 5 |
| reclassified | censored 2019 | 2 | 1 | 0 | 4 | 7 | 14 |
| renumbered | censored 2019 | 3 | 0 | 2 | 0 | 0 | 5 |
| renumbered | followed via successor; censored 2026 | 2 | 2 | 2 | 1 | 0 | 7 |

| code | exit_type | score | last_annex | treatment |
|---|---|---|---|---|
| 300104 | reclassified | 0 | 2019 | censored 2019 |
| 730220 | reclassified | 0 | 2019 | censored 2019 |
| 960102 | reclassified | 0 | 2012 | censored 2012 |
| 730219 | reclassified | 1 | 2019 | censored 2019 |
| 250101 | reclassified | 3 | 2019 | censored 2019 |
| 560104 | reclassified | 3 | 2012 | censored 2012 |
| 730203 | reclassified | 3 | 2019 | censored 2019 |
| 730303 | reclassified | 3 | 2019 | censored 2019 |
| 740106 | reclassified | 3 | 2019 | censored 2019 |
| 960101 | reclassified | 3 | 2012 | censored 2012 |
| 060101 | reclassified | not scored | 2012 | censored 2012 |
| 100112 | reclassified | not scored | 2019 | censored 2019 |
| 120307 | reclassified | not scored | 2019 | censored 2019 |
| 120308 | reclassified | not scored | 2019 | censored 2019 |
| 160102 | reclassified | not scored | 2019 | censored 2019 |
| 190101 | reclassified | not scored | 2019 | censored 2019 |
| 560103 | reclassified | not scored | 2012 | censored 2012 |
| 730204 | reclassified | not scored | 2019 | censored 2019 |
| 730215 | reclassified | not scored | 2019 | censored 2019 |
| 800115 | renumbered | 0 | 2019 | censored 2019 |
| 800207 | renumbered | 0 | 2019 | censored 2019 |
| 800208 | renumbered | 0 | 2019 | censored 2019 |
| 800302 | renumbered | 0 | 2026 | followed via 800228; censored 2026 |
| 800404 | renumbered | 0 | 2026 | followed via 800222; censored 2026 |
| 700102 | renumbered | 1 | 2026 | followed via 720207; censored 2026 |
| 800403 | renumbered | 1 | 2026 | followed via 800221; censored 2026 |
| 220103 | renumbered | 2 | 2026 | followed via 230605; censored 2026 |
| 800101 | renumbered | 2 | 2019 | censored 2019 |
| 800102 | renumbered | 2 | 2019 | censored 2019 |
| 800103 | renumbered | 2 | 2026 | followed via 800220; censored 2026 |
| 800114 | renumbered | 3 | 2026 | followed via 840101; censored 2026 |

Renumbered without a successor (censored at exit): 800207 (score 0), 800208 (0), 800102 (2), 800101 (2), all last listed in PLF 2019. Editions checked: PLF 2019; PLF 2020 pp.30–31 (only 210204→200401 and 210205→200402) and the concordance tables; PLF 2021 pp.33–35 (twelve renumberings, none of these). 800115 (0) is coded renumbered but PLF 2020 p.31 lists it as declassified; it is censored at 2019 either way. In the 2020 edition, the closest labels are 800217 (for 800207) and 800203 (for 800208), but no annex table links them, so they were **not linked**.

## 7. Remaining uncoded exits

`exits_to_code_v2.csv`: **none** — its only uncoded rows were the 11, all now coded in `exits_coded_11_v2.csv`.
Under v2's dating rule, three more measures leave the annex without an end date. They are in both populations, but the chapter code counted them as closures from an end date in an earlier edition. They are censored at their last annex year for now (`uncoded_exits.csv`):

| code | score | last_annex | description_guillaume | article_reference | chapter_code_outcome |
|---|---|---|---|---|---|
| 140110 | Non évalué | 2020 | Exonération des intérêts des livrets d'épargne entreprise | 157-9° quinquies | terminated 2013 (via end date in an earlier edition) |
| 800406 | 0 | 2019 | Autorisation à titre expérimental de l'usage des huiles végétales pures (HVP) comme carburant pour les flottes captives des collectivités locales ou de leurs groupements ayant signé avec l'Etat un protocole permettant d'encadrer cet usage à un taux réduit | not recorded in the annex panel | terminated 2015 (via end date in an earlier edition) |
| 800109 | 2 | 2019 | Exonération de taxe intérieure de consommation pour les produits énergétiques utilisés comme carburant ou combustible à bord des aéronefs, à l'exclusion des aéronefs de tourisme privé | Code des douanes 265 bis-1-b | terminated 2012 (via end date in an earlier edition) |

800406: the label in its last edition is 'gazole non routier pour le ferroviaire', not the Guillaume label (possible code reuse).

## Files

- `exits_coded_11_v2.csv`, `termination_dataset_v2.csv` (main), `termination_dataset_v2_chapter_rule.csv` (robustness)
- `termination_shares_by_score.csv`, `cox_score_per_point_v2.csv`, `km_termination_by_score_v2.png`
- `uncoded_exits.csv`, `CHANGELOG.md`, `build_termination_v2.py`, `write_reports.py`
