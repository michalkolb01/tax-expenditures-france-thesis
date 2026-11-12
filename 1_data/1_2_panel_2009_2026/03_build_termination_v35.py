# Replication package - Chapter 5, step 1: build the termination dataset (v3.5, frozen).
# Inputs : data/intermediate/vm_2009_2019.parquet, vm_2020_2026.parquet (1_data/1_2_panel_2009_2026/),
#          data/intermediate/guillaume_all.csv (1_data/1_1_evaluation_2011/), 1_data/1_2_panel_2009_2026/data/exits_to_code_v2.csv
# Outputs: tables/termination_dataset_v35.csv (379 measures, the chapter's dataset; also
#          copied to data/intermediate/), _chapter_rule.csv, shares, Cox per point, diagnostics.
# Reproduces: 379 measures (95/81/42/60 scored, 101 not scored); terminations 41/33/10/15/38 (137);
#          Cox HR 0.773 (0.642-0.930), p = 0.0064. Rules and hand-coded cases: 1_data/1_2_panel_2009_2026/CHANGELOG.md.
"""Chapter 5 termination dataset, v3.5 (FROZEN) — v3.4 + 060105.

v3.5 (10 Nov 2026): 060105 (TFNB exemption for wetlands, CGI 1395 B bis) closed to new
beneficiaries by LF 2026 (loi n° 2026-103), art. 17 I-20°: new III limits the exemption to
owners who filed the management commitment before the law entered into force; existing
commitments run off. Terminated 2026 (repeal, decision 2: closure to new beneficiaries).
This is the frozen dataset for Chapter 5.

v3.4 — v3.3 + PLF 2026 proposal-risk cases settled.

v3.4 (10 Nov 2026): the 8 measures whose end date appears only in PLF 2026 were checked
against LF 2026 (loi n° 2026-103, art. 17) and the CGI in force on 10/11/2026:
  - 120104 (CGI 81-7°), 120129 (CGI 81-35°): abrogated, LF 2026 art. 17 I-3°: terminated
    2026 (repeal).
  - 160303 (CGI 93-1-5°): abrogated, LF 2026 art. 17 I-4°, from 01/01/2026: terminated
    2026 (repeal).
  - 120204 (CGI 80 quinquies, IJ ALD), 160201 (CGI 92 A, Nobel): proposed in PLF 2026 but
    not in the final law; still in force: censored 2026.
  - 740102, 740103 (VAT franchise for lawyers and authors): specific franchise still in
    force (CGI 293 B I bis, as amended by loi n° 2025-1044); recodified into the CIBS from
    2027 (ordonnance n° 2025-1247), outside the window: censored 2026.
  - 070201: repealed by LF 2025 amendment (PLF 2026 « Suppressions votées »): unchanged.

v3.3 — v3.2 + corrections from the round-2 check sample.

v3.3 (10 Nov 2026):
  - 200309 linked to 230606 (official renumbering, VM PLF 2015, renumbering table).
  - 110214 linked to 110246 (home-help reduction merged into the universal tax credit
    from 2017; advantage continued, decision 3).
  - 110215, 110242 (school-fee reductions): PLF 2026 proposed their abolition (art. 5)
    and the fiches show fin du fait générateur 2024, but the final LF 2026 kept them:
    censored 2026, not terminated.
  - 120116 (médaille du travail): abolished by LF 2026 (loi n° 2026-103), art. 17, I-5°, from
    2026 income: terminated 2026 (v3.2: 2024 from the PLF 2026 fiche).
  - New diagnostic: terminations whose end date first appears in the latest edition
    (proposal risk: the PLF fiche may reflect a suppression not yet voted).

v3.2 — v3.1 with a stricter freeze rule.

v3.2 update: 210313 (PTZ -> PTZ+, seamless replacement) exempted from the freeze rule
(it was wrongly dropped from the population); 110250 (Censi-Bouvard) hand-coded to its
2022 closure; frozen-date log now includes freezes that affect the population filter.

v3.2: an end date is frozen only after >= 2 consecutive editions published after the
end year report the measure as closed (a single stale edition = publication lag,
e.g. retroactive extension); an edition explicitly reporting the measure as open
('non borné') resets the count. Fixes false freezes in v3.1 (060105, 110215, 110242,
090201). The frozen-date table now prints the edition sequence for review.

v3.1 — v3 + fixes from the v3 diagnostics.

Changes from v3 (10 Nov 2026):
  a. Frozen end dates: once an annex edition reports a measure as already closed
     (end year before the edition's publication), later editions that push the end date further out
     are ignored. Fixes late re-dating of long-closed measures (110250, 110251,
     110252, 130211: closed 2012-2022, re-dated 2025 in PLF 2024/2026) and codes
     revived measures as terminated at their first closure (150118, 150119,
     200216: ended 2011, re-created later; decision of the project owner).
  b. The six reduced VAT rates declassified in PLF 2020 (Cour des comptes, NEB 2019)
     are added to the declassification list (label fix, outcome unchanged).
  c. Linked series whose successor leaves the annex without an end date are
     labelled as such (800207 -> 800217, GNV rate dropped silently in PLF 2021).
  d. Draws a random check sample of 20 unaudited terminations (seed 2027).

Earlier changes (v3, primary-source audit):

Changes from v2 (audit of 10 Nov 2026, audit_classification_TEs.xlsx):
  1. Measures declassified before the window (PLF de déclassement <= ORIGIN) are
     excluded; measures declassified during the window are censored at the year
     before declassification (list: PLF 2019 VM II annex « modalités de calcul »).
  2. Measures whose latest reported end date precedes ORIGIN are excluded
     (closed before the window; v2 moved them to a 2011 event, e.g. 230303).
  3. Audit corrections hand-coded in AUDIT_DECISIONS (terminations coded as
     censored in v2, wrong years) and two new links (800207, 730204).
  4. 800406: only rows up to PLF 2016 belong to the Guillaume measure (code
     reused from 2018 for a different measure).
  5. New column `mechanism` (sunset | repeal | underlying_tax_reform |
     scope_change | external | end_date_unverified); audited cases hand-coded.
  6. Diagnostics: unaudited rows showing the error patterns found in the audit;
     change log v2 -> v3.

Writes to OUT (results_ch5_v31/); v3 outputs are read only for the change log.
Run in Colab (Drive mounted) or locally with DATA set below.
Requires: pandas, pyarrow, lifelines, matplotlib.
"""
# ============================================================================
# PARAMETERS
# ============================================================================
# Dating rule for terminations.
#   "effective_year" (default): for end-date closures, the last year of
#       eligibility given in the latest annex edition in which the measure
#       appears; for hand-coded repeals, the year the repeal takes effect.
#   "first_closed_year": one year later for end-date closures.
# NOTE: under "effective_year", end-date closures are dated by the LAST open year
# and hand-coded repeals by the FIRST closed year (convention inherited from v2,
# e.g. 300112). See the README line printed at the end.
DATING_RULE = "effective_year"

