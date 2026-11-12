"""Writes CHANGELOG.md, comparison.md and uncoded_exits.csv for results_ch5_v2."""
import sys
from pathlib import Path
import re, numpy as np, pandas as pd

DATA = Path(sys.argv[1]); OUT = DATA / "results_ch5_v2"
ORDER = ["0", "1", "2", "3", "not scored"]
def yr(x):
    m = re.search(r"(?:19|20)\d{2}", str(x)); return int(m.group(0)) if m else np.nan

P = pd.read_parquet(DATA / "vm_2009_2019.parquet"); V = pd.read_parquet(DATA / "vm_2020_2026.parquet")
ann = pd.concat([P[["numero", "vm_year", "libelle", "reference", "fin_fait"]].rename(columns={"fin_fait": "fin"}),
                 V[["numero", "vm_year", "libelle", "reference", "fin_fait_generateur"]].rename(columns={"fin_fait_generateur": "fin"})])
ann["end"] = ann["fin"].map(yr); ann = ann.sort_values(["numero", "vm_year"])
gui = pd.read_csv(DATA / "guillaume_all.csv", dtype=str); gui["code"] = gui["code"].str.zfill(6)
gui["group"] = gui["score"].where(gui["score"].isin(ORDER[:4]), "not scored")
main = pd.read_csv(OUT / "termination_dataset_v2.csv", dtype={"code": str})
chap = pd.read_csv(OUT / "termination_dataset_v2_chapter_rule.csv", dtype={"code": str})
S = pd.read_csv(OUT / "termination_shares_by_score.csv", dtype={"group": str})
C = pd.read_csv(OUT / "cox_score_per_point_v2.csv")
old11 = pd.read_csv(DATA / "validation" / "exits_coded_11.csv", dtype={"code": str})
new11 = pd.read_csv(OUT / "exits_coded_11_v2.csv", dtype=str)
exits = pd.read_csv(DATA / "exits_to_code_v2.csv", dtype=str)

# ---- chapter code outcomes (Master Thesis_4 Matching, cells 6 and 18) -------
listed = {y: set(ann[ann["vm_year"] == y]["numero"]) for y in range(2011, 2027)}
g = gui[gui["numbered"] == "True"].copy()
g = g[g["code"].map(lambda c: any(c in listed[y] for y in range(2011, 2027)))]
def exit_year(c):
    last = max(y for y in range(2011, 2027) if c in listed[y]); return np.nan if last == 2026 else last + 1
g["exit_year"] = g["code"].map(exit_year)
fin_final = ann.dropna(subset=["end"]).groupby("numero")["end"].last()
g["fin_final"] = g["code"].map(fin_final)
g = g[~(g["fin_final"] <= 2011)].copy()
clos = g["fin_final"].where(g["fin_final"].between(2012, 2026))
g["term_year"] = pd.concat([clos, g["exit_year"]], axis=1).min(axis=1)
g["term"] = g["term_year"].notna().astype(int)
g["via"] = np.select([g["term"].eq(0), clos.notna() & (clos <= g["exit_year"].fillna(9999))], ["open", "closure"], "delisting")
chapter_code = g.set_index("code")
assert chapter_code.groupby("group").size().reindex(ORDER).tolist() == [99, 86, 45, 61, 100]

def md_table(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r.values) + " |")
    return "\n".join(out)

def outcome_txt(e, y):
    return f"terminated {int(y)}" if e == 1 else f"censored {int(y)}"

# ============================================================================
# uncoded_exits.csv (step 2)
# ============================================================================
unc_codes = ["140110", "800406", "800109"]
rows = []
for c in unc_codes:
    h = ann[ann["numero"] == c]
    ref = h["reference"].dropna().astype(str)
    ref = ref[~ref.str.contains("Chiffrages|nan")]
    fins = h["fin"].astype(str)
    rows.append(dict(code=c, score=gui.set_index("code").loc[c, "score"],
                     last_annex=int(h["vm_year"].max()),
                     description_guillaume=gui.set_index("code").loc[c, "libelle"],
                     description_last_annex=h["libelle"].iloc[-1],
                     article_reference=(ref.iloc[-1] if len(ref) else
                                        re.sub(r".*Code des Douanes : ", "Code des douanes ", fins[fins.str.contains("Code des Douanes")].iloc[-1])
                                        if fins.str.contains("Code des Douanes").any() else "not recorded in the annex panel"),
                     in_exits_to_code_v2="no",
                     chapter_code_outcome=outcome_txt(chapter_code.loc[c, "term"], chapter_code.loc[c, "term_year"]) + " (via end date in an earlier edition)",
                     treatment_v2="censored at last annex year (not coded)"))
