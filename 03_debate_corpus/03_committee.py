"""Finance Committee minutes: amendment blocks and their link to measures.

Cuts the Finance Committee minutes (comptes rendus, HTML) into blocks, one
per amendment examined: a block opens on "La commission examine / est
saisie ..." or "Amendement(s) CF ..." and closes on "La commission adopte /
rejette ...". Blocks are linked to amendments by their CF number (and the
PLF year), and through them to a measure. The result is a corpus of texts
linked to measures through amendments; nothing here classifies the content
of the debates.

Steps
    1. Legislatures 15-17, parse_cr v2 (cell 8) -> committee_blocks.parquet (cell 9).
    2. Legislatures 15-17, re-parse with the improved CLOSE pattern (cell 21,
       restated in cell 23, which also accepts "Suivant l'avis ..., la
       commission adopte ...") and match on CF number + legislature + PLF
       year, keeping only (minute, number) pairs with exactly one amendment
       -> committee_matched.parquet (cell 23).
    3. Legislature 14, patterns of cell 62, parse_cr14 (cell 65) ->
       committee_blocks_14.parquet; date and PLF year read from the minute
       (cell 66); match on CF number + PLF year (cell 67) ->
       committee_matched_14.parquet.

Inputs
    ROOT / "00_acquisition" / "manifests" / "manifest_committee.csv"      list of leg 15-17 minutes (00_acquisition)
    RAW / "committee_cr" / <cr>.html    leg 15-17 minutes (00_acquisition)
    ROOT / "00_acquisition" / "manifests" / "manifest_committee_14.csv"   list of leg 14 minutes (00_acquisition)
    RAW / "committee_cr_14" / <file>    leg 14 minutes (00_acquisition)
    INTERMEDIATE / "amendments_15_17.parquet", "amendments_14.parquet" (02_amendments)
    INTERMEDIATE / "amendments_classified.csv"  (02_amendments; called
        classified_combined.csv in the notebook)
Outputs
    INTERMEDIATE / "committee_blocks.parquet"      blocks, leg 15-17 (parse_cr v2)
    INTERMEDIATE / "committee_matched.parquet"     blocks linked to an amendment and a measure, leg 15-17
    INTERMEDIATE / "committee_blocks_14.parquet"   blocks, leg 14
    INTERMEDIATE / "committee_matched_14.parquet"  blocks linked to an amendment and a measure, leg 14

Thesis numbers
    Pipeline step, no thesis number directly. committee_matched.parquet feeds
    04_build_turns.py; committee_matched_14.parquet is not used downstream.

Source
    Master Thesis_7 Committee Debates (7_Committee.ipynb), cells 8, 9 (leg
    15-17 blocks), 21 + 23 (leg 15-17 matching), 62, 65, 66, 67 (leg 14).
    The downloads (cells 4-5 and 60, with the cells listing the leg-14
    files, which write the manifests) belong to
    00_acquisition. Cell 6 (parse_cr v1), cell 10 (first committee_matched,
    overwritten by cell 23), cells 11-20 (diagnostics, validation samples,
    a parse_cr v3 in cell 18), 61, 63, 64 (exploration) are not kept.
    Requires beautifulsoup4.

Changes from the notebook
    - Drive paths replaced by src/config.py; the manifests are read from
      disk instead of the in-memory frames of cells 5 and 60.
    - Step 1: the legislature is cast to str (str(r["legislature"])), as in
      cell 23, because reading the manifest from CSV makes it an integer;
      in the notebook it was already a string in memory.

Known caveats
    - AMBIGUITY: committee_blocks.parquet was written only once, by cell 9,
      with parse_cr v2 (cell 8, CLOSE without the "Suivant l'avis ..."
      variant). committee_matched.parquet (cell 23, 879 rows in the final
      run) re-parses the minutes with the improved CLOSE but does not save
      those blocks. The two files therefore rest on slightly different block
      boundaries; committee_blocks.parquet is not the exact block set behind
      committee_matched.parquet (and so behind the committee turns in
      turns.parquet, which are cut from committee_matched's own text).
    - Only (minute, CF number) pairs that resolve to exactly one amendment
      are kept.
    - Leg 14: the PLF year of a minute is the first "projet de loi de
      finances pour YYYY" found in it.
"""
import re
import sys
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

