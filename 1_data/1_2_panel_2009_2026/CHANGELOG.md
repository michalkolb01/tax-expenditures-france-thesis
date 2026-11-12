# CHANGELOG — Chapter 5 termination dataset, v3.5 (frozen)

This file documents `build_termination_v35.py`, the build used in the thesis
(`tables/termination_dataset_v35.csv`, 379 measures). It is written from the code;
every parameter and hand-coded case below is a constant of that script. The
earlier v2 build and its reports are in `archive/ch5_v2/` (not used in the thesis).

## 1. Population rule (`POPULATION_RULE = "recount"`)

A measure of the 2011 report (`guillaume_all.csv`, 470 measures) is followed if:

1. it has a six-digit code (449 of 470; the 21 unnumbered measures cannot be traced in the annex);
2. it is listed in the 2011 edition of the *Voies et moyens* annex, with **no end date or an end date of 2011 or later** in that edition;
3. it is not dropped by hand as ended before 2011 (180104, 320111, 140124);
4. it was not declassified (removed from the list of tax expenditures) in PLF 2011 or earlier;
5. its latest reported end date (after the freeze rule, §3) is not before 2011.

Result: 379 measures, 278 scored (95 / 81 / 42 / 60 for scores 0–3) and 101 not scored.
The 91 excluded measures and their reasons are in `termination_panel_by_year.xlsx` (this folder), sheet `Excluded`.
The alternative `"chapter"` rule (robustness, `termination_dataset_v35_chapter_rule.csv`) keeps
numbered measures listed at least once in 2011–2026 and drops those whose latest dated end is ≤ 2011 (377 measures).

## 2. Event: termination = closure to new beneficiaries

A measure is terminated when it closes to new beneficiaries, by one of two routes
(column `mechanism`, grouped as in the chapter):

* **End date recorded in the annex** (`end_date_unverified`, `sunset`): the annex gives an end of the
  qualifying event (*fin du fait générateur*) before 2026. 111 terminations.
* **Suppression by law** (`repeal`, `underlying_tax_reform`, `external`): a repeal or suppression
  identified by hand with its legal basis (tables below). 26 terminations.

### Two columns: `mechanism` and `basis`

* **`mechanism`** says **how the measure ended**. It is set by hand for every audited case
  (`MECHANISM`, `AUDIT_DECISIONS` and `DECISIONS_11` below): `repeal`, `sunset`,
  `underlying_tax_reform`, `external` (and `scope_change` for censored exits). For terminations not
  audited by hand it takes the default value **`end_date_unverified`**: the annex records an end
  date, but how the measure ended was not checked against the law. The chapter reports this
  grouping (111 end dates / 26 suppressions), because it describes how measures ended.
* **`basis`** says **where the termination year comes from**: the end date in the latest annex
  edition, an end date frozen at the first reported closure (§3), or a hand-coded decision with its
  effective year.

The two do not coincide: ten measures coded `repeal` (and two coded `underlying_tax_reform`) take
their year from the annex end date. Cross-tabulation of the 137 terminations
(`2_methods/2_1_survival_analysis/tables/route_by_basis.csv`):

| route (from `mechanism`) | `mechanism` | end date in latest edition | end date frozen at first closure | hand-coded | total |
|---|---|---|---|---|---|
| end date recorded in the annex | end_date_unverified | 102 | 7 | 0 | 109 |
| end date recorded in the annex | sunset | 0 | 0 | 2 | 2 |
| suppression by law | repeal | 10 | 0 | 12 | 22 |
| suppression by law | underlying_tax_reform | 2 | 0 | 1 | 3 |
| suppression by law | external | 0 | 0 | 1 | 1 |
| **total** | | **114** | **7** | **16** | **137** |

Grouped by `mechanism`: 111 / 26 (the chapter). Grouped by `basis`: 121 / 16.

## 3. Dating rule (`DATING_RULE = "effective_year"`)

* End-date closures are dated by the **last year of eligibility** in the latest annex edition in which the measure appears.
* **Freeze rule** (v3.1, tightened in v3.2): once at least **two consecutive editions** published after the end year
  report the measure as already closed, later editions that push the end date further out are ignored
  (re-dating of a closed measure, or revival after a gap). A single stale edition is treated as a
  publication lag. An edition that reports the measure as open (*non borné*) resets the count.
  13 measures have a frozen end date (`tables/frozen_end_dates_v35.csv`).
* Hand-coded repeals are dated by the year the repeal **takes effect** (first closed year). The script
  notes this asymmetry (end dates = last open year; repeals = first closed year), inherited from v2;
  `DATING_RULE = "first_closed_year"` would align both. The thesis uses `effective_year`.