U = pd.DataFrame(rows); U.to_csv(OUT / "uncoded_exits.csv", index=False)

# ============================================================================
# CHANGELOG.md
# ============================================================================
L = ["# CHANGELOG — results_ch5_v2", "",
     "Built 10 Nov 2026 with `build_termination_v2.py` (DATING_RULE = `effective_year`, "
     "POPULATION_RULE = `recount`). No existing file was modified; every output is new and sits in this folder.", "",
     "## 1. `exits_coded_11_v2.csv` (from `validation/exits_coded_11.csv`)", "",
     "All 11 records changed. New columns: `termination_status`, `effective_year`, `legal_basis`, `link_to`, `notes_v2`.", ""]
t = old11[["code", "exit_type"]].rename(columns={"exit_type": "exit_type_v1"}).merge(
    new11[["code", "score", "exit_type", "termination_status", "effective_year", "legal_basis", "link_to"]], on="code")
L += [md_table(t.rename(columns={"exit_type": "exit_type_v2"})), ""]

L += ["## 2. Population (recount rule) vs chapter population", ""]
pop_ch = set(chapter_code.index); pop_new = set(main["code"])
dropped3 = ["180104", "320111", "140124"]
L.append(f"- Dropped as ended before 2011 (hand-coded): {', '.join(dropped3)} (all not scored).")
only_ch = sorted(pop_ch - pop_new - set(dropped3)); only_new = sorted(pop_new - pop_ch)
def lst(codes):
    return ", ".join(f"{c} ({gui.set_index('code').loc[c, 'group']})" for c in codes)
L.append(f"- In the chapter population, not in v2 ({len(only_ch)}): 2011 edition gives an end before 2011, later editions extend it: {lst(only_ch)}.")
L.append(f"- In v2, not in the chapter population ({len(only_new)}): 2011 edition gives no end or an end ≥ 2011, latest dated end ≤ 2011: {lst(only_new)}.")
L.append("")

L += ["## 3. Termination outcomes changed vs the chapter code (measures in both populations)", "",
      "`chapter` = outcome produced by the chapter code (*Master Thesis_4 Matching*, cells 6 and 18): end date 2012–2026 "
      "taken from the latest *dated* edition, or any exit from the annex. `v2` = this rebuild.", ""]
x = main.merge(chapter_code[["term", "term_year", "via"]], left_on="code", right_index=True)
x = x[(x["term"] != x["event"]) | ((x["term"] == 1) & (x["event"] == 1) & (x["term_year"] != x["event_year"]))]
x["chapter"] = [outcome_txt(e, y) + f" ({v})" for e, y, v in zip(x["term"], x["term_year"].fillna(2026), x["via"])]
x["v2"] = [outcome_txt(e, y) for e, y in zip(x["event"], x["event_year"])]
x = x.sort_values(["group", "code"])
L += [md_table(x[["code", "group", "chapter", "v2", "basis"]].rename(columns={"group": "score", "basis": "v2 basis"})), ""]

L += ["## 4. Flags (no recoding done)", "",
      "- **800115** is coded `renumbered` in `exits_to_code_v2.csv`, but VM PLF 2020 p.31 lists it as **declassified**. "
      "Both rules censor it at 2019, so results are unaffected.",
      "- **920301**: from PLF 2020 the code belongs to a different measure (TOCE exclusion created in 2020). Only the 2010–2014 rows "
      "are used for the Guillaume measure.",
      "- **800406**: the label in its last edition (PLF 2019, 'gazole non routier pour le ferroviaire') differs from the Guillaume "
      "label (pure vegetable oils): possible code reuse, not resolved.",
      "- **570101, 570102**: no successor code in the 2020–2026 panel; no 2024–2026 measure cites CGI art. 809/810.",
      "- **800207, 800208, 800102, 800101**: renumbered, no successor found (editions checked: PLF 2019; PLF 2020 pp.30–31 and "
      "the concordance tables; PLF 2021 pp.33–35). Censored at 2019.", ""]