WINDOW_END = 2026
ORIGIN = 2011                    # year of the Guillaume report = time 0
T0_EPS = 0.01                    # duration used for terminations in 2011 (t=0)

# Population rule: "recount" (main) or "chapter" (robustness check).
POPULATION_RULE = "recount"

import sys
from pathlib import Path
# [replication package] Paths only: the original read everything from the Drive
# folder MT_replication/data and wrote to data/results_ch5_v35/. Inputs now come
# from data/intermediate/ (panel, Guillaume list) and 1_data/1_2_panel_2009_2026/data/ (exits_to_code_v2.csv);
# outputs go to tables/ in this folder. Nothing else in this file was changed.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import INTERMEDIATE                     # noqa: E402
DATA = INTERMEDIATE
OUT = HERE / "tables"
OUT.mkdir(parents=True, exist_ok=True)
V2_DIR = OUT / "v34"    # change log against v3.4: skipped when that file is absent

import re
import numpy as np
import pandas as pd

# ============================================================================
# HAND-CODED DECISIONS (from the project owner, 10 Nov 2026) — unchanged from v2
# ============================================================================
# status: terminated | censored_2026 | drop | linked | censored_exit
DECISIONS_11 = {
    "300112": dict(status="terminated", effective_year=2012,
                   legal_basis="Loi n° 2011-1978 (LFR 2011), art. 65",
                   exit_type="repealed"),
    "800206": dict(status="terminated", effective_year=2020,
                   legal_basis="Loi n° 2019-1479 (LF 2020), art. 60; effective 1 July 2020",
                   exit_type="repealed"),
    "700101": dict(status="censored_2026", exit_type="still_in_force"),
    "720202": dict(status="censored_2026", exit_type="still_in_force"),
    "920301": dict(status="censored_2026", exit_type="still_in_force",
                   note="code reused from PLF 2020 for a different measure (TOCE exclusion); "
                        "only 2010-2014 rows belong to the Guillaume measure"),
    "180104": dict(status="drop", exit_type="ended_before_2011"),
    "320111": dict(status="drop", exit_type="ended_before_2011"),
    "140124": dict(status="drop", exit_type="ended_before_2011"),
    "730307": dict(status="linked", exit_type="renumbered", link_to="710110"),
    "570101": dict(status="censored_exit", exit_type="reclassified",
                   note="declassified PLF 2024 p.33; no successor code in the 2020-2026 panel "
                        "(no measure cites CGI art. 809/810); censored at last annex year"),
    "570102": dict(status="censored_exit", exit_type="reclassified",
                   note="declassified PLF 2024 p.33; no successor code in the 2020-2026 panel "
                        "(no measure cites CGI art. 809-I bis); censored at last annex year"),
}

