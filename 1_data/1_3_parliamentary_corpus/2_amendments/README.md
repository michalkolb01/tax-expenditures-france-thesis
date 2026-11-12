# 1.3.2 – Amendments matched to measures (section 4.1.3)

Amendments are matched to measures on the tax-code article: the articles cited by each amendment are compared with the legal basis of each measure in the annex. Each candidate link is then checked by a language model, which also labels the direction of the amendment. There is no hand validation of the matching. In the thesis the corpus is used only to locate debates, which are then read.

## Scripts, in order

All paths go through `src/config.py` (`data/raw/` and `data/intermediate/`).

| Script | Inputs | Outputs |
|---|---|---|
| `01_parse_amendments.py` | `raw/an_portal/amendements_leg14–17.xml.zip`, `raw/an_portal/dossiers_leg14–17.xml.zip` | `amendments_14.parquet`, `amendments_15_17.parquet` (articles cited, finance-bill labels) |
| `02_match_articles.py` | Voies et moyens panel (`vm_2009_2019.parquet`, `vm_2020_2026.parquet`), `guillaume_all.csv`, the two amendment files | `measures_with_bands.csv`, `pairs_14.parquet`, `pairs_15_17.parquet` |
| `03_llm_verify_classify.py` | pairs files, Voies et moyens panel, `prompt_verify_single.txt`, `prompt_choose_measure.txt`; `ANTHROPIC_API_KEY` (model `claude-sonnet-4-5`) | `classified_all.csv` (single-article pass), `classified_multi.csv` (multi-article pass), `amendments_classified.csv` (combined: 7,861 amendments, 272 measures) |
| `04_validation_sample.py` | pairs files, `measures_with_bands.csv`, Voies et moyens panel | `validation/matching_precision_sample.xlsx` (100 pairs), `validation/silent_survivors_check.xlsx`: prepared but never coded, not used in the thesis |

`01` takes about twenty minutes; `03` makes about 15,000 API calls but resumes from its CSVs and makes none when they are complete. Source notebooks: *Master Thesis_1 Scraping* (cells 25–34), *Master Thesis_4 Matching*, *Master Thesis_5 Classification*, `12_matching_validation.ipynb`; each script's docstring lists the cells used.

## Known caveats

- `amendments_15_17.parquet` has 648,213 rows for 598,947 parsed amendments: the merge with dossier titles duplicates some amendments. Downstream steps deduplicate on `uid`; the pairs are not affected.
- Finance-bill labels for legislatures 15–17 cover PLF 2021–2026 only; no bill is found under 49.3. The labels are not used by the matching.
- In the notebook, the labelling was run on cached, already labelled files, which breaks on a re-run (`_x`/`_y` columns); `01` labels the freshly parsed frame instead.
- The notebooks read the amendment archives from `raw/an_portal/`, while `data/README.md` lists a `raw/amendments/` folder; the scripts follow the notebooks.
- Exact article matching: amendments citing a parent article ("199") are not matched to measures recorded at a sub-article ("199 sexvicies").
- LLM labels cannot be regenerated identically (temperature not set; model may be retired). The first 600 rows of `classified_multi.csv` were written by an earlier version of the multi-article loop.
- The samples drawn in the notebooks to validate the matching, their coding columns and the figures typed in *Master Thesis 5_Classification* (cells 15 and 31) are in `archive/matching_validation/`; they are not used in the thesis. The 40-pair LLM pilot (cells 8 and 10) and the sample it used (*Master Thesis_4 Matching*, cells 40–41) are left out of the scripts.
- The 100-pair sample and the silent-survivors list from `04_validation_sample.py` (`12_matching_validation.ipynb`) were prepared but not coded.
