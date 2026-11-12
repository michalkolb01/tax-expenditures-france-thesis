"""Plenary debates, legislature 14 (2012-2017): amendment blocks from the DILA records.

Reads the DILA plenary records (compte rendu intégral, XML inside yearly .taz
archives), cuts each sitting into amendment blocks (opened by "pour soutenir
l'amendement n° ..." and closed by the italic note recording the outcome),
extracts the commission and government opinions, and links each block to an
amendment of the legislature-14 amendment dataset and through it to a
measure. The result is a corpus of texts linked to measures through
amendments; nothing here classifies the content of the debates.

Steps
    1. taz_entries (cell 26) reads the archives; parse_cri v2 (cell 39) keeps
       Para and Nota elements; outcome (cell 38) reads the outcome note;
       segment14 (cell 40, with its OPEN14) builds the blocks. Writes
       debate_blocks_14.parquet (cell 41).
    2. avis14 (cell 42): one row per block with the opinions -> debate_avis_14.parquet.
    3. Matching (cells 43, 44 [numero as str], 51, 52, 53): same number, filed
       0-60 days before the sitting; finance-bill amendments must be on the
       PLF of that budget year (sitting date, July onwards counts for the next
       year); among candidates for the same (file, number), the one whose
       exposé shares most words with the block text. Kept only if the
       amendment is in amendments_classified.csv.

Inputs
    RAW / "dila_debats" / <year> / *.taz       DILA plenary records, 2012-2017
    INTERMEDIATE / "amendments_14.parquet"      (1_data/1_3_parliamentary_corpus/2_amendments)
    INTERMEDIATE / "amendments_classified.csv"  (1_data/1_3_parliamentary_corpus/2_amendments; called
        classified_combined.csv in the notebook)
Outputs
    INTERMEDIATE / "debate_blocks_14.parquet"   paragraphs in amendment blocks
    INTERMEDIATE / "debate_avis_14.parquet"     one row per block with the opinions
    INTERMEDIATE / "debate_matched_14.parquet"  blocks linked to one amendment and a measure

Thesis numbers
    Pipeline step, no thesis number directly. debate_matched_14.parquet is NOT
    used to build turns.parquet (04_build_turns.py): legislature 14 is not in
    the speaking-turn corpus.

Source
    Master Thesis_7 Committee Debates (7_Committee.ipynb), cells 26, 38, 39,
    40, 41, 42, 43, 44 (numero cast only), 51, 52, 53. Cells 27-37 are
    exploration (cell 31 is parse_cri v1 and OPEN14 v1, replaced in cells 39
    and 40); cell 44's own match and cells 45-50 are earlier versions of
    debate_matched_14.parquet, overwritten by cell 53.
    Requires the system command `gzip` (to read old Unix .Z archives).

Changes from the notebook
    Drive paths replaced by src/config.py; notebook state passed explicitly.

Known caveats
    - Blocks are found only where the record says "pour soutenir
      l'amendement"; amendments called without that phrase are missed.
    - The PLF-year rule assumes a sitting from July onwards debates the next
      year's budget.
"""
import io
import math  # noqa: F401  (imported in cell 52)
import re
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
from collections import Counter  # noqa: F401  (imported in cell 52)
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

DILA = RAW / "dila_debats"
DATA = INTERMEDIATE


# cell 26
def taz_entries(path):
    """Yield (name, bytes) from a .taz, which may be old Unix .Z, plain tar,
    or a tar within a tar depending on the year."""
    raw = path.read_bytes()
    # old Unix compress
    if raw[:2] == b"\x1f\x9d":
        raw = subprocess.run(["gzip", "-dc"], input=raw,
                             capture_output=True).stdout
    try:
        t = tarfile.open(fileobj=io.BytesIO(raw))
    except tarfile.ReadError:
        return
    for m in t.getmembers():
        if not m.isfile():
            continue
        b = t.extractfile(m).read()
        if m.name.endswith((".tar", ".taz")):
            try:
                t2 = tarfile.open(fileobj=io.BytesIO(b))
                for m2 in t2.getmembers():
                    if m2.isfile():
                        yield m2.name, t2.extractfile(m2).read()
            except tarfile.ReadError:
                yield m.name, b
        else:
            yield m.name, b


