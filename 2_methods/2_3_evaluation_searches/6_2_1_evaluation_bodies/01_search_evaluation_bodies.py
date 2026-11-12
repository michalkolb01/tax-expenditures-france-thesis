"""Section 6.2.1 - Evaluation bodies cited in debates on tax expenditures.

Step 1 of 2: automatic search of the COMPLETE committee and plenary records,
2012-2026. Step 2 is a manual reading of every match (see
02_analyse_reviewed.py and data/te_passages_with_evaluation_reviewed.csv).

Inputs (see data/README.md for download instructions)
    data/raw/dila_debats/**/*.taz              plenary verbatim records, DILA, 2011-2017
    data/raw/an_portal/debats_leg1[567].xml.zip plenary records, Assembly open data, 2017-2026
    data/intermediate/committee_blocks*.parquet Finance Committee minutes, 2012-2026
                                               (built by 1_data/1_3_parliamentary_corpus/3_blocks_and_turns/)

Method
    Unit: passages of about 1,000 characters cut at sentence ends, so the
    unit is the same in every source whatever its XML structure.
    A passage "refers to a tax expenditure" if it contains one of the terms
    in TE below. It "cites an evaluation body" if one of the four bodies in
    BODIES is named within NEAR = 300 characters of such a term (proximity,
    not mere co-occurrence). Passages are deduplicated on their text and
    kept for 2012-2026.

Output
    data/te_passages_with_evaluation.csv   every passage with a body nearby,
                                           to be read and coded (column 'genuine')
Printed (as in the run of 11 November 2026 used in the thesis)
    Passages referring to a tax expenditure, 2012-2026: 20,000
        (committee 2,699; plenary 17,301)
    ... with an evaluation body within 300 characters: 536 (2.7%)
    After manual reading, 494 of the 536 are genuine (see 02_analyse_reviewed.py),
    i.e. about 2.5% of the 20,000 passages.

Known limitation
    The DILA files for 2016 are stored in a format this script skips (227
    non-XML archive members), so 2016 contributes almost no plenary
    passages. Later versions of the cell tried to fix this without success;
    the thesis figures carry this gap and section 4.x says so.

Thesis text: section 6.2.1, first paragraph (2.5%, shares by body).
"""
import glob, gzip, io, os, re, subprocess, sys, tarfile, zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE  # noqa: E402

OUT = Path(__file__).resolve().parent / "data"

TE = re.compile(
    r"niches? fiscales?|dépenses? fiscales?|crédits? d.impôt|réductions? d.impôt|exonérations? fiscales?|"
    r"exonérations? d.impôt|taux réduits? de TVA|abattements? fiscaux|pacte Dutreil|avantages? fiscaux|avantage fiscal|"
    r"défiscalisation|dispositifs? fiscaux|dispositif fiscal", re.I)
BODIES = {
    "Court of Audit": re.compile(r"Cour des comptes", re.I),
    "General Inspectorate of Finance": re.compile(r"Inspection générale des finances|\bIGF\b", re.I),
    "Council for Compulsory Levies": re.compile(r"Conseil des prélèvements obligatoires|\bCPO\b", re.I),
    "France Strategy": re.compile(r"France Stratégie", re.I),
}
MEASURES = {
    "research tax credit": re.compile(r"crédit d.impôt (en faveur de la )?recherche|\bCIR\b", re.I),
    "Dutreil pact": re.compile(r"Dutreil", re.I),
    "home services credit": re.compile(r"emploi d.un salarié à domicile|services à la personne|emploi à domicile", re.I),
    "film and audiovisual credits": re.compile(
        r"crédit d.impôt (cinéma|audiovisuel|international)|œuvres (cinématographiques|audiovisuelles)", re.I),
}
NEAR = 300


def clean(raw_bytes):
    t = raw_bytes.decode("utf-8", errors="ignore").replace("\x00", " ")
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&nbsp;|&#160;|&#xa0;|&#\d+;", " ", t)
    return re.sub(r"\s+", " ", t)


def passages(text, size=1000):
    """Fixed-size passages (~1,000 characters) cut at sentence ends."""
    out, cur = [], ""
    for s in re.split(r"(?<=[.!?»])\s+", text):
        if len(cur) + len(s) > size and cur:
            out.append(cur)
            cur = ""
        cur += s + " "
    if cur.strip():
        out.append(cur)
    return [p for p in out if len(p) > 80 and p.count(" ") > 10]