CR = RAW / "committee_cr"
CR14 = RAW / "committee_cr_14"
DATA = INTERMEDIATE


# ---------------------------------------------------------------- step 1
# cell 8 (parse_cr v2)
OPEN_L15_V2 = re.compile(r"^La commission\s+(examine|est saisie)", re.I)
OPEN_L17_V2 = re.compile(r"^Amendements?\s+", re.I)
CLOSE_V2 = re.compile(r"^La commission\s+(adopte|rejette|approuve)", re.I)
REF_V2 = re.compile(r"\b((?:I{1,2}\s*[-‑]\s*)?CF\s*\d+)", re.I)


def parse_cr_v2(path, meta):
    s = BeautifulSoup(path.read_bytes(), "html.parser")
    txt = [p.get_text(" ", strip=True) for p in s.find_all("p") if p.get_text(strip=True)]
    blocks, cur = [], None
    for t in txt:
        opens = (OPEN_L15_V2.match(t) or OPEN_L17_V2.match(t)) and REF_V2.search(t)
        if opens:
            if cur:
                blocks.append(cur)
            cur = {**meta,
                   "amendements": [re.sub(r"[\s‑-]", "", a).upper() for a in REF_V2.findall(t)],
                   "entete": t[:250], "paras": [], "decision": None}
        elif cur is not None:
            if CLOSE_V2.match(t):
                cur["decision"] = t[:250]
                blocks.append(cur)
                cur = None
            else:
                cur["paras"].append(t)
    if cur:
        blocks.append(cur)
    return blocks


# cell 9
def committee_blocks(M):
    rows = []
    for i, r in M[M["status"] == "ok"].reset_index(drop=True).iterrows():
        p = CR / f"{r['cr']}.html"
        if not p.exists():
            continue
        try:
            rows += parse_cr_v2(p, {"cr": r["cr"], "legislature": str(r["legislature"]),
                                    "date": r["date"]})
        except Exception as e:
            print(f"  {r['cr']}: {type(e).__name__}")
        if i % 50 == 0:
            print(f"  {i}/237")

    B = pd.DataFrame(rows)
    B["texte"] = B["paras"].map(lambda ps: " ".join(ps))
    B["n_paras"] = B["paras"].map(len)
    B["amd"] = B["amendements"].map(lambda a: "|".join(a))
    B = B.drop(columns=["paras", "amendements"])

    print(f"\n{len(B):,} committee blocks")
    print(B.groupby("legislature").size().to_string())
    print(B["n_paras"].describe()[["min", "50%", "max"]].to_string())
    B.to_parquet(DATA / "committee_blocks.parquet", index=False)


# ---------------------------------------------------------------- step 2
# cells 21 + 23 (improved CLOSE)
OPEN_L15 = re.compile(r"^La commission\s+(examine|est saisie)", re.I)
OPEN_L17 = re.compile(r"^Amendements?\s+", re.I)
CLOSE = re.compile(r"^(?:Suivant l[’']avis[^,]{0,60},\s*)?[Ll]a commission\s+"
                   r"(adopte|rejette|approuve)", re.I)
REF = re.compile(r"\b((?:I{1,2}\s*[-‑]\s*)?CF\s*\d+)", re.I)


def norm(s):
    return re.sub(r"[\s‑\-]", "", s).upper()


