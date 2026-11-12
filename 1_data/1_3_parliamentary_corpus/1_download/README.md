# 1.3.1 – Download of the records (section 4.1.3)

Downloads every public source into data/raw/ and writes a manifest per source (URL, download date, size). The manifests used for the thesis go in manifests/.

Scripts, in order (none of them is needed to reproduce the thesis numbers: they rebuild data/raw/):

1. `01_download_an_portal.py` – AN open-data archives (amendements, debats, dossiers, reunions, acteurs; legislatures 14–17) → `data/raw/an_portal/*.xml.zip`; `manifests/manifest_an_portal.csv`. From *1_Scraping* c4, c6, c8, c10, c12.
2. `02_download_dila.py` – DILA plenary records 2011–2017 (817 `.taz`) → `data/raw/dila_debats/<year>/`; `manifests/manifest_dila.csv`. From *1_Scraping* c19, c21, c23.
3. `03_download_committee.py` – Finance Committee minutes: legislatures 15–17 from the AN open data (238 finance-bill examinations, 237 downloaded) → `data/raw/committee_cr/`, `manifests/manifest_committee.csv`; legislature 14 from the old AN site (506 records) → `data/raw/committee_cr_14/`, `manifests/manifest_committee_14.csv`. Needs the `reunions_leg*.xml.zip` from step 1. From *7_Committee* c4–c5 and c58, c60.

`manifests/` holds the manifests used for the thesis (URL, date, size, checksum of every file). `pdf_checklist.csv` (listed in data/README.md for the tome II PDFs) has no writer in any notebook.

Known caveats

- `amendements_leg15` and `amendements_leg16` (738 MB and 412 MB) were too large to download from Colab; they were downloaded by hand from the same portal pages (manifest column `how = laptop`). Script 01 skips them.
- Legislature 17 archives are rebuilt daily by the portal; `verified = False` in the manifest means an older edition, not a damaged file. The thesis used the editions of 2026-08-26.
- The amendment archives are stored in `data/raw/an_portal/`, not in an `amendments/` folder as data/README.md suggests; committee minutes are in `committee_cr/` and `committee_cr_14/` (not `committee/`).
- Legislature 14: the probe covers record numbers 1–120 per session; 3 further records of session 2012-13 (numbers above 120) were found in the notebook but never downloaded, and are not in `manifest_committee_14.csv`.
- No notebook downloads the tome II inventories (`vmt_tome2/`) or the 2011 report (`guillaume_2011/`): they were saved by hand from the Ministry's website.
- The notebooks wrote the manifests to `raw/`; the scripts write them to `1_data/1_3_parliamentary_corpus/1_download/manifests/`.
- The amendment parsing (1_Scraping c25–34) is in `1_data/1_3_parliamentary_corpus/2_amendments/`.
