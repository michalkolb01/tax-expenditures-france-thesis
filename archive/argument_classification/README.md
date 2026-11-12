# Argument classification (archived)

Earlier stage of the project, not used in the thesis. Kept for transparency.

The thesis does not classify interventions into argument categories and reports no shares of
arguments. These files document the automated classification that was tried before the
interventions were read by hand (section 6.3).

| File | Content |
|---|---|
| `01_classify_v3.py` | Classification of the 5,340 speaking turns with `prompt_arguments_v3.txt` → `arguments_v3.csv` (LLM, `claude-sonnet-4-5`, key from `ANTHROPIC_API_KEY`) |
| `02_dedup.py` | Deduplication on (text, measure) → `arguments_v3_dedup.csv` (3,352 interventions) |
| `03_validation_sheets.py` | Validation samples → `validation_arguments_v3.csv`, `validation_offtopic_v3.csv` |
| `prompt_arguments_v0.txt` … `v2.txt` | Earlier prompts (superseded; source cells in each file's header) |
| `validation_random100.csv`, `human_validation_34.xlsx` | Validation files of the classification. No notebook writes them. |
| `validation_arguments_v3.csv` | Validation sample of the v3 classification |

Source notebooks: *08_arguments_v3* and the last cells of *Master Thesis_7 Committee Debates*.
The speaker and group columns of `arguments_v3_dedup.csv` (`speaker_role`, `name`, `group_tag`,
`group`, `bloc`) were added by cells that cannot be re-run (live call to nosdeputes.fr; a manual
correction table not saved in the notebook).

`data/intermediate/arguments_v3_dedup.csv` stays in the main package because
`2_methods/2_4_arguments/01_build_reading_workbook.py` uses it to select the interventions to read
(see `data/README.md`).
