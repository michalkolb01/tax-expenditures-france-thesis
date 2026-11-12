"""Download the Finance Committee minutes (comptes rendus), legislatures 14-17.

Pipeline step, no thesis number directly.

Legislatures 15-17: the meeting records (reunions_leg15/16/17.xml.zip,
downloaded by 01_download_an_portal.py) are scanned for meetings of the
Commission des finances (organe PO59048) that have a compte rendu; those
whose agenda mentions the examination of a finance bill ("Examen ... projet
de loi de finances") are downloaded as HTML from the AN open-data URL.

Legislature 14: the open-data URL returns 404 for these minutes, so they are
taken from the old site (/14/cr-cfiab/<session>/c<ssss><nnn>.asp), probing
numbers 1-120 in each parliamentary session 2012-13 to 2016-17 and keeping
pages over 20 kB. All committee minutes of the session are kept, not only
finance-bill examinations.

Inputs
    data/raw/an_portal/reunions_leg15.xml.zip, ..._leg16, ..._leg17
    https://www.assemblee-nationale.fr/dyn/opendata/<CR uid>.html   (leg 15-17)
    https://www.assemblee-nationale.fr/14/cr-cfiab/<session>/*.asp  (leg 14)
Outputs
    data/raw/committee_cr/<CR uid>.html                 237 files (leg 15-17)
    data/raw/committee_cr_14/<session>_c<ssss><nnn>.asp 506 files (leg 14)
    00_acquisition/manifests/manifest_committee.csv     238 rows (status,
                                                        bytes, sha256, date,
                                                        agenda)
    00_acquisition/manifests/manifest_committee_14.csv  506 rows (session,
                                                        n, url, bytes, path,
                                                        sha256)
Needs
    pip install requests pandas

Source
    Master Thesis_7 Committee (7_Committee.ipynb):
    - leg 15-17: cells 4 (finance_sessions: 1,025 finance-committee
      meetings with a transcript, 238 finance-bill examinations) and 5
      (download + manifest_committee.csv; 237 ok, 1 http 404).
      Cells 0-3 (inspecting the XML and testing URL patterns) dropped.
    - leg 14: cell 58 (probing the session folders, the list F of 506
      records) and cell 60 (download + manifest_committee_14.csv).
      Cells 55-57 (testing URLs) and 59 dropped.
    NameError fixed: `base` was used in cells 57-59 but defined in no
    surviving cell; it is set here to the folder tested in cell 56,
    https://www.assemblee-nationale.fr/14/cr-cfiab/ .

Caveats
    - Cell 59 found 3 more records in session 12-13 (numbers above 120) but
      did not add them to F, so they were never downloaded and are not in
      manifest_committee_14.csv. This script reproduces that (1-120 only).
    - The raw folders keep the notebook names committee_cr/ and
      committee_cr_14/ (data/README.md groups them under "committee/"),
      because the parsing cells of 7_Committee (now 03_debate_corpus) read
      them under these names.
    - The manifests were written to raw/ in the notebook; they now go to
      00_acquisition/manifests/.
"""
import hashlib
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
MANIFESTS = HERE / "manifests"
AN_PORTAL = RAW / "an_portal"
CR = RAW / "committee_cr"
CR14 = RAW / "committee_cr_14"

h = {"User-Agent": "research"}


# ---------------------------------------------------------------------------
# Legislatures 15-17 (cells 4-5)
# ---------------------------------------------------------------------------
def finance_sessions(leg):
    rows = []
    with zipfile.ZipFile(AN_PORTAL / f"reunions_leg{leg}.xml.zip") as f:
        for n in [x for x in f.namelist() if x.endswith(".xml")]:
            s = f.read(n).decode("utf-8", "ignore")
            if "PO59048" not in s:
                continue
            cr = re.search(r"<compteRenduRef>(.*?)</compteRenduRef>", s)
            dt = re.search(r"<timeStampDebut>(.*?)T", s)
            odj = re.sub(r"\s+", " ", " ".join(re.findall(r"<item>(.*?)</item>", s, re.S)))
            if not cr:
                continue
            rows.append({"legislature": str(leg), "cr": cr.group(1),
                         "date": dt.group(1) if dt else None, "odj": odj[:400]})
    return pd.DataFrame(rows)