* Time origin 2011 (`ORIGIN`); window ends 2026 (`WINDOW_END`); terminations dated 2011 get duration 0.01 (`T0_EPS`).
* `sched_end_2011` = 1 when the 2011 edition already gave an end in 2011 (13 scored measures).

## 4. Censoring rules

* Still listed in 2026, or end date ≥ 2026 → censored 2026.
* Declassified during the window (PLF 2019 annex list, plus `DECLASSIFIED_EXTRA`) → censored the year before declassification.
* Left the annex without an end date: reclassified or renumbered without a successor → censored at the last annex year.
* Renumbered with an official successor (`LINKS`) → followed through the successor code.
* Hand-coded `censored_2026` (still in force) and `censored_exit` (reclassified) cases: tables below.
* A measure that leaves the annex with no coding rule raises an error (no silent default).

## 5. Hand-coded cases (from the code)

### Hand-coded decisions (DECISIONS_11 + AUDIT_DECISIONS)

| code | score | decision | year | mechanism | legal basis | note | outcome in v3.5 |
|---|---|---|---|---|---|---|---|
| 300112 | not scored | terminated (v2 (11 exits)) | 2012 | repealed | Loi n° 2011-1978 (LFR 2011), art. 65 |  | terminated 2012 |
| 800206 | 1 | terminated (v2 (11 exits)) | 2020 | repealed | Loi n° 2019-1479 (LF 2020), art. 60; effective 1 July 2020 |  | terminated 2020 |
| 700101 | 0 | censored_2026 (v2 (11 exits)) |  | still_in_force |  |  | censored 2026 |
| 720202 | 2 | censored_2026 (v2 (11 exits)) |  | still_in_force |  |  | censored 2026 |
| 920301 | 0 | censored_2026 (v2 (11 exits)) |  | still_in_force |  | code reused from PLF 2020 for a different measure (TOCE exclusion); only 2010-2014 rows belong to the Guillaume measure | censored 2026 |
| 180104 |  | drop (v2 (11 exits)) |  | ended_before_2011 |  |  | dropped |
| 320111 |  | drop (v2 (11 exits)) |  | ended_before_2011 |  |  | dropped |
| 140124 |  | drop (v2 (11 exits)) |  | ended_before_2011 |  |  | dropped |
| 730307 | not scored | linked (v2 (11 exits)) |  | renumbered |  |  | censored 2026 |
| 570101 | not scored | censored_exit (v2 (11 exits)) |  | reclassified |  | declassified PLF 2024 p.33; no successor code in the 2020-2026 panel (no measure cites CGI art. 809/810); censored at last annex year | censored 2023 |
| 570102 | not scored | censored_exit (v2 (11 exits)) |  | reclassified |  | declassified PLF 2024 p.33; no successor code in the 2020-2026 panel (no measure cites CGI art. 809-I bis); censored at last annex year | censored 2023 |
| 140110 | not scored | terminated (v3 audit) | 2014 | repeal | CGI art. 157 9° quinquies abrogé from 01/01/2014 (LF 2014, loi n° 2013-1278) | v2: uncoded exit, censored 2020 | terminated 2014 |
| 800406 | 0 | terminated (v3 audit) | 2016 | repeal | HVP rate pegged to art. 265 bis A reduction; 265 bis A abrogé from 01/01/2016 (LF 2014, art. 34); PLF 2017 lists it as non-TE | v2: uncoded exit, censored 2019 (code reused from 2018 for railway diesel) | terminated 2016 |
| 060101 | not scored | terminated (v3 audit) | 2011 | underlying_tax_reform | Departmental and regional TFNB shares abolished from 2011 (LF 2010, loi n° 2009-1673); CGI 1586 D / 1599 ter D | v2: reclassified, censored 2012 | terminated 2011 |
| 120307 | not scored | terminated (v3 audit) | 2017 | repeal | CGI art. 83 bis abrogé by LF 2014 (loi n° 2013-1278), art. 26 I-j, effective 01/01/2017 | v2: reclassified, censored 2019 | terminated 2017 |
| 300104 | 0 | terminated (v3 audit) | 2018 | external | European Commission decision C(2017) 5176 final; doctrine withdrawn BOI-IS-CHAMP-30-60-20171206 | v2: reclassified, censored 2019 | terminated 2018 |
| 560104 | 3 | terminated (v3 audit) | 2011 | repeal | LF 2011 (loi n° 2010-1657): exemption replaced by 3.5% rate; LFR 2011 (loi n° 2011-1117), art. 9: reduced rate abolished 01/10/2011 | v2: reclassified, censored 2012 | terminated 2011 |
| 230405 | 1 | terminated (v3 audit) | 2014 | repeal | CGI art. 39 ter B abrogé by LF 2014 (loi n° 2013-1278), art. 26 I-f; last version in force until 01/01/2014 | v2: end date 2012 | terminated 2014 |
| 110250 | 1 | terminated (v3 audit) | 2022 | sunset | Censi-Bouvard reduction (CGI 199 sexvicies) open to new investments until 31/12/2022; PLF 2024 fiche: fin du fait générateur 2022 | v3: end date 2025 (PLF 2025/2026 re-dated the closed measure; only one edition reported the closure, so the generic freeze rule did not apply) | terminated 2022 |
| 120116 | 0 | terminated (v3 audit) | 2026 | repeal | CGI art. 157 6° abrogé by LF 2026 (loi n° 2026-103 du 19 février 2026), art. 17, I-5° (art. 5 of the PLF), from 2026 income | v3.2: end 2024 (PLF 2026 fiche reflecting the proposal) | terminated 2026 |
| 110215 | 0 | censored_2026 (v3 audit) |  |  |  | abolition proposed in PLF 2026 art. 5 but not in the final LF 2026 (art. 17 of loi n° 2026-103 does not touch CGI 199 quater F); still in force | censored 2026 |
| 110242 | 1 | censored_2026 (v3 audit) |  |  |  | abolition proposed in PLF 2026 art. 5 but not in the final LF 2026 (art. 17 of loi n° 2026-103 does not touch CGI 199 quater F); still in force | censored 2026 |
| 120104 | 0 | terminated (v3 audit) | 2026 | repeal | CGI art. 81-7° abrogé by LF 2026 (loi n° 2026-103), art. 17 I-3° | v3.3: end 2024 from the PLF 2026 fiche | terminated 2026 |
| 120129 | not scored | terminated (v3 audit) | 2026 | repeal | CGI art. 81-35° abrogé by LF 2026 (loi n° 2026-103), art. 17 I-3° | v3.3: end 2024 from the PLF 2026 fiche | terminated 2026 |
| 160303 | not scored | terminated (v3 audit) | 2026 | repeal | CGI art. 93-1-5° abrogé by LF 2026 (loi n° 2026-103), art. 17 I-4°, in force 01/01/2026 | v3.3: end 2024 from the PLF 2026 fiche | terminated 2026 |
| 120204 | 0 | censored_2026 (v3 audit) |  |  |  | abolition proposed in PLF 2026 but not in LF 2026 (CGI 80 quinquies untouched); still in force | censored 2026 |
| 160201 | 0 | censored_2026 (v3 audit) |  |  |  | abolition proposed in PLF 2026 but not in LF 2026 (CGI 92 A untouched); still in force | censored 2026 |
| 740102 | 2 | censored_2026 (v3 audit) |  |  |  | specific franchise still in force: CGI 293 B I bis (loi n° 2025-1044); recodified into the CIBS from 2027 (ordonnance n° 2025-1247), outside window | censored 2026 |
| 740103 | 2 | censored_2026 (v3 audit) |  |  |  | specific franchise still in force: CGI 293 B I bis (loi n° 2025-1044); recodified into the CIBS from 2027 (ordonnance n° 2025-1247), outside window | censored 2026 |
| 060105 | 0 | terminated (v3 audit) | 2026 | repeal | CGI art. 1395 B bis III, added by LF 2026 (loi n° 2026-103), art. 17 I-20°: exemption limited to commitments filed before the law's entry into force | closed to new beneficiaries in 2026; existing 5-year commitments run off. 1395 D (abrogé LF 2014, art. 26) was recodified as 1395 B bis: continuous measure | terminated 2026 |
| 920202 | 3 | terminated (v3 audit) | 2011 | sunset | CGI art. 302 bis KG: reduced rate for non-analogue services fixed for 2009-2011 only (loi n° 2009-258, art. 32; LF 2011) | v2: end date 2014 (= last annex year) | terminated 2011 |