# ============================================================================
# AUDIT DECISIONS (primary-source audit, 10 Nov 2026) — NEW in v3
# ============================================================================
AUDIT_DECISIONS = {
    "140110": dict(status="terminated", effective_year=2014, mechanism="repeal",
                   legal_basis="CGI art. 157 9° quinquies abrogé from 01/01/2014 (LF 2014, loi n° 2013-1278)",
                   note="v2: uncoded exit, censored 2020"),
    "800406": dict(status="terminated", effective_year=2016, mechanism="repeal",
                   legal_basis="HVP rate pegged to art. 265 bis A reduction; 265 bis A abrogé from "
                               "01/01/2016 (LF 2014, art. 34); PLF 2017 lists it as non-TE",
                   note="v2: uncoded exit, censored 2019 (code reused from 2018 for railway diesel)"),
    "060101": dict(status="terminated", effective_year=2011, mechanism="underlying_tax_reform",
                   legal_basis="Departmental and regional TFNB shares abolished from 2011 "
                               "(LF 2010, loi n° 2009-1673); CGI 1586 D / 1599 ter D",
                   note="v2: reclassified, censored 2012"),
    "120307": dict(status="terminated", effective_year=2017, mechanism="repeal",
                   legal_basis="CGI art. 83 bis abrogé by LF 2014 (loi n° 2013-1278), art. 26 I-j, "
                               "effective 01/01/2017",
                   note="v2: reclassified, censored 2019"),
    "300104": dict(status="terminated", effective_year=2018, mechanism="external",
                   legal_basis="European Commission decision C(2017) 5176 final; doctrine withdrawn "
                               "BOI-IS-CHAMP-30-60-20171206",
                   note="v2: reclassified, censored 2019"),
    "560104": dict(status="terminated", effective_year=2011, mechanism="repeal",
                   legal_basis="LF 2011 (loi n° 2010-1657): exemption replaced by 3.5% rate; "
                               "LFR 2011 (loi n° 2011-1117), art. 9: reduced rate abolished 01/10/2011",
                   note="v2: reclassified, censored 2012"),
    "230405": dict(status="terminated", effective_year=2014, mechanism="repeal",
                   legal_basis="CGI art. 39 ter B abrogé by LF 2014 (loi n° 2013-1278), art. 26 I-f; "
                               "last version in force until 01/01/2014",
                   note="v2: end date 2012"),
    "110250": dict(status="terminated", effective_year=2022, mechanism="sunset",
                   legal_basis="Censi-Bouvard reduction (CGI 199 sexvicies) open to new investments until "
                               "31/12/2022; PLF 2024 fiche: fin du fait générateur 2022",
                   note="v3: end date 2025 (PLF 2025/2026 re-dated the closed measure; only one "
                        "edition reported the closure, so the generic freeze rule did not apply)"),
    "120116": dict(status="terminated", effective_year=2026, mechanism="repeal",
                   legal_basis="CGI art. 157 6° abrogé by LF 2026 (loi n° 2026-103 du 19 février 2026), "
                               "art. 17, I-5° (art. 5 of the PLF), from 2026 income",
                   note="v3.2: end 2024 (PLF 2026 fiche reflecting the proposal)"),
    "110215": dict(status="censored_2026", mechanism="",
                   note="abolition proposed in PLF 2026 art. 5 but not in the final LF 2026 "
                        "(art. 17 of loi n° 2026-103 does not touch CGI 199 quater F); still in force"),
    "110242": dict(status="censored_2026", mechanism="",
                   note="abolition proposed in PLF 2026 art. 5 but not in the final LF 2026 "
                        "(art. 17 of loi n° 2026-103 does not touch CGI 199 quater F); still in force"),
    "120104": dict(status="terminated", effective_year=2026, mechanism="repeal",
                   legal_basis="CGI art. 81-7° abrogé by LF 2026 (loi n° 2026-103), art. 17 I-3°",
                   note="v3.3: end 2024 from the PLF 2026 fiche"),
    "120129": dict(status="terminated", effective_year=2026, mechanism="repeal",
                   legal_basis="CGI art. 81-35° abrogé by LF 2026 (loi n° 2026-103), art. 17 I-3°",
                   note="v3.3: end 2024 from the PLF 2026 fiche"),
    "160303": dict(status="terminated", effective_year=2026, mechanism="repeal",
                   legal_basis="CGI art. 93-1-5° abrogé by LF 2026 (loi n° 2026-103), art. 17 I-4°, "
                               "in force 01/01/2026",
                   note="v3.3: end 2024 from the PLF 2026 fiche"),
    "120204": dict(status="censored_2026", mechanism="",
                   note="abolition proposed in PLF 2026 but not in LF 2026 (CGI 80 quinquies untouched); "
                        "still in force"),
    "160201": dict(status="censored_2026", mechanism="",
                   note="abolition proposed in PLF 2026 but not in LF 2026 (CGI 92 A untouched); "
                        "still in force"),
    "740102": dict(status="censored_2026", mechanism="",
                   note="specific franchise still in force: CGI 293 B I bis (loi n° 2025-1044); "
                        "recodified into the CIBS from 2027 (ordonnance n° 2025-1247), outside window"),
    "740103": dict(status="censored_2026", mechanism="",
                   note="specific franchise still in force: CGI 293 B I bis (loi n° 2025-1044); "
                        "recodified into the CIBS from 2027 (ordonnance n° 2025-1247), outside window"),
    "060105": dict(status="terminated", effective_year=2026, mechanism="repeal",
                   legal_basis="CGI art. 1395 B bis III, added by LF 2026 (loi n° 2026-103), art. 17 I-20°: "
                               "exemption limited to commitments filed before the law's entry into force",
                   note="closed to new beneficiaries in 2026; existing 5-year commitments run off. "
                        "1395 D (abrogé LF 2014, art. 26) was recodified as 1395 B bis: continuous measure"),
    "920202": dict(status="terminated", effective_year=2011, mechanism="sunset",
                   legal_basis="CGI art. 302 bis KG: reduced rate for non-analogue services fixed for "
                               "2009-2011 only (loi n° 2009-258, art. 32; LF 2011)",
                   note="v2: end date 2014 (= last annex year)"),
}
DECISIONS = {**DECISIONS_11, **AUDIT_DECISIONS}

