"""Match amendments to tax expenditures through the tax-code articles they cite.

Voies et moyens gives the legal basis (CGI articles) of each measure in each
edition; amendments cite articles in their text (`articles_strict`, from
01_parse_amendments.py). An amendment is paired with a measure when it cites
an article in that measure's legal basis, exactly as recorded (no partial
matches: "199" does not match "199 sexvicies"). When a measure's basis
changed over time, the edition closest to the deposit year is used. The
result is candidate pairs, not verified matches: one article can host
several measures (223 O hosts thirty-one), and roughly half of matched
amendments resolve to a single measure. 03_llm_verify_classify.py verifies
them.

Population: the 449 measures of the 2011 report with a six-digit code
(`numbered`), grouped in three bands by 2011 score: "0-1", "2-3",
"non évalué".

Also saves, per measure: presence in Voies et moyens 2011/2013/2019/2026,
nature of the beneficiary in 2011 (ménages/entreprises), amendment counts
(leg 14 and legs 15-17), and sunset columns (`sunset_raw`, `borne`,
`borne_2011`, `info_2011`). The candidate pairs are then checked by a
language model in 03_llm_verify_classify.py; there is no hand validation.

Inputs
    data/intermediate/vm_2009_2019.parquet, vm_2020_2026.parquet  (Voies et moyens panel)
    data/intermediate/amendments_14.parquet, amendments_15_17.parquet  (01_parse_amendments.py)
    data/intermediate/guillaume_all.csv
Outputs
    data/intermediate/measures_with_bands.csv   (449 measures, 361 with at least one amendment)
    data/intermediate/pairs_14.parquet          (11,036 pairs, 3,066 amendments, 296 measures)
    data/intermediate/pairs_15_17.parquet       (42,378 pairs, 12,179 amendments, 343 measures)
Reproduces
    Pipeline step, no thesis number directly. Printed counts in the notebook:
    3,671 of 9,303 references dropped as non-CGI; 7,163 measure-article-year
    rows, 587 distinct articles, 473 identifying a single measure, 33 pointing
    to four or more; 7,649 amendments resolving to one measure.
Source
    Master Thesis_4 Matching.ipynb, cells 2 (setup), 4 (bands, presence),
    23 (nature_2011), 25 (article index), 27 (join), 32-33 (sunset columns),
    37 (save), 40 (count of amendments resolving to one measure).
    Not included: the 40-pair sample drawn in cells 40-41 for the LLM pilot
    (archived with its coding in archive/matching_validation/).
    Dropped: cells 5-21 (early survival analysis, superseded by the Chapter 5 scripts in 2_methods/), 29, 31,
    34-35, 39 (descriptive tables, nothing saved), 42-52 (dead).
Changes from the notebook
    - Paths through src/config.py. Descriptive prints of cells 23 and 32-33
      kept short; the crosstabs that only displayed results are dropped.
Known caveats
    - amendments_15_17.parquet holds 648,213 rows with duplicated amendments
      (see 01_parse_amendments.py). The join deduplicates on
      (uid, article, measure), so the pairs are not affected.
    - Exact article matching: amendments citing a parent article ("199",
      "195") are invisible for measures recorded at a sub-article; 115
      amendments naming Censi-Bouvard among them.
    - In the join, the `sort_values("lag").drop_duplicates(...)` line is
      repeated twice in the notebook; kept (it is idempotent).
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

DATA = INTERMEDIATE

NOT_CGI = re.compile(r"\bloi\s*n[°o]|d[ée]cret|BOFIP|BOI-|\bDB\d|ordonnance|annexe", re.I)


def band(s):
    return {"0": "0-1", "1": "0-1", "2": "2-3", "3": "2-3"}.get(s, "non évalué")


def build_index(P, vm, POP):
    """Measure -> article index (cell 25)."""
    cols = ["numero", "vm_year", "reference", "articles"]
    Pn = P[cols].assign(code_ref="code général des impôts")
    src = pd.concat([Pn, vm[cols + ["code_ref"]]], ignore_index=True)

    ok = ~src["reference"].fillna("").str.contains(NOT_CGI)
    ok &= src["code_ref"].fillna("code général des impôts").str.contains(
            "g[ée]n[ée]ral des imp", case=False, regex=True)
    print(f"{(~ok).sum():,} of {len(src):,} references dropped as non-CGI")

    idx = src[ok & src["articles"].notna() & (src["articles"] != "")]
    idx = idx.assign(article=idx["articles"].str.split("|")).explode("article")
    idx["article"] = idx["article"].str.strip()
    idx = idx[idx["article"] != ""]

    amb = idx.groupby("article")["numero"].nunique()
    print(f"{len(idx):,} measure-article-year rows, {len(amb)} distinct articles")
    print(f"  {(amb==1).sum()} identify a single measure")
    print(f"  {(amb>3).sum()} point to four or more")

    idx2 = (idx[idx["numero"].isin(POP)][["numero", "vm_year", "article"]]
            .drop_duplicates().rename(columns={"numero": "measure"}))
    return idx2


def join(df, label, idx2):
    """Amendment x measure join on the cited article (cell 27)."""
    d = df[df["articles_strict"].fillna("") != ""].copy()
    d["year"] = pd.to_datetime(d["date_depot"], errors="coerce").dt.year
    d = d.assign(article=d["articles_strict"].str.split("|")).explode("article")
    d["article"] = d["article"].str.strip()
    d = d[d["article"] != ""]

    m = d.merge(idx2, on="article", how="inner")
    m["lag"] = (m["year"] - m["vm_year"]).abs()
    m = m.sort_values("lag").drop_duplicates(["uid", "article", "measure"])
    m = m.sort_values("lag").drop_duplicates(["uid", "article", "measure"])

    per = m.groupby("uid")["measure"].nunique()
    print(f"{label}: {len(m):,} pairs, {m['uid'].nunique():,} amendments, "
          f"{m['measure'].nunique()} measures "
          f"({(per==1).sum():,} resolve to a single measure)")
    return m, per


def main():
    # --- setup (cell 2) ---
    P = pd.read_parquet(DATA / "vm_2009_2019.parquet")
    vm = pd.read_parquet(DATA / "vm_2020_2026.parquet")
    am = pd.read_parquet(DATA / "amendments_15_17.parquet")
    am14 = pd.read_parquet(DATA / "amendments_14.parquet")
    gui = pd.read_csv(DATA / "guillaume_all.csv", dtype={"code": str})
    print(f"Voies et moyens : {len(P)+len(vm):,} rows, 2009–2026")
    print(f"amendments 14   : {len(am14):,}")
    print(f"amendments 15-17: {len(am):,}")
    print(f"measures        : {len(gui)}")

    # --- bands and presence (cell 4) ---
    g = gui[gui["numbered"]].copy()
    g["band"] = g["score"].map(band)
    for y in (2011, 2013, 2019, 2026):
        src = P if y < 2020 else vm
        g[f"in_{y}"] = g["code"].isin(set(src[src["vm_year"] == y]["numero"]))
    print(g["band"].value_counts().to_string())

    # --- beneficiary type in 2011 (cell 23) ---
    b11 = P[P["vm_year"] == 2011].drop_duplicates("numero").set_index("numero")
    g["nature_2011"] = (g["code"].map(b11["benef_raw"])
                        .str.extract(r"(m[ée]nages|entreprises)", flags=re.I)[0]
                        .str.lower())

    # --- article index (cell 25) and join (cell 27) ---
    POP = set(g["code"])
    idx2 = build_index(P, vm, POP)
    m14, per14 = join(am14, "leg 14    ", idx2)
    m, per = join(am, "legs 15-17", idx2)

    counts14 = m14.drop_duplicates(["uid", "measure"]).groupby("measure").size()
    counts = m.drop_duplicates(["uid", "measure"]).groupby("measure").size()
    g["n_amend_14"] = g["code"].map(counts14).fillna(0).astype(int)
    g["n_amend_15_17"] = g["code"].map(counts).fillna(0).astype(int)

    # --- sunset columns (cells 32-33) ---
    src = pd.concat([P, vm])
    sunset = (src[["numero", "vm_year", "fin_fait_generateur"]]
              .dropna(subset=["fin_fait_generateur"])
              .sort_values("vm_year")
              .drop_duplicates("numero", keep="last")
              .set_index("numero")["fin_fait_generateur"].astype(str))
    g["sunset_raw"] = g["code"].map(sunset)
    g["borne"] = ~g["sunset_raw"].fillna("").str.contains("non.?born", case=False, regex=True)

    s11 = (P[P["vm_year"] == 2011][["numero", "fin_fait"]]
           .dropna().drop_duplicates("numero").set_index("numero"))
    g["borne_2011"] = ~(g["code"].map(s11["fin_fait"]).fillna("").astype(str)
                        .str.contains("non.?born", case=False, regex=True))
    g["info_2011"] = g["code"].isin(s11.index)

    # --- save (cell 37) ---
    g.to_csv(DATA / "measures_with_bands.csv", index=False)
    m.to_parquet(DATA / "pairs_15_17.parquet", index=False)
    m14.to_parquet(DATA / "pairs_14.parquet", index=False)
    print(f"{len(g)} measures, "
          f"{(g['n_amend_14'] + g['n_amend_15_17'] > 0).sum()} with at least one amendment")

    # --- amendments resolving to one measure (cell 40) ---
    pairs = pd.concat([m14, m], ignore_index=True)
    per_all = pairs.groupby("uid")["measure"].nunique()
    print(f"{(per_all == 1).sum():,} amendments resolving to one measure")

if __name__ == "__main__":
    main()
