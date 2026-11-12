# 1.3.2 – Amendments matched to measures (section 4.1.3)

Extracts the tax-code articles cited by each amendment, proposes candidate measures through the legal basis recorded in the annex, verifies each candidate with an LLM, and classifies the direction of the amendment. Includes the prompts and the scripts that draw the validation samples.

## Scripts, in order

All paths go through `src/config.py` (`data/raw/` and `data/intermediate/`).

| Script | Inputs | Outputs |
|---|---|---|
| `01_parse_amendments.py` | `raw/an_portal/amendements_leg14–17.xml.zip`, `raw/an_portal/dossiers_leg14–17.xml.zip` | `amendments_14.parquet`, `amendments_15_17.parquet` (articles cited, finance-bill labels) |
| `02_match_articles.py` | Voies et moyens panel (`vm_2009_2019.parquet`, `vm_2020_2026.parquet`), `guillaume_all.csv`, the two amendment files | `measures_with_bands.csv`, `pairs_14.parquet`, `pairs_15_17.parquet`, `precision_check_40_v3.csv` |
| `03_llm_verify_classify.py` | pairs files, Voies et moyens panel, `prompt_verify_single.txt`, `prompt_choose_measure.txt`; `ANTHROPIC_API_KEY` (model `claude-sonnet-4-5`) | `classified_all.csv` (single-article pass), `classified_multi.csv` (multi-article pass), `amendments_classified.csv` (combined: 7,861 amendments, 272 measures) |
| `04_validation_sample.py` | pairs files, `measures_with_bands.csv`, Voies et moyens panel | `validation/matching_precision_sample.xlsx` (100 pairs to code by hand), `validation/silent_survivors_check.xlsx` |

`01` takes about twenty minutes; `03` makes about 15,000 API calls but resumes from its CSVs and makes none when they are complete. Source notebooks: *Master Thesis_1 Scraping* (cells 25–34), *Master Thesis_4 Matching*, *Master Thesis_5 Classification*, `12_matching_validation.ipynb`; each script's docstring lists the cells used.

## Known caveats

- `amendments_15_17.parquet` has 648,213 rows for 598,947 parsed amendments: the merge with dossier titles duplicates some amendments. Downstream steps deduplicate on `uid`; the pairs are not affected.
- Finance-bill labels for legislatures 15–17 cover PLF 2021–2026 only; no bill is found under 49.3. The labels are not used by the matching.
- In the notebook, the labelling was run on cached, already labelled files, which breaks on a re-run (`_x`/`_y` columns); `01` labels the freshly parsed frame instead.
- The notebooks read the amendment archives from `raw/an_portal/`, while `data/README.md` lists a `raw/amendments/` folder; the scripts follow the notebooks.
- Exact article matching: amendments citing a parent article ("199") are not matched to measures recorded at a sub-article ("199 sexvicies").
- LLM labels cannot be regenerated identically (temperature not set; model may be retired). The first 600 rows of `classified_multi.csv` were written by an earlier version of the multi-article loop.
- The 40-pair pilot (*5 Classification*, cells 8 and 10) is exploratory and not included. Its hand-coding file names the human judgement column `claude_relevant`, which raises the question of who coded it.
- `classification_meta.json` (cell 15) and `validation_summary.json` hard-code validation figures (0.98, 0.92, 0.90, 0.97) that no notebook cell computes; the meta file is not written by the scripts.
- `validation_random100.csv`, once listed for this folder, validates the classification of debate interventions (not the matching); it is in `archive/argument_classification/`. The hand-coded results of the two workbooks from `04_validation_sample.py` are not in the package.