### Links to a successor code (LINKS)

| code | successor | source |
|---|---|---|
| 730307 | 710110 | VM PLF 2021 p.33 |
| 220103 | 230605 | VM PLF 2013 p.28 |
| 700102 | 720207 | VM PLF 2021 p.33 |
| 800103 | 800220 | VM PLF 2021 p.34 |
| 800403 | 800221 | VM PLF 2021 p.34 |
| 800404 | 800222 | VM PLF 2021 p.34 |
| 800302 | 800228 | VM PLF 2021 p.34 |
| 800114 | 840101 | VM PLF 2021 p.34 |
| 800207 | 800217 | duplicate codes for the same measure 2017-2019 (customs code art. 265, table B, index 36); not in an official renumbering table |
| 200309 | 230606 | VM PLF 2015, « Reclassement par renumérotation » |
| 110214 | 110246 | reduction merged into the universal tax credit from 2017 (decision 3: advantage continued) |
| 730204 | 730210 | decision 3: 5.5% -> 10% from 01/01/2018 (LF 2018, art. 12) is a partial cut, not a termination; residual 10% rate covered by 730210 |

### Renumbered without a linked successor (UNLINKED_RENUMBERED)

| code | note |
|---|---|
| 800208 | silent drop in PLF 2020; reduced rate still in force (art. 265 version 31/12/2020) |
| 800115 | PLF 2020 p.31 lists it as DECLASSIFIED, not renumbered; censored at exit |

