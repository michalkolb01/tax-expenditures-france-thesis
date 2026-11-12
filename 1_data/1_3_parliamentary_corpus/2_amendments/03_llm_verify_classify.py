"""Verify the amendment-measure pairs with an LLM and classify each amendment's direction.

Article matching (02_match_articles.py) gives candidate pairs, not verified
matches: one article often hosts several distinct provisions (278 bis-5°
fertilisers, 278 bis-4° animal feed). The model (claude-sonnet-4-5) reads
each amendment's dispositif and exposé sommaire, with the article-40
compensation clause removed, and

1. single-article pass: for the 7,649 amendments that resolve to one
   measure, decides whether the amendment really concerns that measure
   (PERTINENT: oui|non) and classifies its direction (CATEGORIE:
   supprime|restreint|etend|maintient|technique|autre). Prompt:
   prompt_verify_single.txt.
2. multi-article pass: for the 7,596 amendments citing an article shared by
   several measures, shows up to 8 candidate measures (letters A-H) and asks
   which one, if any, the amendment concerns (MESURE: letter or AUCUNE),
   with the same categories. Prompt: prompt_choose_measure.txt.
3. combine: accepted single-article pairs (pertinent == "oui") and resolved
   multi-article pairs (measure not null), one row per amendment.

"etend" / "restreint" are defined by revenue forgone: lowering a reduced
rate from 10% to 5.5% extends the tax expenditure. "maintient" = opposes a
removal proposed elsewhere in the bill.

Both passes append to their CSV every 50 rows and skip uids already done, so
an interrupted run resumes. With complete CSVs in place, the script makes no
API call and only rebuilds the combined file.

Inputs
    data/intermediate/vm_2009_2019.parquet, vm_2020_2026.parquet
    data/intermediate/pairs_14.parquet, pairs_15_17.parquet   (02_match_articles.py)
    1_data/1_3_parliamentary_corpus/2_amendments/prompt_verify_single.txt, prompt_choose_measure.txt
    Environment variable ANTHROPIC_API_KEY (only if some rows remain to classify)
Outputs
    data/intermediate/classified_all.csv     (7,649 rows: 4,903 pertinent = oui, 2,746 non)
    data/intermediate/classified_multi.csv   (7,596 rows, 2,958 resolved to a measure)
    data/intermediate/amendments_classified.csv  (7,861 amendments, 272 measures)
Reproduces
    Pipeline step. amendments_classified.csv is the file used by
    2_methods/2_5_pairs/01_pair_search.py (amendments to remove or narrow measures).
    Category counts in the thesis run: single-article etend 3,367,
    restreint 998, supprime 216, technique 205, maintient 109; multi-article
    (resolved) etend 2,345, restreint 346, supprime 109, maintient 89,
    technique 64.
Source
    Master Thesis_5 Classification.ipynb, cells 2 (setup), 4 (pairs, solo,
    lib), 6 (PROMPT, strip_gage, strip_accents, classify), 13 (single-article
    run -> classified_all.csv), 20 (CHOICE_PROMPT), 21 (helpers, same as
    cell 6), 22 (classify_choice), 23 (setup and candidates for the
    multi-article pass), 25 (LETTERS), 26 (multi-article run ->
    classified_multi.csv), 27 (combine -> classified_combined.csv).
    Dropped: cells 8 and 10 (40-pair pilot, exploratory), 11 (descriptive),
    15 (classification_meta.json, see caveats), 18, 19 and 24 (superseded
    multi-article runs: cell 19 wrote the first 600 rows; cell 24 failed with
    a code error on the 6,996 others, rows that cell 26 dropped and redid),
    28-38 (chapter-5 analysis).
Changes from the notebook
    - Paths through src/config.py; API key from os.environ["ANTHROPIC_API_KEY"]
      (the notebook used the Colab secret ANTHROPIC_KEY); prompts loaded from
      the .txt files, verbatim.
    - The notebook used one name `lib` for two objects: a DataFrame
      (libelle, reference) in the single-article pass (cell 4) and a Series of
      libelle in the multi-article pass (cell 23). Here they are passed
      explicitly to classify() and classify_choice() as `lib`; same content.
    - Cell 26 started by dropping rows of classified_multi.csv with no raw
      output (rows that failed with a code error) so they are retried; it
      read the file unconditionally. Here this is skipped when the file does
      not exist yet.
    - The client is created only when some rows remain to classify.
    - The combined file is written as amendments_classified.csv (the notebook
      wrote classified_combined.csv; the rename to the package name was done
      by hand outside the notebooks).
Known caveats
    - The first 600 rows of classified_multi.csv in the thesis run predate the
      code shown here: written by an earlier version of the loop (cell 19,
      possibly with an earlier classify_choice) and kept by cell 26 because
      they had a raw output. A fresh run may differ on them.
    - Temperature was not set (the installed SDK rejected the parameter), so
      labels cannot be regenerated identically; the labelled files are the
      record.
    - Cell 15 wrote classification_meta.json with validation figures typed in
      by hand (precision 0.78 before / 0.98 after the filter, direction
      agreement 0.92, coverage counts) and no cell computing them. Not
      reproduced here. The validation of the final corpus (40 accepted pairs
      coded by hand) is not in any notebook.
    - The 40-pair pilot (cells 8 and 10) is left out. Its "hand coding" file
      (precision_40_v3_coded.csv) names the human judgement column
      `claude_relevant`, which suggests it was not (only) coded by hand.
"""
import os
import re
import sys
import time  # noqa: F401  (imported in the notebook setup)
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
DATA = INTERMEDIATE
MODEL = "claude-sonnet-4-5"
PROMPT = (HERE / "prompt_verify_single.txt").read_text(encoding="utf-8")
CHOICE_PROMPT = (HERE / "prompt_choose_measure.txt").read_text(encoding="utf-8")

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MAX_CAND = 8

