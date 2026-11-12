"""Samples prepared to validate the amendment-measure matching (no LLM).

PREPARED BUT NOT CODED: the two workbooks below were drawn but never coded,
and nothing in the thesis rests on them. The matching has no hand validation.

Two workbooks, drawn for coding:

1. Precision sample: 100 (amendment, measure) pairs from pairs_14 and
   pairs_15_17, stratified by 2011 score group (0, 1, 2, 3, not evaluated;
   20 each) and by whether the pair is ambiguous (every article linking the
   amendment to the measure also hosts another tax expenditure): 7 ambiguous
   and 13 unambiguous per group, topped up from the other cell if short. An
   amendment appears at most once. `weight` = pairs in the cell / pairs drawn,
   to reweight precision to the population. Seed 20261109. Columns
   `correct_match` (yes / no / partly) and `notes` are left empty for coding.
2. Silent survivors: measures scored 0 in 2011, listed in Voies et moyens
   2026 and still open to new beneficiaries (`fin_fait_generateur` "Non borné"
   or a year >= 2026), with no matched amendment, to search for;
   plus a context sheet of all open score-0 measures.

The article index is rebuilt exactly as in 02_match_articles.py
(`n_measures` counts all tax expenditures on the article, not only the
2011 ones).

Inputs
    data/intermediate/vm_2009_2019.parquet, vm_2020_2026.parquet
    data/intermediate/measures_with_bands.csv, pairs_14.parquet, pairs_15_17.parquet
        (02_match_articles.py)
    data/intermediate/guillaume_all.csv  (read in the notebook, not used)
Outputs
    data/intermediate/validation/matching_precision_sample.xlsx
        sheets: sample (100 rows), strata_sample, strata_population
    data/intermediate/validation/silent_survivors_check.xlsx
        sheets: silent_survivors, all_open_score0
Reproduces
    Pipeline step, no thesis number directly. Notebook result: 587 distinct
    CGI articles, 473 hosting one measure, 114 several (33 four or more);
    116 measures scored 0, 57 listed in 2026, 46 still open, 5 with no
    matched amendment; 19 of the 46 matched only through shared articles.
Source
    12_matching_validation.ipynb, cells 2 (setup), 6 (article index),
    8 (pairs and strata), 10 (sample), 12 (precision workbook),
    14 (silent survivors). Dropped: cell 4 (file listing, diagnostic).
Changes from the notebook
    - Paths through src/config.py; outputs in INTERMEDIATE / "validation".
Known caveats
    - Needs openpyxl.
    - The workbooks were prepared but not coded.
"""
import html
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

DATA = INTERMEDIATE
VAL = DATA / "validation"

SEED = 20261109     # fixed: the sample is reproducible
N_TOTAL = 100
AMB_SHARE = 1 / 3        # target share of pairs on articles hosting several measures

NOT_CGI = re.compile(r"\bloi\s*n[°o]|d[ée]cret|BOFIP|BOI-|\bDB\d|ordonnance|annexe", re.I)


def clean(x):
    x = html.unescape(re.sub(r"<[^>]+>", " ", str(x or "")))
    return re.sub(r"\s+", " ", x).strip()


def link(uid, leg):
    m = re.match(r"AMANR5L(\d{2})", str(uid))
    leg = int(m.group(1)) if m else pd.to_numeric(leg, errors="coerce")
    return f"https://www.assemblee-nationale.fr/dyn/{int(leg)}/amendements/{uid}" \
           if pd.notna(leg) and int(leg) >= 15 else ""


def is_open(f):
    if re.search(r"non.?born", str(f), re.I):
        return True
    y = re.search(r"(?:19|20)\d{2}", str(f))
    return bool(y) and int(y.group(0)) >= 2026


def hint(a):
    a = str(a)
    if a in ("", "nan"):
        return "no CGI article in the index: cannot be matched"
    if re.search(r"\d+-\d+(-[a-z])?\b", a):
        return "recorded at sub-paragraph level: amendments citing the parent article are not matched"
    return ""