# Renumbered / continued measures linked to their successor.
LINKS = {
    "730307": ("710110", "VM PLF 2021 p.33"),
    "220103": ("230605", "VM PLF 2013 p.28"),
    "700102": ("720207", "VM PLF 2021 p.33"),
    "800103": ("800220", "VM PLF 2021 p.34"),
    "800403": ("800221", "VM PLF 2021 p.34"),
    "800404": ("800222", "VM PLF 2021 p.34"),
    "800302": ("800228", "VM PLF 2021 p.34"),
    "800114": ("840101", "VM PLF 2021 p.34"),
    # NEW in v3
    "800207": ("800217", "duplicate codes for the same measure 2017-2019 (customs code art. 265, "
                         "table B, index 36); not in an official renumbering table"),
    "200309": ("230606", "VM PLF 2015, « Reclassement par renumérotation »"),
    "110214": ("110246", "reduction merged into the universal tax credit from 2017 (decision 3: "
                         "advantage continued)"),
    "730204": ("730210", "decision 3: 5.5% -> 10% from 01/01/2018 (LF 2018, art. 12) is a partial "
                         "cut, not a termination; residual 10% rate covered by 730210"),
}
UNLINKED_RENUMBERED = {
    "800208": "silent drop in PLF 2020; reduced rate still in force (art. 265 version 31/12/2020)",
    "800115": "PLF 2020 p.31 lists it as DECLASSIFIED, not renumbered; censored at exit",
}
UNCODED_CENSOR_EXIT = set()     # v2: {"140110", "800406", "800109"} — all now coded

# Codes reused for a different measure: keep only rows up to this annex year.
ROW_CUTOFF = {"920301": 2014, "800406": 2016}

# Declassified measures (PLF 2019 VM II annex « Chiffrages des mesures considérées
# comme des modalités de calcul de l'impôt », pp. 231-249): code -> PLF de déclassement.
DECLASSIFIED = {
    "100112": 2011, "110101": 2006, "110106": 2006, "110304": 2006, "110306": 2006,
    "120308": 2012, "130303": 2006, "140203": 2009, "140305": 2009, "150113": 2006,
    "150115": 2006, "150116": 2006, "150202": 2006, "150206": 2006, "150208": 2006,
    "150404": 2006, "150511": 2006, "150513": 2006, "150516": 2009, "160102": 2013,
    "160104": 2009, "160401": 2006, "160403": 2009, "160404": 2006, "160405": 2009,
    "170302": 2006, "170304": 2006, "180201": 2006, "180302": 2006, "190101": 2011,
    "190201": 2006, "190202": 2006, "190203": 2009, "190204": 2009, "190205": 2009,
    "190206": 2009, "190207": 2009, "190209": 2009, "200301": 2009, "200303": 2009,
    "200306": 2009, "210302": 2009, "210304": 2009, "210319": 2009, "230501": 2009,
    "230503": 2009, "230603": 2009, "250101": 2011, "320103": 2009, "320110": 2006,
    "320117": 2006, "330101": 2006, "330102": 2006, "330104": 2006, "330105": 2006,
    "350101": 2009, "400204": 2006, "400302": 2006, "520113": 2006, "520119": 2009,
    "520120": 2009, "520203": 2009, "520204": 2006, "520206": 2009, "520207": 2009,
    "520301": 2009, "520305": 2009, "570103": 2006, "570201": 2006, "570203": 2006,
    "740104": 2006, "800101": 2009, "800102": 2009, "800109": 2009, "820101": 2017,
    "980101": 2018, "980102": 2018, "980103": 2018, "980104": 2018, "980105": 2018,
}
# Also declassified, but not in the PLF 2019 list (left before 2019).
DECLASSIFIED_EXTRA = {"800115": 2020, "570101": 2024, "570102": 2024,
                      # PLF 2020 review of reduced VAT rates (Cour des comptes, NEB 2019, pp. 17-18)
                      "730203": 2020, "730215": 2020, "730219": 2020, "730220": 2020,
                      "730303": 2020, "740106": 2020}

