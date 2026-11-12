"""Section 6.2.2 - References to the 2011 evaluation in the complete record.

Step 1 of 2: broad automatic search of the COMPLETE raw transcripts
(plenary 2011-2026, Finance Committee 2012-2026). Step 2 is a manual
reading of every candidate (column 'keep' in
data/evaluation2011_candidates_RAW_reviewed.csv; see 02_analyse_references.py).

Why a broad search: speakers rarely name the report. They refer to "the
evaluation committee", to "the 2011 evaluation", to a measure "scored zero",
to the inspectorate that staffed the committee, or to its chair. The
patterns below catch all of these; the manual reading removes the false
positives (the CICE monitoring committee, the Assembly's own evaluation
committee, other reports by the inspectorate, and so on).

Inputs
    data/raw/dila_debats/**/*.taz               plenary, DILA, 2011-2017
    data/raw/an_portal/debats_leg1[567].xml.zip  plenary, Assembly open data, 2017-2026
    data/intermediate/committee_blocks*.parquet  Finance Committee minutes, 2012-2026

Rules
    - A speech naming the evaluation several times counts once (matches less
      than 700 characters apart).
    - Candidates are deduplicated on the sitting date and a stretch of text,
      so a speech present in two overlapping files counts once.
    - Bodies with similar names are excluded automatically (EXCLUDE).

Validation (known-item test)
    The reference read in full in the sitting of 17 October 2013 (debate on
    the school-fee reductions) must be found. It is (printed at the end).

Output
    data/evaluation2011_candidates_RAW.csv  (218 candidates in the thesis run)
Printed in the run of 11 November 2026
    1. DILA: 817 files, 0 failed, 113 candidates
    2. Portal: 3 archives, 96 candidates
    3. Committee: 13 candidates
    Total: 218 candidates; known item (17 Oct 2013) found: True

Thesis text: section 6.2.2.
"""
import glob, gzip, io, os, re, subprocess, sys, tarfile, zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE  # noqa: E402

OUT = Path(__file__).resolve().parent / "data"

PATTERNS = {
    "committee or report named": r"comité d.évaluation des dépenses fiscales|rapport Guillaume|comité Guillaume|mission Guillaume|Henri Guillaume",
    "evaluation committee": r"comité d.évaluation(?! et de contrôle)(?! des réformes)(?! de la réforme)",
    "inspectorate and 2011": r"(Inspection générale des finances|\bIGF\b).{0,150}2011|2011.{0,150}(Inspection générale des finances|\bIGF\b)",
    "2011 and a score": r"2011.{0,120}(not[ée]e?s?\b|\bnote\b|score|« zéro »|nulle)|(not[ée]e?s?\b|\bnote\b|score).{0,120}2011",
    "evaluation of niches in 2011": r"évaluation (de toutes |des )?(les |des )?(niches|dépenses fiscales).{0,60}2011|2011.{0,60}évaluation (de toutes |des )?(les |des )?(niches|dépenses fiscales)",
    "score out of three": r"(note|noté|notée|notées|score)\s+(de\s+|d.)?(0|zéro|1|un|2|deux|3|trois)\s+sur\s+(3|trois)\b|échelle (allant )?de (0|zéro) à (3|trois)",
}
RX = {k: re.compile(v, re.I | re.S) for k, v in PATTERNS.items()}
EXCLUDE = re.compile(r"rapport Guillaume sur la technologie|comité d.évaluation et de contrôle|fiscalité du capital|"
                     r"condition militaire|produits de santé|France relance|ordonnances travail", re.I)


def strip_xml(b):
    t = b.decode("utf-8", errors="ignore")
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&nbsp;|&#160;|&#xa0;", " ", t)
    return re.sub(r"\s+", " ", t)