(OUT / "CHANGELOG.md").write_text("\n".join(L), encoding="utf-8")
n_changed = len(x)

# ============================================================================
# comparison.md
# ============================================================================
def share_row(variant):
    s = S[S["variant"] == variant].set_index("group")
    return s
main_s = share_row("main (recount rule)"); chap_s = share_row("robustness (chapter rule)")
no19 = share_row("main without the 19 with latest end <= 2011"); no3 = share_row("main without 140110, 800406, 800109")
chapter_vals = {"0": (0.52, 99), "1": (0.47, 86), "2": (0.29, 45), "3": (0.20, 61), "not scored": (0.41, 100)}
recount_sizes = {"0": 99, "1": 81, "2": 45, "3": 61, "not scored": 108}
T = pd.DataFrame({
    "score": ORDER,
    "chapter (n, share)": [f"{chapter_vals[k][1]}, {chapter_vals[k][0]:.0%}" for k in ORDER],
    "recount n": [recount_sizes[k] for k in ORDER],
    "v2 main (n, terminated, share)": [f"{int(main_s.loc[k,'measures'])}, {int(main_s.loc[k,'terminated'])}, {main_s.loc[k,'share']:.0%}" for k in ORDER],
    "v2 without the 19": [f"{int(no19.loc[k,'measures'])}, {int(no19.loc[k,'terminated'])}, {no19.loc[k,'share']:.0%}" for k in ORDER],
    "v2 without the 3 uncoded": [f"{int(no3.loc[k,'measures'])}, {int(no3.loc[k,'terminated'])}, {no3.loc[k,'share']:.0%}" for k in ORDER],
    "v2 chapter rule": [f"{int(chap_s.loc[k,'measures'])}, {int(chap_s.loc[k,'terminated'])}, {chap_s.loc[k,'share']:.0%}" for k in ORDER],
})
def cox_line(model, dummy):
    r = C[(C["model"] == model) & (C["dummy_2011_end"] == dummy)].iloc[0]
    d = f"; dummy HR {r['dummy_HR']}, p = {r['dummy_p']}" if dummy else ""
    return f"| {model}{' + 2011-end dummy' if dummy else ''} | {r['HR']:.3f} ({r['CI_low']:.3f}–{r['CI_high']:.3f}) | {r['p']} | {int(r['N'])} | {int(r['events'])} | {d.strip('; ')} |"

dummy = main[main["sched_end_2011"] == 1]["group"].value_counts().reindex(ORDER).fillna(0).astype(int)
n19 = main[main["latest_end_le_2011"] == 1]
sw = main.merge(chapter_code[["term", "via"]], left_on="code", right_index=True)
sw = sw[(sw["term"] == 1) & (sw["event"] == 0)]
sw_tab = pd.crosstab(sw["basis"], sw["group"]).reindex(columns=ORDER, fill_value=0)
sw_tab["total"] = sw_tab.sum(axis=1)
sw_tab.loc["total"] = sw_tab.sum()
swc = chap.merge(chapter_code[["term"]], left_on="code", right_index=True)
swc = swc[(swc["term"] == 1) & (swc["event"] == 0)]["group"].value_counts().reindex(ORDER).fillna(0).astype(int)

# 7 score-1 measures kept only under the chapter rule
rows = []
for c in sorted(set(chap["code"]) - set(main["code"])):
    if gui.set_index("code").loc[c, "group"] != "1":
        continue
    h = ann[ann["numero"] == c]; later = sorted(y for y in h["vm_year"].unique() if y > 2011)
    r = chap.set_index("code").loc[c]
    rows.append(dict(code=c, end_2011_edition=h[h["vm_year"] == 2011]["fin"].iloc[0],
                     later_annexes=f"{later[0]}–{later[-1]} ({len(later)} editions)",
                     latest_end=("non borné" if pd.isna(r["end_latest"]) else int(r["end_latest"])),
                     outcome_under_chapter_rule=outcome_txt(r["event"], r["event_year"]),
                     name=gui.set_index("code").loc[c, "libelle"][:80]))