# Mechanism of exit for audited cases that need no recoding (v3 column `mechanism`).
MECHANISM = {
    "300112": "repeal", "800206": "repeal",
    "210306": "repeal", "120114": "repeal", "140201": "repeal", "120136": "repeal",
    "920201": "repeal", "150711": "repeal", "120301": "repeal", "120507": "repeal",
    "160103": "repeal", "210311": "repeal",
    "170501": "underlying_tax_reform", "970101": "underlying_tax_reform",
    "560103": "scope_change", "960101": "scope_change", "960102": "scope_change",
}

# ============================================================================
# 1. Inputs
# ============================================================================
def yr(x):
    m = re.search(r"(?:19|20)\d{2}", str(x))
    return int(m.group(0)) if m else np.nan

P = pd.read_parquet(DATA / "vm_2009_2019.parquet")
V = pd.read_parquet(DATA / "vm_2020_2026.parquet")
ann = pd.concat([
    P[["numero", "vm_year", "libelle", "reference", "fin_fait"]].rename(columns={"fin_fait": "fin"}),
    V[["numero", "vm_year", "libelle", "reference", "fin_fait_generateur"]].rename(columns={"fin_fait_generateur": "fin"}),
], ignore_index=True)
ann["numero"] = ann["numero"].astype(str).str.zfill(6)
ann["end"] = ann["fin"].map(yr)
ann = ann.sort_values(["numero", "vm_year"])

gui = pd.read_csv(DATA / "guillaume_all.csv", dtype=str)
gui["code"] = gui["code"].str.strip().str.zfill(6)
gui = gui.drop_duplicates("code")
gui["group"] = gui["score"].where(gui["score"].isin(["0", "1", "2", "3"]), "not scored")

exits = pd.read_csv(HERE / "data" / "exits_to_code_v2.csv", dtype=str)
exits["code"] = exits["code"].str.zfill(6)
EXIT_TYPE = exits.set_index("code")["exit_type"]

DECL = {**DECLASSIFIED, **DECLASSIFIED_EXTRA}

# ============================================================================
# 2. Population
# ============================================================================
r2011 = ann[ann["vm_year"] == 2011].drop_duplicates("numero").set_index("numero")
end_2011 = r2011["end"]

def rows(code):
    h = ann[ann["numero"] == code]
    if code in ROW_CUTOFF:
        h = h[h["vm_year"] <= ROW_CUTOFF[code]]
    return h

FREEZE_LOG = {}
# Codes where a stale early end date must NOT freeze the series (seamless replacement
# under the same code, no gap in coverage).
FREEZE_EXCEPTIONS = {
    "210313": "old PTZ ended 2010, replaced on 01/01/2011 by PTZ+ under the same code; "
              "stale '2010' in early editions refers to the old PTZ",
}
MIN_CLOSED_EDITIONS = 2   # editions in a row that must report the measure as already closed

def is_open(fin):
    return bool(re.search(r"born|permanent", str(fin), re.I))

def frozen_end(h, code=None):
    """End date from a sequence of editions. Once at least MIN_CLOSED_EDITIONS
    consecutive editions published after the end year report the measure as
    closed, later upward revisions are ignored (re-dating of a closed measure, or a
    revival after a real gap). A single stale edition is treated as a publication
    lag (retroactive extension). An edition that explicitly reports the measure as
    open ('non borné') resets the count."""
    seq = []
    for _, r in h.sort_values("vm_year").iterrows():
        if pd.notna(r["end"]):              # a year in the field wins over any 'non borné' wording
            seq.append((int(r["vm_year"]), int(r["end"])))
        elif is_open(r["fin"]):
            seq.append((int(r["vm_year"]), "open"))
    frozen, run_end, run_len, last = np.nan, None, 0, np.nan
    if code in FREEZE_EXCEPTIONS:
        seq = [(y, e) for y, e in seq]          # keep sequence for the log, but never freeze
    for y, e in seq:
        if e == "open":                     # reported open again: cancel any freeze
            frozen, run_end, run_len, last = np.nan, None, 0, np.nan
            continue
        last = e
        if pd.notna(frozen):
            continue
        if e < y - 1 and code not in FREEZE_EXCEPTIONS:   # PLF y published in autumn y-1: already closed
            run_len = run_len + 1 if run_end == e else 1
            run_end = e
            if run_len >= MIN_CLOSED_EDITIONS:
                frozen = e
        else:
            run_end, run_len = None, 0
    if pd.notna(frozen) and pd.notna(last) and last != frozen and code is not None:
        FREEZE_LOG[code] = (int(frozen), int(last), " ".join(f"{y}:{e}" for y, e in seq))
    return frozen if pd.notna(frozen) else last