### Codes reused for a different measure (ROW_CUTOFF: only rows up to this edition)

| code | last edition used |
|---|---|
| 920301 | 2014 |
| 800406 | 2016 |

### Freeze-rule exceptions (FREEZE_EXCEPTIONS)

| code | reason |
|---|---|
| 210313 | old PTZ ended 2010, replaced on 01/01/2011 by PTZ+ under the same code; stale '2010' in early editions refers to the old PTZ |

### Mechanism set by hand for audited end-date cases (MECHANISM)

| code | mechanism |
|---|---|
| 300112 | repeal |
| 800206 | repeal |
| 210306 | repeal |
| 120114 | repeal |
| 140201 | repeal |
| 120136 | repeal |
| 920201 | repeal |
| 150711 | repeal |
| 120301 | repeal |
| 120507 | repeal |
| 160103 | repeal |
| 210311 | repeal |
| 170501 | underlying_tax_reform |
| 970101 | underlying_tax_reform |
| 560103 | scope_change |
| 960101 | scope_change |
| 960102 | scope_change |

### Declassified measures added beyond the PLF 2019 list (DECLASSIFIED_EXTRA)

| code | PLF of declassification |
|---|---|
| 800115 | 2020 |
| 570101 | 2024 |
| 570102 | 2024 |
| 730203 | 2020 |
| 730215 | 2020 |
| 730219 | 2020 |
| 730220 | 2020 |
| 730303 | 2020 |
| 740106 | 2020 |

The PLF 2019 declassification list (DECLASSIFIED) has 80 codes; see the script.

## 6. Differences from v2 (`archive/ch5_v2/`)

| | v2 | v3.5 |
|---|---|---|
| Population | 391 (99 / 81 / 45 / 61 scored, 105 not scored) | 379 (95 / 81 / 42 / 60, 101) |
| Terminations | 144 (46 / 35 / 12 / 14 / 37) | 137 (41 / 33 / 10 / 15 / 38) |
| Cox, score per point | 0.729 (0.607–0.875), N 286, 107 events | 0.773 (0.642–0.930), N 278, 99 events |

Changes, in the order they were made (from the script's header):

* **v3** (primary-source audit): measures declassified before the window are excluded and those declassified
  during it censored the year before; measures whose latest end date precedes 2011 are excluded (v2 moved them
  to a 2011 event, e.g. 230303); audit decisions hand-coded (`AUDIT_DECISIONS`); new links 800207 → 800217
  and 730204 → 730210; 800406 uses only rows up to PLF 2016 (code reused); new column `mechanism`; the three
  exits left uncoded in v2 (140110, 800406, 800109; `data/uncoded_exits.csv`) are now coded.
* **v3.1**: frozen end dates (late re-dating of closed measures ignored: 110250, 110251, 110252, 130211;
  revived measures 150118, 150119, 200216 terminated at their first closure); six reduced VAT rates
  declassified in PLF 2020 added to the declassification list (outcome unchanged); linked series whose
  successor leaves the annex without an end date labelled as such; random check sample of 20.
* **v3.2**: freeze only after ≥ 2 consecutive closed editions (fixes false freezes of 060105, 110215,
  110242, 090201); 210313 (PTZ → PTZ+) exempted from the freeze; 110250 hand-coded to its 2022 closure.
* **v3.3**: 200309 linked to 230606; 110214 linked to 110246; 110215 and 110242 censored 2026 (abolition
  proposed in PLF 2026 but not in the final LF 2026); 120116 terminated 2026 (LF 2026, art. 17).
* **v3.4**: the eight measures whose end date appeared only in PLF 2026 checked against LF 2026 (loi
  n° 2026-103): 120104, 120129, 160303 terminated 2026; 120204, 160201, 740102, 740103 censored 2026; 070201 unchanged.
* **v3.5**: 060105 terminated 2026 (closed to new beneficiaries by LF 2026, art. 17 I-20°). Frozen.

`data/exits_coded_11_v2.csv` documents the 11 exits coded by hand in v2 (`DECISIONS_11`, unchanged in
v3.5); `data/exits_to_code_v2.csv` is the exit-type list read by the script.