GAGE = re.compile(
    r"(?:La perte|Les pertes|La perte éventuelle|Cette perte)\s+de\s+recettes.*?$",
    re.I | re.S)

_client = None


def get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def strip_gage(s):
    return re.sub(r"\s+", " ", GAGE.sub("", str(s) if pd.notna(s) else "")).strip()


def strip_accents(s):
    if not s:
        return s
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


# ---------------------------------------------------------------------------
# Single-article pass (cells 4, 6, 13)
# ---------------------------------------------------------------------------
def classify(row, lib):
    """lib: DataFrame indexed by numero with libelle and reference (cell 4)."""
    r = lib.loc[row["measure"]] if row["measure"] in lib.index else None
    p = PROMPT.format(
        code=row["measure"],
        label=str(r["libelle"] if r is not None else "?")[:160],
        ref=str(r["reference"] if r is not None else "?")[:80],
        dispositif=strip_gage(row["dispositif"])[:1500],
        expose=strip_gage(row["expose"])[:1200])

    msg = get_client().messages.create(
        model=MODEL, max_tokens=300,
        messages=[{"role": "user", "content": p}])
    out = msg.content[0].text

    per_ = re.search(r"(?:pertinent|r[ée]ponse)\s*:\s*(oui|non)", out, re.I)
    cat = re.search(r"cat[ée]gorie\s*:\s*(\w+)", out, re.I)
    ana = re.search(r"analyse\s*:\s*(.*?)$", out, re.I | re.S)
    return {"pertinent": per_.group(1).lower() if per_ else None,
            "categorie": strip_accents(cat.group(1)) if cat else None,
            "analyse":   ana.group(1).strip() if ana else None,
            "raw": out}


def single_pass(P, vm, pairs):
    per = pairs.groupby("uid")["measure"].nunique()
    solo = pairs[pairs["uid"].map(per) == 1].drop_duplicates("uid")
    lib = (pd.concat([P[["numero", "vm_year", "libelle", "reference"]],
                      vm[["numero", "vm_year", "libelle", "reference"]]])
             .sort_values("vm_year").drop_duplicates("numero", keep="last")
             .set_index("numero"))
    print(f"{len(pairs):,} pairs, {len(solo):,} resolving to one measure, "
          f"{solo['measure'].nunique()} measures")

    OUT = DATA / "classified_all.csv"
    done = set(pd.read_csv(OUT)["uid"]) if OUT.exists() else set()
    todo = solo[~solo["uid"].isin(done)].reset_index(drop=True)
    print(f"{len(done):,} already done, {len(todo):,} to go")

    buf = []
    for i, r in todo.iterrows():
        try:
            out = classify(r, lib)
        except Exception as e:
            out = {"pertinent": None, "categorie": None,
                   "analyse": f"ERROR {type(e).__name__}: {e}", "raw": ""}
        buf.append({"uid": r["uid"], "measure": r["measure"],
                    "article": r["article"], "date_depot": r["date_depot"],
                    "sort": r.get("sort"), **out})

        if len(buf) >= 50 or i == len(todo) - 1:
            pd.DataFrame(buf).to_csv(OUT, mode="a", header=not OUT.exists(),
                                     index=False)
            buf = []
            print(f"  {i+1:,}/{len(todo):,}")

    res_all = pd.read_csv(OUT)
    print(f"\n{len(res_all):,} classified")
    print(res_all["pertinent"].value_counts(dropna=False).to_string())
    print(res_all["categorie"].value_counts(dropna=False).to_string())