def latest_end(code):
    return frozen_end(rows(code), code)

def latest_dated_end_raw(code):
    """Latest year reported in any edition (v2 'chapter rule' definition, unchanged)."""
    e = rows(code).dropna(subset=["end"])
    return e["end"].iloc[-1] if len(e) else np.nan

DROP_LOG = []

def population(rule):
    if rule == "recount":
        keep = r2011.index[end_2011.isna() | (end_2011 >= ORIGIN)]
        pop = gui[gui["code"].isin(keep)]
    else:
        pop = gui[gui["numbered"].astype(str) == "True"]
        pop = pop[pop["code"].isin(ann[ann["vm_year"].between(ORIGIN, WINDOW_END)]["numero"])]
        pop = pop[~(pop["code"].map(latest_dated_end_raw) <= ORIGIN)]
    pop = pop.copy()
    reasons = {}
    for c in pop["code"]:
        if DECISIONS.get(c, {}).get("status") == "drop":
            reasons[c] = "hand-coded: ended before 2011"
        elif c in DECL and DECL[c] <= ORIGIN:
            reasons[c] = f"declassified PLF {DECL[c]} (before the window)"
        elif c not in DECISIONS and pd.notna(latest_end(c)) and latest_end(c) < ORIGIN:
            reasons[c] = f"latest end date {int(latest_end(c))} precedes the window"
    for c, why in reasons.items():
        DROP_LOG.append(dict(population_rule=rule, code=c, reason=why))
    return pop[~pop["code"].isin(reasons)].copy()

# ============================================================================
# 3. Outcome per measure
# ============================================================================
def history(code):
    h = pd.concat([rows(code)] + ([rows(LINKS[code][0])] if code in LINKS else []))
    return h.sort_values("vm_year")

def shift(y):
    return y + 1 if DATING_RULE == "first_closed_year" else y

def outcome(code):
    h = history(code)
    last = h.iloc[-1]
    last_annex = int(last["vm_year"])
    end = frozen_end(h, code)
    d = DECISIONS.get(code, {})
    exit_code = EXIT_TYPE.get(code)
    base = dict(last_annex=last_annex, end_latest=end, linked_to=LINKS.get(code, ("",))[0],
                legal_basis=d.get("legal_basis", ""), audit_note=d.get("note", ""))
    if d.get("status") == "terminated":
        return {**base, "event": 1, "event_year": d["effective_year"], "basis": "hand-coded termination",
                "mechanism": d.get("mechanism", "repeal")}
    if d.get("status") == "censored_2026":
        return {**base, "event": 0, "event_year": WINDOW_END, "basis": "hand-coded: still in force", "mechanism": ""}
    if d.get("status") == "censored_exit":
        return {**base, "event": 0, "event_year": last_annex, "basis": "reclassified, censored at exit",
                "mechanism": "scope_change"}
    if code in DECL and code not in LINKS:          # declassified during the window
        return {**base, "event": 0, "event_year": DECL[code] - 1,
                "basis": f"declassified PLF {DECL[code]}, censored at year before", "mechanism": "scope_change"}
    # end-date closures (also applies to linked measures, through the successor)
    if pd.notna(end) and end < WINDOW_END:
        y = shift(int(end))
        if y < WINDOW_END:
            basis = ("end date frozen at first reported closure (later editions re-dated it)"
                     if code in FREEZE_LOG else "end date in latest edition")
            return {**base, "event": 1, "event_year": max(y, ORIGIN), "basis": basis,
                    "mechanism": MECHANISM.get(code, "end_date_unverified")}
    if last_annex >= WINDOW_END:
        return {**base, "event": 0, "event_year": WINDOW_END, "basis": "still listed in 2026", "mechanism": ""}
    if pd.notna(end) and end >= WINDOW_END:
        return {**base, "event": 0, "event_year": WINDOW_END, "basis": "end date >= 2026, censored 2026", "mechanism": ""}
    # left the annex without an end date
    if code in LINKS:
        return {**base, "event": 0, "event_year": last_annex,
                "basis": f"linked series ({LINKS[code][0]}) left the annex without an end date, censored at exit",
                "mechanism": ""}
    if exit_code == "reclassified":
        return {**base, "event": 0, "event_year": last_annex, "basis": "reclassified, censored at exit",
                "mechanism": MECHANISM.get(code, "scope_change")}
    if exit_code == "renumbered":
        return {**base, "event": 0, "event_year": last_annex, "basis": "renumbered, no successor, censored at exit",
                "mechanism": ""}
    if code in UNCODED_CENSOR_EXIT:
        return {**base, "event": 0, "event_year": last_annex, "basis": "uncoded exit, censored at exit", "mechanism": ""}
    raise ValueError(f"{code}: left the annex in {last_annex} with no coding rule")