def parse_cr(path, meta):
    s = BeautifulSoup(path.read_bytes(), "html.parser")
    txt = [p.get_text(" ", strip=True) for p in s.find_all("p") if p.get_text(strip=True)]
    out, cur = [], None
    for t in txt:
        if (OPEN_L15.match(t) or OPEN_L17.match(t)) and REF.search(t):
            if cur:
                out.append(cur)
            cur = {**meta, "amendements": [norm(a) for a in REF.findall(t)],
                   "entete": t[:250], "paras": [], "decision": None}
        elif cur is not None:
            if CLOSE.match(t):
                cur["decision"] = t[:250]
                out.append(cur)
                cur = None
            else:
                cur["paras"].append(t)
    if cur:
        out.append(cur)
    return out


def committee_matched(M):
    am = pd.read_parquet(DATA / "amendments_15_17.parquet").drop_duplicates("uid")
    cl = pd.read_csv(DATA / "amendments_classified.csv", dtype={"measure": str})

    rows = []
    for i, r in M[M["status"] == "ok"].reset_index(drop=True).iterrows():
        p = CR / f"{r['cr']}.html"
        if p.exists():
            rows += parse_cr(p, {"cr": r["cr"], "legislature": str(r["legislature"]),
                                 "date": r["date"]})
        if i % 60 == 0:
            print(f"  {i}/237")

    B = pd.DataFrame(rows)
    B["texte"] = B["paras"].map(" ".join)
    B["n_paras"] = B["paras"].map(len)
    B["amd"] = B["amendements"].map("|".join)
    B = B.drop(columns=["paras", "amendements"])
    print(f"\n{len(B):,} blocks, decision captured on {B['decision'].notna().mean():.0%}")

    # PLF year on both sides
    am["date_depot"] = pd.to_datetime(am["date_depot"], errors="coerce")
    am["plf"] = am["date_depot"].dt.year + (am["date_depot"].dt.month >= 7).astype(int)
    am["key"] = am["numero_long"].fillna("").map(norm)
    am["legislature"] = am["legislature"].astype(str)

    odj = M.set_index("cr")["odj"]
    B["plf"] = pd.to_numeric(B["cr"].map(odj)
                             .str.extract(r"finances\s+(?:rectificative\s+)?pour\s+(\d{4})")[0],
                             errors="coerce")

    ex = B.assign(a=B["amd"].str.split("|")).explode("a")
    ex = ex[ex["a"].notna() & (ex["a"] != "")]

    j = ex.merge(am[["uid", "key", "legislature", "plf", "texte_ref", "sort"]],
                 left_on=["a", "legislature", "plf"],
                 right_on=["key", "legislature", "plf"], how="inner")
    n = j.groupby(["cr", "a"])["uid"].nunique()
    j = j[j.set_index(["cr", "a"]).index.isin(set(n[n == 1].index))]

    mm = j.merge(cl[["uid", "measure", "categorie"]], on="uid")
    print(f"{len(mm):,} blocks reach a classified amendment, {mm['measure'].nunique()} measures")
    mm.to_parquet(DATA / "committee_matched.parquet", index=False)


# ---------------------------------------------------------------- step 3
# cell 62
OPEN14C = re.compile(
    r"^(?:Puis,?\s+)?(?:La Commission|Elle)\s+"
    r"(?:examine|est saisie|étudie|en vient|adopte également)", re.I)
CLOSE14C = re.compile(
    r"^(?:Puis,?\s*)?(?:Suivant l[’']avis[^,]{0,80},\s*)?"
    r"(?:La Commission|elle)\s+(adopte|rejette)\s+(?:l[’']|les\s+|le\s+)?amendement"
    r"|^L[’']amendement\s+CF\s*\d+\s+est\s+retiré", re.I)
REF14 = re.compile(r"\bCF\s*(\d+)", re.I)


# cell 65
def parse_cr14(path, meta):
    s = BeautifulSoup(path.read_bytes(), "html.parser")
    txt = [x.get_text(" ", strip=True) for x in s.find_all(["p", "div"])
           if x.get_text(strip=True)]
    out, cur = [], None
    for t in txt:
        if OPEN14C.match(t) and REF14.search(t):
            if cur:
                out.append(cur)
            cur = {**meta, "amendements": REF14.findall(t),
                   "entete": t[:250], "paras": [], "decision": None}
        elif cur is not None:
            if CLOSE14C.match(t):
                cur["decision"] = t[:250]
                out.append(cur)
                cur = None
            else:
                cur["paras"].append(t)
    if cur:
        out.append(cur)
    return out