def main():
    VAL.mkdir(parents=True, exist_ok=True)

    # --- article index (cell 6) ---
    P = pd.read_parquet(DATA / "vm_2009_2019.parquet")
    vm = pd.read_parquet(DATA / "vm_2020_2026.parquet")
    g = pd.read_csv(DATA / "measures_with_bands.csv", dtype={"code": str})
    g["code"] = g["code"].str.zfill(6)
    gui = pd.read_csv(DATA / "guillaume_all.csv", dtype={"code": str})  # noqa: F841

    cols = ["numero", "vm_year", "reference", "articles"]
    src = pd.concat([P[cols].assign(code_ref="code général des impôts"),
                     vm[cols + ["code_ref"]]], ignore_index=True)
    ok = ~src["reference"].fillna("").str.contains(NOT_CGI)
    ok &= src["code_ref"].fillna("code général des impôts").str.contains(
              "g[ée]n[ée]ral des imp", case=False, regex=True)
    idx = src[ok & src["articles"].notna() & (src["articles"] != "")]
    idx = idx.assign(article=idx["articles"].str.split("|")).explode("article")
    idx["article"] = idx["article"].str.strip()
    idx = idx[idx["article"] != ""]

    n_meas = idx.groupby("article")["numero"].nunique().rename("n_measures")
    POP = set(g["code"])
    n_meas_pop = idx[idx["numero"].isin(POP)].groupby("article")["numero"].nunique()

    print(f"{len(n_meas)} distinct CGI articles in Voies et moyens 2009–2026")
    print(f"  hosting one measure:      {(n_meas == 1).sum()}")
    print(f"  hosting several measures: {(n_meas > 1).sum()}  (four or more: {(n_meas > 3).sum()})")
    print(f"{len(n_meas_pop)} of them host a Guillaume measure; "
          f"{(n_meas_pop > 1).sum()} host several Guillaume measures")

    # --- pairs and strata (cell 8) ---
    pairs = pd.concat([pd.read_parquet(DATA / "pairs_14.parquet"),
                       pd.read_parquet(DATA / "pairs_15_17.parquet")], ignore_index=True)
    pairs["measure"] = pairs["measure"].astype(str).str.zfill(6)
    pairs["n_measures"] = pairs["article"].map(n_meas).fillna(1).astype(int)
    print(f"{len(pairs):,} uid-article-measure rows")

    u = (pairs.groupby(["uid", "measure"])
              .agg(article=("article", lambda s: " | ".join(sorted(set(s)))),
                   n_measures=("n_measures", "min"))
              .reset_index())
    u["ambiguous"] = u["n_measures"] > 1
    u["score_grp"] = u["measure"].map(g.set_index("code")["score"]).fillna("Non évalué")
    u["score_grp"] = u["score_grp"].where(u["score_grp"].isin(["0", "1", "2", "3"]), "non évalué")

    meta_cols = ["uid", "legislature", "numero", "date_depot", "dispositif", "expose"]
    meta = pairs[[c for c in meta_cols if c in pairs.columns]].drop_duplicates("uid")
    u = u.merge(meta, on="uid", how="left")

    pop = pd.crosstab(u["score_grp"], u["ambiguous"], margins=True)
    print(f"{len(u):,} amendment–measure pairs, {u['uid'].nunique():,} amendments")
    print(f"share ambiguous in the population: {u['ambiguous'].mean():.2f}\n")
    print(pop)

    # --- sample (cell 10) ---
    rng = np.random.default_rng(SEED)
    GROUPS = ["0", "1", "2", "3", "non évalué"]
    per_grp = N_TOTAL // len(GROUPS)
    n_amb = 7                                   # 7 of 20 per group -> 35 of 100
    quota = {True: n_amb, False: per_grp - n_amb}

    picked, used = [], set()

    def draw(cell, k):
        cell = cell[~cell["uid"].isin(used)]
        take = cell.iloc[rng.permutation(len(cell))].drop_duplicates("uid").head(k)
        used.update(take["uid"])
        return take

    for grp in GROUPS:
        sub = u[u["score_grp"] == grp]
        got = {a: draw(sub[sub["ambiguous"] == a], quota[a]) for a in (True, False)}
        for a in (True, False):                      # top up from the other cell if short
            short = quota[a] - len(got[a])
            if short > 0:
                extra = draw(sub[sub["ambiguous"] == (not a)], short)
                got[not a] = pd.concat([got[not a], extra])
                print(f"score {grp}: {short} {'ambiguous' if a else 'unambiguous'} "
                      f"pairs missing, taken from the other cell")
        for a in (True, False):
            picked.append(got[a])

    s = pd.concat(picked, ignore_index=True)
    cell_n = u.groupby(["score_grp", "ambiguous"]).size()
    draw_n = s.groupby(["score_grp", "ambiguous"]).size()
    s["weight"] = [cell_n[k] / draw_n[k] for k in zip(s["score_grp"], s["ambiguous"])]
    print(pd.crosstab(s["score_grp"], s["ambiguous"], margins=True))
    assert s["uid"].is_unique

    # --- precision workbook (cell 12) ---
    lib = (pd.concat([P[["numero", "vm_year", "libelle"]], vm[["numero", "vm_year", "libelle"]]])
             .sort_values("vm_year").drop_duplicates("numero", keep="last")
             .set_index("numero")["libelle"])

    out = pd.DataFrame({
        "amendment_id":        s["uid"],
        "amendment_number":    s.get("numero"),
        "legislature":         s.get("legislature"),
        "date":                pd.to_datetime(s.get("date_depot"), errors="coerce").dt.date,
        "url":                 [link(a, b) for a, b in zip(s["uid"], s.get("legislature"))],
        "dispositif":          s.get("dispositif").map(clean),
        "expose_sommaire":     s.get("expose").map(clean),
        "article_cited":       s["article"],
        "measure_code":        s["measure"],
        "measure_name":        s["measure"].map(lib),
        "score":               s["score_grp"],
        "article_hosts_several_measures": np.where(s["ambiguous"], "yes", "no"),
        "n_measures_on_article": s["n_measures"],
        "weight":              s["weight"].round(2),
        "correct_match":       "",               # yes / no / partly
        "notes":               "",
    })
    out = out.sample(frac=1, random_state=SEED).reset_index(drop=True)   # strata not in row order

    with pd.ExcelWriter(VAL / "matching_precision_sample.xlsx", engine="openpyxl") as w:
        out.to_excel(w, sheet_name="sample", index=False)
        pd.crosstab(s["score_grp"], s["ambiguous"], margins=True).to_excel(w, sheet_name="strata_sample")
        pop.to_excel(w, sheet_name="strata_population")
    print(f"saved {len(out)} rows -> {VAL / 'matching_precision_sample.xlsx'}")

    # --- silent survivors (cell 14) ---
    v26 = vm[vm["vm_year"] == 2026].drop_duplicates("numero").set_index("numero")

    z = g[(g["score"] == "0") & g["code"].isin(v26.index)].copy()
    z["fin_fait_generateur_2026"] = z["code"].map(v26["fin_fait_generateur"])
    z = z[z["fin_fait_generateur_2026"].map(is_open)]
    z["n_matched_amendments"] = z["n_amend_14"] + z["n_amend_15_17"]
    z["articles_2026"] = z["code"].map(v26["reference"])
    z["articles_index"] = z["code"].map(idx[idx["numero"].isin(POP)].groupby("numero")["article"]
                                        .agg(lambda a: " | ".join(sorted(set(a)))))
    z["only_shared_articles"] = z["code"].map(
        idx[idx["numero"].isin(POP)].groupby("numero")["article"]
           .agg(lambda a: all(n_meas[x] > 1 for x in set(a))))

    silent = z[z["n_matched_amendments"] == 0]
    sheet = pd.DataFrame({
        "code":            silent["code"],
        "name":            silent["code"].map(lib),
        "tax_code_articles": silent["articles_2026"],
        "articles_as_indexed": silent["articles_index"],
        "cost_2011":       silent["cost_2011"],
        "end_of_eligibility_2026": silent["fin_fait_generateur_2026"],
        "matching_hint":   silent["articles_index"].map(hint),
        "amendment_found_by_hand": "",          # yes / no
        "amendment_ids":   "",
        "notes":           "",
    })
    context = z[["code", "libelle", "cost_2011", "fin_fait_generateur_2026", "articles_index",
                 "only_shared_articles", "n_amend_14", "n_amend_15_17", "n_matched_amendments"]]\
        .sort_values("n_matched_amendments")

    with pd.ExcelWriter(VAL / "silent_survivors_check.xlsx", engine="openpyxl") as w:
        sheet.to_excel(w, sheet_name="silent_survivors", index=False)
        context.to_excel(w, sheet_name="all_open_score0", index=False)

    print(f"score 0: {(g['score']=='0').sum()} measures, "
          f"{g.loc[g['score']=='0','code'].isin(v26.index).sum()} listed in 2026, "
          f"{len(z)} still open, {len(silent)} with no matched amendment")
    print(f"open score-0 measures matched only through shared articles: "
          f"{int((z['only_shared_articles'] == True).sum())}")  # noqa: E712


if __name__ == "__main__":
    main()