def build(rule):
    pop = population(rule)
    o = pd.DataFrame([{"code": c, **outcome(c)} for c in pop["code"]])
    o = pop[["code", "libelle", "score", "group"]].merge(o, on="code")
    o["duration"] = (o["event_year"] - ORIGIN).astype(float)
    o.loc[o["duration"] <= 0, "duration"] = T0_EPS
    o["end_2011_edition"] = o["code"].map(end_2011)
    o["sched_end_2011"] = (o["end_2011_edition"] == ORIGIN).astype(int)
    o["latest_end_eq_2011"] = (o["end_latest"] == ORIGIN).astype(int)
    o["population_rule"] = rule
    o["dating_rule"] = DATING_RULE
    return o

ORDER = ["0", "1", "2", "3", "not scored"]

def shares(o, label):
    t = o.groupby("group").agg(measures=("code", "size"), terminated=("event", "sum")).reindex(ORDER)
    t.loc["all"] = t.sum()
    t["share"] = (t["terminated"] / t["measures"]).round(3)
    t.insert(0, "variant", label)
    return t.reset_index()

# ============================================================================
# 4. Diagnostics: same error patterns in unaudited rows
# ============================================================================
AUDITED = set(DECISIONS) | set(LINKS) | set(MECHANISM) | set(UNLINKED_RENUMBERED)

def diagnostics(o):
    out = []
    for _, r in o.iterrows():
        c = r["code"]
        if c in AUDITED:
            continue
        h = rows(c).dropna(subset=["end"])
        if r["event"] == 0 and str(r["basis"]).startswith("reclassified") and c not in DECL:
            out.append(dict(code=c, pattern="exit coded 'reclassified' but not in any declassification list",
                            detail=f"last annex {r['last_annex']}"))
        if r["event"] == 1 and pd.notna(r["end_latest"]) and r["end_latest"] == r["last_annex"]:
            out.append(dict(code=c, pattern="end date equals last annex year (920202 pattern)",
                            detail=f"end {int(r['end_latest'])}"))
        hh = rows(c).sort_values("vm_year")
        if r["event"] == 1 and len(hh) and pd.notna(hh["end"].iloc[-1]) and hh["end"].iloc[:-1].isna().all() \
                and int(hh["vm_year"].iloc[-1]) >= WINDOW_END:
            out.append(dict(code=c, pattern="end date appears only in the latest edition (proposal risk)",
                            detail=f"end {int(hh['end'].iloc[-1])}"))
        if len(h) and r["event"] == 1 and h["end"].max() != h["end"].min():
            out.append(dict(code=c, pattern="end date changed across editions (extension or error)",
                            detail=f"ends reported: {sorted(set(int(x) for x in h['end']))}"))
    return pd.DataFrame(out)