def near(p, rx_body):
    te_pos = [m.start() for m in TE.finditer(p)]
    return any(abs(b.start() - t) <= NEAR for b in rx_body.finditer(p) for t in te_pos)


def find_date(raw_text, name=""):
    head = raw_text[:20000]
    m = (re.search(r"[Dd]ate_?[Ss]eance[^>]*>\s*(20[12]\d)-?(\d{2})-?(\d{2})", head)
         or re.search(r"(20[12]\d)-(\d{2})-(\d{2})", head)
         or re.search(r"(20[12]\d)(\d{2})(\d{2})\d{6,9}", head))
    if m:
        return "".join(m.groups())
    m = re.search(r"(20[12]\d)(\d{2})(\d{2})", name)
    return "".join(m.groups()) if m else ""


def open_taz(path):
    """DILA .taz = tar compressed with Unix 'compress' (.Z); gzip -dc decompresses it."""
    raw = open(path, "rb").read()
    if raw[:2] == b"\x1f\x9d":
        raw = subprocess.run(["gzip", "-dc"], input=raw, capture_output=True).stdout
    elif raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return tarfile.open(fileobj=io.BytesIO(raw))


def main():
    rows = []

    def record(text, venue, date):
        for p in passages(text):
            if TE.search(p):
                r = {"venue": venue, "year": date[:4], "text": p}
                for b, rx in BODIES.items():
                    r[b] = near(p, rx)
                for m, rx in MEASURES.items():
                    r[m] = bool(rx.search(p))
                rows.append(r)

    for f in sorted(glob.glob(str(RAW / "dila_debats" / "**" / "*.taz"), recursive=True)):
        try:
            with open_taz(f) as tar:
                for m in tar.getmembers():
                    if m.isfile() and m.name.lower().endswith(".xml"):
                        raw = tar.extractfile(m).read()
                        record(clean(raw), "floor", find_date(raw.decode("utf-8", "ignore"), os.path.basename(f)))
        except Exception as e:  # noqa: BLE001
            print("skip", os.path.basename(f), str(e)[:60])
    print("DILA done:", len(rows))

    for f in sorted(glob.glob(str(RAW / "an_portal" / "debats_leg1[567].xml.zip"))):
        with zipfile.ZipFile(f) as z:
            for n in z.namelist():
                if n.endswith(".xml"):
                    raw = z.read(n)
                    record(clean(raw), "floor", find_date(raw.decode("utf-8", "ignore"), n))
    print("portal done:", len(rows))

    for f in glob.glob(str(INTERMEDIATE / "committee_blocks*.parquet")):
        d = pd.read_parquet(f)
        dc = next((c for c in ["date", "session"] if c in d.columns), None)
        for _, r in d.iterrows():
            date = str(r[dc]) if dc else ""
            date = ("20" + date[:2]) if re.match(r"\d\d-\d\d", date) else date
            record(re.sub(r"\s+", " ", str(r["texte"])), "committee", date)
    print("committee done:", len(rows))

    df = pd.DataFrame(rows)
    df = df[(df.year >= "2012") & (df.year <= "2026")].drop_duplicates("text")
    df["any_body"] = df[list(BODIES)].any(axis=1)
    df["period"] = pd.cut(df.year.astype(int), [2011, 2016, 2019, 2026], labels=["2012-16", "2017-19", "2020-26"])
    df[df.any_body].to_csv(OUT / "te_passages_with_evaluation.csv", index=False)

    print(f"\nPassages referring to a tax expenditure, 2012-2026: {len(df):,}")
    print(f"... with an evaluation body within {NEAR} characters: {df.any_body.sum():,} ({df.any_body.mean():.1%})")
    print(df[list(BODIES)].sum().to_string())
    print("\nBy venue:")
    print(df.groupby("venue").any_body.agg(["sum", "size", "mean"]).to_string())
    print("\nBy period:")
    print(df.groupby("period", observed=True).any_body.agg(["sum", "size", "mean"]).to_string())
    print("\nNext step: read every row of te_passages_with_evaluation.csv and add a column 'genuine' "
          "(1 = an evaluation body cited about a tax expenditure, 0 = not).")


if __name__ == "__main__":
    main()