# cell 38
OUT14 = re.compile(r"\(\s*(?:L|Le|Les)[^)]{0,20}?amendements?\b[^)]*?\)", re.I)
VERD = re.compile(r"(n['’]est pas adopté|ne sont pas adoptés|est adopté|sont adoptés|"
                  r"est retiré|sont retirés|tombe|tombent)", re.I)


def outcome(t):
    m = OUT14.search(t)
    if not m:
        return None
    seg = m.group(0)
    v = VERD.search(seg)
    nums = re.findall(r"\bn?[°o]?\s*(\d{1,5})\b", seg)
    return (nums, v.group(1) if v else None)


# cell 39 (parse_cri v2)
def parse_cri(data):
    s = data.decode("utf-8", "ignore").replace("&#128;", "&#160;")
    r = ET.fromstring(s.encode())
    meta = {t: (r.find(f".//{t}").text if r.find(f".//{t}") is not None else None)
            for t in ("dateSeance", "numSeance", "LegislatureNumero")}
    rows = []
    for el in r.iter():
        if el.tag not in ("Para", "Nota"):
            continue
        nom = el.find(".//Orateur/Nom")
        rows.append({**meta, "kind": el.tag,
                     "orateur": nom.text.strip() if nom is not None and nom.text else None,
                     "texte": " ".join("".join(el.itertext()).split())})
    return pd.DataFrame(rows)


# cell 40
OPEN14 = re.compile(r"pour soutenir l[’']amendement\s+n[°o]?\s*(\d+)", re.I)


def segment14(d):
    d = d.reset_index(drop=True)
    d["amendement"] = None
    cur_start, cur_num = None, None
    for i, r in d.iterrows():
        t = r["texte"] or ""
        m = OPEN14.search(t)
        if m:
            cur_start, cur_num = i, m.group(1)
            continue
        o = outcome(t) if r["kind"] == "Nota" else None
        if o and o[0]:
            nums, verdict = o
            if cur_start is not None:
                d.loc[cur_start:i, "amendement"] = "|".join(nums)
                d.loc[i, "verdict"] = verdict
            cur_start, cur_num = None, None
    return d


# cell 41
def run_dila(year):
    rows = []
    for f in sorted((DILA / str(year)).iterdir()):
        try:
            for name, data in taz_entries(f):
                if not name.startswith("CRI_"):
                    continue
                d = segment14(parse_cri(data))
                bb = d[d["amendement"].notna()]
                if len(bb):
                    bb = bb.copy()
                    bb["file"] = f.name
                    rows.append(bb)
        except Exception:
            continue
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_blocks():
    parts = []
    for y in range(2012, 2018):
        p = run_dila(y)
        print(f"{y}: {len(p):,} paragraphs, {p['amendement'].nunique() if len(p) else 0} blocks")
        parts.append(p)
    D14 = pd.concat(parts, ignore_index=True)
    D14.to_parquet(DATA / "debate_blocks_14.parquet", index=False)
    print(f"\n{D14['amendement'].nunique():,} blocks total")
    return D14


# cell 42
AVIS_C = re.compile(r"avis de la commission", re.I)
AVIS_G = re.compile(r"avis du [Gg]ouvernement", re.I)


def avis14(bloc):
    bloc = bloc.reset_index(drop=True)
    out = {"avis_commission": None, "qui_commission": None,
           "avis_gouvernement": None, "qui_gouvernement": None}
    for i, r in bloc.iterrows():
        if i + 1 >= len(bloc):
            continue
        nxt = bloc.iloc[i + 1]
        t = r["texte"] or ""
        if AVIS_C.search(t) and out["avis_commission"] is None:
            out["avis_commission"], out["qui_commission"] = nxt["texte"], nxt["orateur"]
        elif AVIS_G.search(t) and out["avis_gouvernement"] is None:
            out["avis_gouvernement"], out["qui_gouvernement"] = nxt["texte"], nxt["orateur"]
    return out