if __name__ == "__main__":
    from lifelines import CoxPHFitter, KaplanMeierFitter
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    main = build(POPULATION_RULE)
    main.to_csv(OUT / "termination_dataset_v35.csv", index=False)
    main.to_csv(DATA / "termination_dataset_v35.csv", index=False)   # [replication package]
    chap = build("chapter")
    chap.to_csv(OUT / "termination_dataset_v35_chapter_rule.csv", index=False)
    pd.DataFrame(DROP_LOG).to_csv(OUT / "population_drops_v35.csv", index=False)

    D = diagnostics(main)
    D.to_csv(OUT / "diagnostics_unaudited_v35.csv", index=False)
    print(f"\nDiagnostics: {len(D)} flags on unaudited rows -> diagnostics_unaudited_v35.csv")
    if len(D):
        print(D["pattern"].value_counts().to_string())

    # ---- frozen end dates ------------------------------------------------------
    F = pd.DataFrame([dict(code=c, frozen_end=f, latest_edition_end=l, editions=q) for c, (f, l, q) in FREEZE_LOG.items()])
    F.to_csv(OUT / "frozen_end_dates_v35.csv", index=False)
    print(f"\nFrozen end dates: {len(F)} measures -> frozen_end_dates_v35.csv")
    if len(F):
        print(F[["code", "frozen_end", "latest_edition_end"]].to_string(index=False))

    # ---- random check sample (round 2 audit) -----------------------------------
    pool = main[(main["event"] == 1) & (~main["code"].isin(AUDITED))]
    sample = pool.sample(n=min(20, len(pool)), random_state=2027)[
        ["code", "libelle", "score", "event_year", "end_latest", "last_annex", "basis"]].copy()
    for col in ["Verdict (Correct / Wrong / Unsure)", "Correct coding if wrong", "Evidence (source, page or article)", "Notes"]:
        sample[col] = ""
    sample.to_csv(OUT / "check_sample_v35.csv", index=False)
    print(f"\nCheck sample: {len(sample)} unaudited terminations -> check_sample_v35.csv")

    # ---- change log v2 -> v3 -------------------------------------------------
    v2f = V2_DIR / "termination_dataset_v34.csv"
    if v2f.exists():
        v2 = pd.read_csv(v2f, dtype={"code": str})
        m = v2[["code", "event", "event_year", "basis"]].merge(
            main[["code", "event", "event_year", "basis", "mechanism", "legal_basis"]],
            on="code", how="outer", suffixes=("_v34", "_v35"), indicator=True)
        changed = m[(m["_merge"] != "both") | (m["event_v34"] != m["event_v35"]) |
                    (m["event_year_v34"] != m["event_year_v35"]) | (m["basis_v34"] != m["basis_v35"])].copy()
        changed["change"] = changed["_merge"].map({"left_only": "dropped from population",
                                                   "right_only": "added to population",
                                                   "both": "recoded"})
        changed.drop(columns="_merge").to_csv(OUT / "changelog_v34_v35.csv", index=False)
        print(f"\nChange log: {len(changed)} measures changed -> changelog_v34_v35.csv")
        print(changed["change"].value_counts().to_string())

    S = pd.concat([
        shares(main, "main (recount rule)"),
        shares(main[main["latest_end_eq_2011"] == 0], "main without measures ending in 2011"),
        shares(main[main["mechanism"] != "scope_change"], "main, scope-change exits removed"),
        shares(chap, "robustness (chapter rule)"),
    ])
    S.to_csv(OUT / "termination_shares_by_score_v35.csv", index=False)
    print(S.to_string(index=False))
    print("\nTerminations by mechanism (main):")
    print(main[main["event"] == 1]["mechanism"].value_counts().to_string())

    # ---- Kaplan-Meier --------------------------------------------------------
    labels = {"0": "Score 0", "1": "Score 1", "2": "Score 2", "3": "Score 3", "not scored": "Not scored"}
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for g in ORDER:
        s = main[main["group"] == g]
        kmf = KaplanMeierFitter().fit(s["duration"] + ORIGIN, s["event"], label=f"{labels[g]} (n = {len(s)})")
        kmf.plot_survival_function(ax=ax, ci_show=False)
    ax.set_xlim(ORIGIN, WINDOW_END)
    ax.set_ylim(0, 1.02)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.1f}"))
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of measures not terminated")
    ax.set_title("Survival of tax expenditures by 2011 Guillaume score (v3.5, frozen)")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT / "km_termination_by_score_v35.png", dpi=300)

    # ---- Cox -------------------------------------------------------------------
    def cox(o, with_dummy, label):
        e = o[o["group"].isin(["0", "1", "2", "3"])].copy()
        e["score_num"] = e["score"].astype(int)
        cols = ["duration", "event", "score_num"] + (["sched_end_2011"] if with_dummy else [])
        f = CoxPHFitter().fit(e[cols], "duration", "event")
        s = f.summary.loc["score_num"]
        return dict(model=label, dummy_2011_end=with_dummy, N=len(e), events=int(e["event"].sum()),
                    HR=round(s["exp(coef)"], 3), CI_low=round(s["exp(coef) lower 95%"], 3),
                    CI_high=round(s["exp(coef) upper 95%"], 3), p=round(s["p"], 4),
                    dummy_HR=round(f.summary.loc["sched_end_2011", "exp(coef)"], 3) if with_dummy else "",
                    dummy_p=round(f.summary.loc["sched_end_2011", "p"], 4) if with_dummy else "")
    C = pd.DataFrame([
        cox(main, False, "main"), cox(main, True, "main"),
        cox(main[main["mechanism"] != "scope_change"], False, "main, scope-change exits removed"),
        cox(main[main["latest_end_eq_2011"] == 0], False, "main without measures ending in 2011"),
        cox(chap, False, "chapter rule"), cox(chap, True, "chapter rule"),
    ])
    C.to_csv(OUT / "cox_score_per_point_v35.csv", index=False)
    print(C.to_string(index=False))
    print(f"\nDating rule: {DATING_RULE}; population rule: {POPULATION_RULE}")
    print("README: end-date closures are dated by the last open year, hand-coded repeals by the first "
          "closed year (v2 convention). Set DATING_RULE='first_closed_year' to align both.")