# cell 66
DATE_RE = re.compile(r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+"
                     r"(\d{1,2})\s+(\w+)\s+(\d{4})", re.I)
PLF_RE = re.compile(r"projet de loi de finances(?:\s+rectificative)?\s+pour\s+(\d{4})", re.I)


def committee_14(M14):
    # cell 65
    rows = []
    for i, r in M14.reset_index(drop=True).iterrows():
        p = CR14 / r["path"]
        if p.exists():
            rows += parse_cr14(p, {"session": r["session"], "path": r["path"]})
        if i % 100 == 0:
            print(f"  {i}/{len(M14)}")

    B14 = pd.DataFrame(rows)
    B14["texte"] = B14["paras"].map(" ".join)
    B14["n_paras"] = B14["paras"].map(len)
    B14["amd"] = B14["amendements"].map(lambda a: "|".join(f"CF{x}" for x in a))
    B14 = B14.drop(columns=["paras", "amendements"])
    print(f"\n{len(B14):,} blocks, decision on {B14['decision'].notna().mean():.0%}")
    print(B14["n_paras"].describe()[["min", "50%", "max"]].to_string())
    B14.to_parquet(DATA / "committee_blocks_14.parquet", index=False)

    # cell 66
    meta = []
    for _, r in M14.iterrows():
        p = CR14 / r["path"]
        if not p.exists():
            continue
        s = p.read_bytes().decode("utf-8", "ignore")
        d = DATE_RE.search(s)
        y = PLF_RE.search(s)
        meta.append({"path": r["path"],
                     "date_txt": d.group(0) if d else None,
                     "year": int(d.group(4)) if d else None,
                     "plf": int(y.group(1)) if y else None})
    MT = pd.DataFrame(meta)
    print(f"{MT['date_txt'].notna().sum()} with a date, {MT['plf'].notna().sum()} naming a PLF")

    # cell 67
    am14 = pd.read_parquet(DATA / "amendments_14.parquet").drop_duplicates("uid")
    am14["key"] = (am14["numero_long"].fillna("")
                   .str.replace(r"[\s‑\-]", "", regex=True).str.upper())
    am14["plf"] = pd.to_numeric(am14["plf_year"], errors="coerce")

    B14 = B14.merge(MT[["path", "plf", "year"]], on="path", how="left")
    ex = B14.assign(a=B14["amd"].str.split("|")).explode("a")
    ex = ex[ex["a"].notna() & (ex["a"] != "")]
    ex["a"] = ex["a"].str.replace(r"\s", "", regex=True).str.upper()

    j = ex.merge(am14[["uid", "key", "plf", "texte_ref", "sort"]],
                 left_on=["a", "plf"], right_on=["key", "plf"], how="inner")
    n = j.groupby(["path", "a"])["uid"].nunique()
    j = j[j.set_index(["path", "a"]).index.isin(set(n[n == 1].index))]
    print(f"{len(j):,} unambiguous, {j['uid'].nunique():,} amendments")

    cl = pd.read_csv(DATA / "amendments_classified.csv", dtype={"measure": str})
    m14c = j.merge(cl[["uid", "measure", "categorie"]], on="uid")
    print(f"{len(m14c):,} reach a classified amendment, {m14c['measure'].nunique()} measures")
    m14c.to_parquet(DATA / "committee_matched_14.parquet", index=False)


def main():
    M = pd.read_csv(ROOT / "00_acquisition" / "manifests" / "manifest_committee.csv")
    committee_blocks(M)
    committee_matched(M)
    M14 = pd.read_csv(ROOT / "00_acquisition" / "manifests" / "manifest_committee_14.csv")
    committee_14(M14)


if __name__ == "__main__":
    main()