# ---------------------------------------------------------------------------
# Multi-article pass (cells 20-26)
# ---------------------------------------------------------------------------
def classify_choice(row, lib):
    """lib: Series libelle indexed by numero (cell 23)."""
    ms = list(row["measures"])[:MAX_CAND]
    opts = "\n".join(f"{LETTERS[i]}. {m} — {str(lib.get(m,'?'))[:90]}"
                     for i, m in enumerate(ms))
    p = CHOICE_PROMPT.format(article=row["article"], options=opts,
                             dispositif=strip_gage(row["dispositif"])[:1500],
                             expose=strip_gage(row["expose"])[:1200])
    out = get_client().messages.create(model=MODEL, max_tokens=300,
            messages=[{"role": "user", "content": p}]).content[0].text
    mm = re.search(r"mesure\s*:\s*([A-Z]+)", out, re.I)
    cat = re.search(r"cat[ée]gorie\s*:\s*(\w+)", out, re.I)
    ana = re.search(r"analyse\s*:\s*(.*?)$", out, re.I | re.S)
    pick = mm.group(1).upper() if mm else None
    measure = (ms[LETTERS.index(pick)]
               if pick and len(pick) == 1 and LETTERS.index(pick) < len(ms) else None)
    return {"chosen": pick, "measure": measure, "n_shown": len(ms),
            "categorie": strip_accents(cat.group(1)) if cat else None,
            "analyse": ana.group(1).strip() if ana else None, "raw": out}


def multi_pass(P, vm, pairs):
    lib = (pd.concat([P[["numero", "vm_year", "libelle"]], vm[["numero", "vm_year", "libelle"]]])
             .sort_values("vm_year").drop_duplicates("numero", keep="last")
             .set_index("numero")["libelle"])

    per = pairs.groupby("uid")["measure"].nunique()
    multi = pairs[pairs["uid"].map(per) > 1].copy()
    multi["n_cand"] = multi["uid"].map(per)

    cand = (multi.groupby("uid")
                 .agg(article=("article", "first"),
                      measures=("measure", lambda s: sorted(set(s))),
                      n_cand=("n_cand", "first"),
                      dispositif=("dispositif", "first"),
                      expose=("expose", "first"))
                 .reset_index().drop_duplicates("uid"))

    OUT2 = DATA / "classified_multi.csv"

    # drop the rows that failed with a code error so they get retried
    if OUT2.exists():
        r2 = pd.read_csv(OUT2)
        good = r2[r2["raw"].notna()]
        print(f"keeping {len(good):,} of {len(r2):,}")
        good.to_csv(OUT2, index=False)

    done = set(pd.read_csv(OUT2)["uid"]) if OUT2.exists() else set()
    todo = cand[~cand["uid"].isin(done)].reset_index(drop=True)
    print(f"{len(cand):,} candidates; {len(done):,} done, {len(todo):,} to go")

    buf = []
    for i, r in todo.iterrows():
        try:
            out = classify_choice(r, lib)
        except (NameError, AttributeError, KeyError, TypeError, IndexError):
            raise                       # a bug, not a bad row — stop now
        except Exception as e:
            out = {"chosen": None, "measure": None, "n_shown": None,
                   "categorie": None,
                   "analyse": f"ERROR {type(e).__name__}: {e}", "raw": ""}
        buf.append({"uid": r["uid"], "article": r["article"],
                    "n_cand": r["n_cand"],
                    "candidates": "|".join(r["measures"]), **out})
        if len(buf) >= 50 or i == len(todo) - 1:
            pd.DataFrame(buf).to_csv(OUT2, mode="a", header=not OUT2.exists(), index=False)
            buf = []
            print(f"  {i+1:,}/{len(todo):,}")

    r2 = pd.read_csv(OUT2)
    print(f"\n{len(r2):,} classified, {r2['measure'].notna().sum():,} resolved to a measure")
    print(r2["categorie"].value_counts(dropna=False).to_string())


# ---------------------------------------------------------------------------
# Combine (cell 27)
# ---------------------------------------------------------------------------
def combine():
    p1 = pd.read_csv(DATA / "classified_all.csv", dtype={"measure": str})
    p2 = pd.read_csv(DATA / "classified_multi.csv", dtype={"measure": str})

    a = p1[p1["pertinent"] == "oui"][["uid", "measure", "categorie", "analyse"]].copy()
    a["pass"] = "single-article"

    b = p2[p2["measure"].notna()][["uid", "measure", "categorie", "analyse"]].copy()
    b["pass"] = "multi-article"

    allc = pd.concat([a, b], ignore_index=True).drop_duplicates("uid")
    allc.to_csv(DATA / "amendments_classified.csv", index=False)

    print(f"{len(allc):,} classified amendments, {allc['measure'].nunique()} measures")
    print(allc.groupby("pass")["categorie"].value_counts().unstack(fill_value=0).to_string())


def main():
    P = pd.read_parquet(DATA / "vm_2009_2019.parquet")
    vm = pd.read_parquet(DATA / "vm_2020_2026.parquet")
    pairs = pd.concat([pd.read_parquet(DATA / "pairs_14.parquet"),
                       pd.read_parquet(DATA / "pairs_15_17.parquet")], ignore_index=True)
    single_pass(P, vm, pairs)
    multi_pass(P, vm, pairs)
    combine()


if __name__ == "__main__":
    main()
