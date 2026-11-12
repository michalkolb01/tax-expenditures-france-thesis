"""Chapter 5 - The survival dataset as an Excel workbook, for reading by hand.

Inputs
    ch5/tables/termination_dataset_v35.csv   (build_termination_v35.py, v3.5 frozen:
                                              the chapter's 379 measures)
    ch5/tables/population_drops_v35.csv      (build_termination_v35.py: measures
                                              removed from the population, with reason)
    data/intermediate/guillaume_all.csv      (the 470 measures of the 2011 report)
    data/intermediate/vm_2009_2019.parquet   (2011 annex: end date, creation year)
Output
    ch5/termination_panel_by_year.xlsx with four sheets:
      Measures      one row per measure followed (379)
      Year by year  status 2011-2026: open / terminated / closed / censored (coloured)
      Excluded      the 91 measures of the report not followed, with the reason (470 -> 379)
      Notes         definitions and censoring rules (see ch5/CHANGELOG.md)
Checks (printed; Chapter 5): 278 scored (95/81/42/60), 101 not scored;
terminated 41/33/10/15 and 38. Differences are reported, the data are not changed.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from config import INTERMEDIATE  # noqa: E402

TAB = HERE / "tables"
OUT = HERE / "termination_panel_by_year.xlsx"
ORIGIN, END = 2011, 2026
YEARS = list(range(ORIGIN, END + 1))
END_DATE = {"end_date_unverified", "sunset"}
FILL = {"open": "D9EAD3", "terminated": "E06666", "closed": "CCCCCC", "censored": "FFE599"}
EXPECTED = {"0": (95, 41), "1": (81, 33), "2": (42, 10), "3": (60, 15), "not scored": (101, 38)}


def yr(x):
    m = re.search(r"(19|20)\d{2}", str(x))
    return int(m.group(0)) if m else np.nan


def beneficiaries(b):
    b = str(b)
    if "Entreprises et" in b:
        return "households and firms"
    if "nage" in b:
        return "households"
    if "Entreprise" in b:
        return "firms"
    return b if b not in ("nan", "") else ""


def censor_reason(r):
    if r["event"] == 1:
        return ""
    if r["event_year"] >= END:
        return "still in force in 2026 (" + str(r["basis"]) + ")"
    return str(r["basis"])


def status_row(r):
    y = int(r["event_year"])
    out = {}
    for t in YEARS:
        if r["event"] == 1:
            out[t] = "open" if t < y else ("terminated" if t == y else "closed")
        else:
            out[t] = "open" if t <= y else "censored"
    return out


def build_measures(d, g, r2011):
    gi = g.set_index("code")
    m = pd.DataFrame({
        "code": d["code"],
        "name (French)": d["libelle"],
        "score 2011": d["group"],
        "cost 2011 (EUR m)": d["code"].map(gi["cost_2011"]),
        "beneficiaries": d["code"].map(gi["beneficiaires"]).map(beneficiaries),
        "tax": d["code"].map(gi["impot"]),
        "year of creation": d["code"].map(r2011["creation"]).map(yr),
        "terminated": np.where(d["event"] == 1, "yes", "no"),
        "termination year": d["event_year"].where(d["event"] == 1),
        "route": np.where(d["event"] == 1,
                          np.where(d["mechanism"].isin(END_DATE), "end date recorded in the annex",
                                   "suppression by law"), ""),
        "mechanism (code)": d["mechanism"].fillna(""),
        "basis (code)": d["basis"],
        "closure scheduled in 2011": np.where(d["sched_end_2011"] == 1, "yes", "no"),
        "censoring year": d["event_year"].where(d["event"] == 0),
        "censoring reason": d.apply(censor_reason, axis=1),
        "legal basis of termination": d["legal_basis"].fillna("").where(d["event"] == 1, ""),
        "linked successor code": d["linked_to"].fillna(""),
        "last annex year": d["last_annex"],
        "audit note": d["audit_note"].fillna(""),
    })
    return m


def build_excluded(d, g, ann2011):
    drops = pd.read_csv(TAB / "population_drops_v35.csv", dtype=str)
    drops = drops[drops["population_rule"] == "recount"].set_index("code")["reason"]
    rows = []
    for _, r in g[~g["code"].isin(set(d["code"]))].iterrows():
        c = r["code"]
        if c in drops.index:
            why = drops[c]
        elif str(r["numbered"]) != "True":
            why = "no six-digit code in the report (measure identified by the evaluators, never numbered)"
        elif c not in ann2011.index:
            why = "not listed in the 2011 annex edition"
        elif pd.notna(ann2011.loc[c, "end"]) and ann2011.loc[c, "end"] < ORIGIN:
            why = f"2011 annex edition gives an end date before 2011 ({int(ann2011.loc[c, 'end'])})"
        else:
            why = "UNEXPLAINED - check"
        rows.append(dict(code=c, name=r["libelle"], score=r["score"], reason=why))
    return pd.DataFrame(rows).sort_values("code")


NOTES = [
    ("Source", "ch5/tables/termination_dataset_v35.csv, built by ch5/build_termination_v35.py (v3.5, frozen). "
               "Full rules and every hand-coded case: ch5/CHANGELOG.md."),
    ("Population", "Measures of the 2011 report (Guillaume) with a six-digit code, listed in the 2011 annex "
                   "edition with no end date or an end date of 2011 or later; minus measures declassified before "
                   "2011, measures whose latest reported end date precedes 2011, and three hand-coded drops "
                   "(180104, 320111, 140124). 470 -> 379: see sheet Excluded."),
    ("Termination", "Closure to new beneficiaries. Either an end date recorded in the annex (end of the "
                    "qualifying event, 'fin du fait generateur'; route 'end date recorded in the annex') or a "
                    "repeal/suppression by law identified by hand (route 'suppression by law'). Existing "
                    "beneficiaries may keep the advantage after termination."),
    ("Termination year", "End-date closures: the last year of eligibility given in the latest annex edition in "
                         "which the measure appears; once at least two consecutive editions published after the "
                         "end year report the measure as closed, later re-dating is ignored (frozen end date). "
                         "Hand-coded repeals: the year the repeal takes effect."),
    ("Route vs basis", "'route' groups the code column `mechanism`: end_date_unverified and sunset = end date; "
                       "repeal, underlying_tax_reform, external = suppression by law (the chapter's 111/26). "
                       "`basis` records where the event comes from (end date in latest edition, frozen end date, "
                       "hand-coded termination)."),
    ("Censoring", "Measures still listed in 2026, or with an end date in 2026 or later, are censored in 2026. "
                  "Measures declassified during the window are censored the year before declassification. "
                  "Measures that leave the annex without an end date are censored at their last annex year "
                  "(reclassified, renumbered without successor). Renumbered measures with an official successor "
                  "are followed through the successor's code."),
    ("Closure scheduled in 2011", "The 2011 annex edition already gave an end of eligibility in 2011."),
    ("Year by year", "open = in force and open to new beneficiaries; terminated = year of closure to new "
                     "beneficiaries; closed = years after termination; censored = no longer observed "
                     "(reason in sheet Measures)."),
    ("Time origin", "2011 (year of the report). Terminations dated 2011 have duration 0.01 in the Cox models."),
]


def autosize(ws, max_w=60):
    for col in ws.columns:
        w = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(10, w + 2), max_w)


def main():
    d = pd.read_csv(TAB / "termination_dataset_v35.csv", dtype={"code": str, "score": str})
    d["code"] = d["code"].str.zfill(6)
    g = pd.read_csv(INTERMEDIATE / "guillaume_all.csv", dtype=str)
    g["code"] = g["code"].str.strip().str.zfill(6)
    g = g.drop_duplicates("code")
    a = pd.read_parquet(INTERMEDIATE / "vm_2009_2019.parquet")
    a["numero"] = a["numero"].astype(str).str.zfill(6)
    ann2011 = a[a["vm_year"] == 2011].drop_duplicates("numero").set_index("numero")
    ann2011 = ann2011.assign(end=ann2011["fin_fait"].map(yr))

    M = build_measures(d, g, ann2011)
    Y = pd.concat([M[["code", "name (French)", "score 2011"]],
                   pd.DataFrame([status_row(r) for _, r in d.iterrows()])], axis=1)
    X = build_excluded(d, g, ann2011)
    N = pd.DataFrame(NOTES, columns=["item", "definition"])

    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        M.to_excel(w, sheet_name="Measures", index=False)
        Y.to_excel(w, sheet_name="Year by year", index=False)
        X.to_excel(w, sheet_name="Excluded", index=False)
        N.to_excel(w, sheet_name="Notes", index=False)
        for ws in w.book.worksheets:
            ws.freeze_panes = "B2"
            for c in ws[1]:
                c.font = Font(bold=True)
            autosize(ws)
        ws = w.book["Year by year"]
        ws.column_dimensions["B"].width = 50
        for row in ws.iter_rows(min_row=2, min_col=4):
            for c in row:
                if c.value in FILL:
                    c.fill = PatternFill("solid", fgColor=FILL[c.value])
        wn = w.book["Notes"]
        wn.column_dimensions["B"].width = 120
        for c in wn["B"]:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    # ---- checks against Chapter 5 -------------------------------------------
    ok = True
    for grp, (n_exp, t_exp) in EXPECTED.items():
        s = M[M["score 2011"] == grp]
        n, t = len(s), int((s["terminated"] == "yes").sum())
        flag = "" if (n, t) == (n_exp, t_exp) else "   <-- DIFFERS from Chapter 5"
        ok &= flag == ""
        print(f"score {grp:<10} measures {n:>3} (chapter {n_exp}), terminated {t:>3} (chapter {t_exp}){flag}")
    print(f"total {len(M)} measures (chapter 379); excluded {len(X)} (470 - 379 = 91)")
    unexplained = (X["reason"] == "UNEXPLAINED - check").sum()
    print("unexplained exclusions:", unexplained)
    print("All counts match Chapter 5." if ok and len(M) == 379 else "COUNTS DIFFER - see above.")
    print("Written", OUT)


if __name__ == "__main__":
    main()