def build_avis(D14):
    rows = []
    for (f, num), bloc in D14.groupby(["file", "amendement"]):
        rows.append({"file": f, "amendement": num,
                     "date": bloc["dateSeance"].iloc[0],
                     "legislature": "14",
                     "n_paragraphes": len(bloc),
                     "verdict": bloc["verdict"].dropna().iloc[0] if bloc["verdict"].notna().any() else None,
                     **avis14(bloc)})
    A14 = pd.DataFrame(rows)
    print(f"{len(A14):,} blocks")
    print(f"  commission avis: {A14['avis_commission'].notna().sum():,}")
    print(f"  government avis: {A14['avis_gouvernement'].notna().sum():,}")
    A14.to_parquet(DATA / "debate_avis_14.parquet", index=False)
    return A14


# cell 52
STOP = set("""le la les de des du et en un une à au aux pour par sur dans que qui
ce cette ces est sont a ont il elle nous vous ne pas plus être avec ou son sa ses
d l n s c y""".split())


def toks(t):
    return {w for w in re.findall(r"[a-zàâçéèêëîïôûùüÿœ]{4,}", str(t).lower())
            if w not in STOP}


def pick(grp):
    """Among candidates sharing (file, numero), keep the one whose exposé
    overlaps most with the words spoken in the block."""
    spoken = toks(grp["bloc_texte"].iloc[0])
    if not spoken:
        return grp.nsmallest(1, "lag")
    sc = grp["expose"].map(lambda e: len(toks(e) & spoken) / (len(toks(e)) ** 0.5 + 1))
    return grp.assign(score=sc).nlargest(1, "score")


def match(D14, A14):
    # cell 43
    am14 = pd.read_parquet(DATA / "amendments_14.parquet").drop_duplicates("uid")
    A14["date"] = pd.to_datetime(A14["date"], errors="coerce")
    am14["date_depot"] = pd.to_datetime(am14["date_depot"], errors="coerce")

    # cell 44 (only the key cast; its match was overwritten by cell 53)
    A14["numero"] = A14["amendement"].astype(str)
    am14["numero"] = am14["numero"].astype(str)
    cl = pd.read_csv(DATA / "amendments_classified.csv", dtype={"measure": str})

    # cell 51
    A14["yr"] = A14["date"].dt.year + (A14["date"].dt.month >= 7).astype(int)
    am14["plf"] = pd.to_numeric(am14["plf_year"], errors="coerce")

    c = A14.merge(am14[["uid", "numero", "texte_ref", "date_depot", "plf", "sort"]],
                  on="numero", how="inner")
    c["lag"] = (c["date"] - c["date_depot"]).dt.days
    c = c[(c["lag"] >= 0) & (c["lag"] <= 60)]

    # a finance-bill block must match an amendment on that year's PLF
    fin = c[c["plf"].notna() & (c["plf"] == c["yr"])]
    oth = c[c["plf"].isna()]
    c2 = pd.concat([fin, oth])

    # cell 53
    bt = (D14.groupby(["file", "amendement"])["texte"]
          .apply(lambda s: " ".join(s.astype(str))[:4000]).rename("bloc_texte").reset_index())
    c3 = c2.merge(bt, left_on=["file", "numero"], right_on=["file", "amendement"], how="left")
    c3 = c3.merge(am14[["uid", "expose"]], on="uid", how="left")

    best = (c3.groupby(["file", "numero"], group_keys=False)
            .apply(pick))
    m14d = best.merge(cl[["uid", "measure", "categorie"]], on="uid")
    print(f"{len(m14d):,} blocks, {m14d['measure'].nunique()} measures")
    m14d.to_parquet(DATA / "debate_matched_14.parquet", index=False)


def main():
    D14 = build_blocks()
    A14 = build_avis(D14)
    match(D14, A14)


if __name__ == "__main__":
    main()