def find_date(raw_text, name=""):
    """Sitting date as YYYYMMDD: from the XML header if possible, else from the file name."""
    head = raw_text[:20000]
    m = (re.search(r"[Dd]ate_?[Ss]eance[^>]*>\s*(20[12]\d)-?(\d{2})-?(\d{2})", head)
         or re.search(r"(20[12]\d)-(\d{2})-(\d{2})", head)
         or re.search(r"(20[12]\d)(\d{2})(\d{2})\d{6,9}", head))
    if m:
        return "".join(m.groups())
    m = re.search(r"(20[12]\d)(\d{2})(\d{2})", name)
    return "".join(m.groups()) if m else ""


def scan(text, source, date):
    """One candidate per speech (matches less than 700 characters apart count once)."""
    out, last = [], -10**9
    hits = sorted((m.start(), name) for name, r in RX.items() for m in r.finditer(text))
    for pos, name in hits:
        if pos - last < 700:
            continue
        win = text[max(0, pos - 400):pos + 400]
        if EXCLUDE.search(win):
            continue
        last = pos
        out.append({"source": source, "date": date, "pattern": name, "excerpt": win, "keep": ""})
    return out


def open_taz(path):
    """DILA .taz = tar compressed with Unix 'compress' (.Z); gzip -dc decompresses it."""
    raw = open(path, "rb").read()
    if raw[:2] == b"\x1f\x9d":
        raw = subprocess.run(["gzip", "-dc"], input=raw, capture_output=True).stdout
    elif raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return tarfile.open(fileobj=io.BytesIO(raw))


def main():
    rows, errors = [], []
    taz_files = sorted(glob.glob(str(RAW / "dila_debats" / "**" / "*.taz"), recursive=True))
    for f in taz_files:
        try:
            with open_taz(f) as tar:
                for m in tar.getmembers():
                    if m.isfile():
                        raw = tar.extractfile(m).read()
                        date = find_date(raw.decode("utf-8", "ignore"), os.path.basename(f))
                        rows += scan(strip_xml(raw), "floor DILA " + os.path.basename(f), date)
        except Exception as e:  # noqa: BLE001
            errors.append((os.path.basename(f), str(e)[:100]))
    print(f"1. DILA: {len(taz_files)} files, {len(errors)} failed, {len(rows)} candidates so far")

    n0 = len(rows)
    portal_files = sorted(glob.glob(str(RAW / "an_portal" / "debats_leg1[567].xml.zip")))
    for f in portal_files:
        with zipfile.ZipFile(f) as z:
            for n in z.namelist():
                if n.endswith(".xml"):
                    raw = z.read(n)
                    date = find_date(raw.decode("utf-8", "ignore"), n)
                    rows += scan(strip_xml(raw), "floor portal " + os.path.basename(n), date)
    print(f"2. Portal: {len(portal_files)} archives, {len(rows) - n0} candidates")

    n0 = len(rows)
    for f in glob.glob(str(INTERMEDIATE / "committee_blocks*.parquet")):
        d = pd.read_parquet(f)
        dc = next((c for c in ["date", "session"] if c in d.columns), None)
        for _, r in d.iterrows():
            rows += scan(str(r["texte"]), "committee " + os.path.basename(f), str(r[dc]) if dc else "")
    print(f"3. Committee: {len(rows) - n0} candidates")

    g = pd.DataFrame(rows)
    g["key"] = g["date"].astype(str).str[:8] + g["excerpt"].str[350:470]
    g = g.drop_duplicates("key").drop(columns="key").sort_values("date").reset_index(drop=True)
    g.to_csv(OUT / "evaluation2011_candidates_RAW.csv", index=False)
    print(f"\nTotal: {len(g)} candidates written to evaluation2011_candidates_RAW.csv")
    print(g.groupby("pattern").size().to_string())

    known = g[g["date"].astype(str).str.startswith("20131017")]
    print("\nKnown item (17 Oct 2013) found:", len(known) > 0)
    print("\nNext step: read every candidate and fill 'keep' (1 = genuine reference to the 2011 "
          "evaluation, 0 = not, ? = uncertain), with a 'note' for doubtful cases and 'use' for "
          "how the reference is used.")


if __name__ == "__main__":
    main()