K = pd.DataFrame(rows)
both1 = sorted(c for c in set(main["code"]) - set(chap["code"]) if gui.set_index("code").loc[c, "group"] == "1")

# 31 coded delistings
ex = exits[exits["exit_type"].notna()].merge(main[["code", "group", "last_annex", "linked_to", "event", "event_year", "basis"]], on="code", how="left")
ex["successor"] = ex["linked_to"].fillna("").map(lambda v: str(int(float(v))) if v not in ("", "nan") else "")
ex["treatment"] = [("followed via " + s + "; " if s else "") + outcome_txt(e, y) for s, e, y in zip(ex["successor"], ex["event"], ex["event_year"])]
ex = ex.sort_values(["exit_type", "group", "code"])
ex_tab = pd.crosstab([ex["exit_type"], ex["treatment"].str.replace(r"followed via \d+; ", "followed via successor; ", regex=True)],
                     ex["group"]).reindex(columns=ORDER, fill_value=0)
ex_tab["total"] = ex_tab.sum(axis=1)

R = ["# Chapter 5 terminations — v2 compared with the chapter and the recount", "",
     "Rules used: population = **recount rule** (open in 2011 if the 2011 edition gives no end date or an end ≥ 2011), "
     "minus 180104, 320111, 140124. Dating rule = **effective year of termination**: for end-date closures, the end of "
     "eligibility in the latest edition in which the measure appears (an end in 2026 or later = censored at 2026); for "
     "the two hand-coded repeals, the effective year (300112: 2012; 800206: 2020). Real terminations only: exits from the "
     "annex without an end date are censored at their last annex year unless hand-coded as a repeal. Renumbered measures are "
     "followed through their successor code. Time origin 2011; terminations dated 2011 get duration 0.01.", "",
     "## 1. Termination shares by Guillaume score", "", md_table(T), "",
     f"The 19 measures whose latest end is ≤ 2011 are terminated in 2011. {int(n19['sched_end_2011'].sum())} of them are flagged by the 2011-end dummy.", "",
     "## 2. Cox model, score per point (scored measures only)", "",
     "| model | HR (95% CI) | p | N | events | dummy |", "|---|---|---|---|---|---|",
     cox_line("main", False), cox_line("main", True),
     cox_line("main without 3 uncoded", False), cox_line("main without 3 uncoded", True),
     cox_line("main without the 19", False), cox_line("chapter rule", False), cox_line("chapter rule", True), "",
     "Reference values: chapter HR **0.69 (0.58–0.83)**; independent recount HR **0.825 (0.693–0.982), N 286, 105 events**.", "",
     "- **v2 vs the recount.** v2 has the same N (286 scored measures: the recount rule, and the 3 dropped measures are not scored). "
     "v2 has 107 events against 105. The recount (*Untitled9*, cell 5) also differs in three ways: (a) it counts as events only end "
     "dates in 2012–2025 and treats an end of 2011 as censored at 2026, where v2 terminates those measures in 2011; (b) it treats "
     "800206 (score 1, repealed 2020) as censored at its last annex year, where v2 counts it as an event; (c) it controls for households, log cost, no cost estimate, "
     "age and income tax. Its HR is the adjusted one, so it is not directly comparable with the unadjusted v2 HR.",
     "- **v2 vs the chapter.** The chapter HR (0.69) is stronger than any v2 specification; the chapter-rule v2 gives "
     f"{C[(C['model']=='chapter rule')&(~C['dummy_2011_end'])].iloc[0]['HR']:.3f}. The chapter code's event definition counts "
     "every exit from the annex as a termination (see §4). That inflates events most among the measures that were reclassified "
     "or renumbered.", "",
     "## 3. 2011-end dummy (2011 edition gives an end of eligibility in 2011)", "",
     "Under the recount rule: " + ", ".join(f"score {k}: {v}" if k != "not scored" else f"not scored: {v}" for k, v in dummy.items())
     + f" — total {dummy.sum()} ({dummy[ORDER[:4]].sum()} scored, used in the Cox models).", "",
     "## 4. Measures that switch from terminated (chapter code) to censored (v2)", "",
     f"Main population, measures in both populations: **{len(sw)}** switch. By score: "
     + ", ".join(f"{k}: {int(sw_tab.loc['total', k])}" for k in ORDER) + ". No measure switches the other way.", "",
     md_table(sw_tab.reset_index().rename(columns={"basis": "reason in v2"})), "",
     f"On the chapter population (robustness), {int(swc.sum())} switch: " + ", ".join(f"{k}: {v}" for k, v in swc.items()) + ".",
     "'still listed in 2026' under a chapter closure: the latest *dated* edition gave an end in 2012–2026, but the latest edition "
     "gives no end date or an end of 2026. Under the chapter rule's own dating (end 2026 = terminated), part of these would stay terminated.", "",
     "## 5. Why group sizes differ (chapter 86/100 vs recount 81/108 for score 1 / not scored)", "",
     "No measure has a different score in the two counts: both use `guillaume_all.csv`, which has no duplicate codes. The "
     "difference is the definition of 'open in 2011':",
     "- chapter code: drop a measure if the end date in the **latest dated edition** is ≤ 2011;",
     "- recount: keep a measure if the **2011 edition** gives no end date or an end ≥ 2011.",
     f"{len(set(chap['code']) - set(main['code']))} measures are only in the chapter population. The 2011 edition gives an end before 2011, which later editions "
     f"extended; 7 of them have score 1. {len(set(main['code']) - set(chap['code']))} are only in the recount population: the 2011 edition gives an end of 2011 or none, "
     f"and a later edition dates the end at or before 2011; 2 have score 1 ({', '.join(both1)}) and 9 are not scored. "
     "Score 1: 86 − 7 + 2 = 81. Not scored: 100 − 1 + 9 = 108.", "",
     "### The score-1 measures kept only under the chapter rule (not changed; for your decision)", "",
     "You asked for 5. The net difference is 5, but 7 measures are involved: 7 leave and 2 enter.", "",
     md_table(K), "",
     "## 6. Reclassified (19) and renumbered (12) measures from `exits_to_code_v2.csv`", "",
     md_table(ex_tab.reset_index()), "",
     md_table(ex[["code", "exit_type", "group", "last_annex", "treatment"]].rename(columns={"group": "score"})), "",
     "Renumbered without a successor (censored at exit): 800207 (score 0), 800208 (0), 800102 (2), 800101 (2), all last listed in "
     "PLF 2019. Editions checked: PLF 2019; PLF 2020 pp.30–31 (only 210204→200401 and 210205→200402) and the concordance "
     "tables; PLF 2021 pp.33–35 (twelve renumberings, none of these). 800115 (0) is coded renumbered but PLF 2020 p.31 lists it "
     "as declassified; it is censored at 2019 either way. In the 2020 edition, the closest labels are 800217 (for 800207) and "
     "800203 (for 800208), but no annex table links them, so they were **not linked**.", "",
     "## 7. Remaining uncoded exits", "",
     "`exits_to_code_v2.csv`: **none** — its only uncoded rows were the 11, all now coded in `exits_coded_11_v2.csv`.",
     "Under v2's dating rule, three more measures leave the annex without an end date. They are in both populations, but the chapter "
     "code counted them as closures from an end date in an earlier edition. They are censored at their last annex year for now "
     "(`uncoded_exits.csv`):", "",
     md_table(U[["code", "score", "last_annex", "description_guillaume", "article_reference", "chapter_code_outcome"]]), "",
     "800406: the label in its last edition is 'gazole non routier pour le ferroviaire', not the Guillaume label (possible code reuse).", "",
     "## Files", "",
     "- `exits_coded_11_v2.csv`, `termination_dataset_v2.csv` (main), `termination_dataset_v2_chapter_rule.csv` (robustness)",
     "- `termination_shares_by_score.csv`, `cox_score_per_point_v2.csv`, `km_termination_by_score_v2.png`",
     "- `uncoded_exits.csv`, `CHANGELOG.md`, `build_termination_v2.py`, `write_reports.py`", ""]
(OUT / "comparison.md").write_text("\n".join(R), encoding="utf-8")
print("records changed vs chapter (CHANGELOG §3):", n_changed)
print(T.to_string(index=False)); print(sw_tab); print(ex_tab); print(K.to_string(index=False))