def download_leg15_17():
    CR.mkdir(parents=True, exist_ok=True)
    S = pd.concat([finance_sessions(l) for l in (15, 16, 17)], ignore_index=True)
    S = S.drop_duplicates("cr")
    S["examen"] = S["odj"].str.contains(r"[Ee]xamen.{0,60}projet de loi de finances",
                                        regex=True, na=False)
    print(f"{len(S)} finance-committee meetings with a transcript")
    print(S.groupby(["legislature", "examen"]).size().to_string())

    BASE = "https://www.assemblee-nationale.fr/dyn/opendata/{}.html"
    todo = S[S["examen"]].copy()
    print(f"{len(todo)} to fetch\n")

    rows = []
    for i, r in todo.reset_index(drop=True).iterrows():
        dest = CR / f"{r['cr']}.html"
        if dest.exists():
            status = "have"
        else:
            try:
                resp = requests.get(BASE.format(r["cr"]), timeout=60,
                                    headers={"User-Agent": "research"})
                if resp.status_code == 200 and len(resp.content) > 5000:
                    dest.write_bytes(resp.content)
                    status = "ok"
                else:
                    status = f"http {resp.status_code}"
            except Exception as e:
                status = type(e).__name__
            time.sleep(1)
        rows.append({**r.to_dict(), "status": status,
                     "bytes": dest.stat().st_size if dest.exists() else 0,
                     "sha256": hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else None,
                     "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        if i % 20 == 0:
            print(f"  {i}/{len(todo)}")

    M = pd.DataFrame(rows)
    M.to_csv(MANIFESTS / "manifest_committee.csv", index=False)
    print()
    print(M["status"].value_counts().to_string())


# ---------------------------------------------------------------------------
# Legislature 14 (cells 58 and 60)
# ---------------------------------------------------------------------------
base = "https://www.assemblee-nationale.fr/14/cr-cfiab/"


def find_leg14():
    found = []
    for s, pre in [("12-13", "1213"), ("13-14", "1314"), ("14-15", "1415"),
                   ("15-16", "1516"), ("16-17", "1617")]:
        n_ok = 0
        for i in range(1, 121):
            url = f"{base}{s}/c{pre}{i:03d}.asp"
            try:
                r = requests.get(url, timeout=15, headers=h)
                if r.status_code == 200 and len(r.content) > 20000:
                    found.append({"session": s, "n": i, "url": url,
                                  "bytes": len(r.content)})
                    n_ok += 1
            except Exception:
                pass
        print(f"{s}: {n_ok} records")

    F = pd.DataFrame(found)
    print(f"\n{len(F)} committee records found")
    return F


def download_leg14(F):
    CR14.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, r in F.reset_index(drop=True).iterrows():
        name = r["url"].rsplit("/", 1)[-1]
        dest = CR14 / f"{r['session']}_{name}"
        if not dest.exists():
            resp = requests.get(r["url"], timeout=30, headers=h)
            if resp.status_code == 200:
                dest.write_bytes(resp.content)
            time.sleep(0.5)
        rows.append({**r.to_dict(), "path": dest.name,
                     "sha256": hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else None})
        if i % 100 == 0:
            print(f"  {i}/{len(F)}")

    M14 = pd.DataFrame(rows)
    M14.to_csv(MANIFESTS / "manifest_committee_14.csv", index=False)
    print(f"\n{M14['path'].nunique()} files saved")


def main():
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    download_leg15_17()
    download_leg14(find_leg14())


if __name__ == "__main__":
    main()
