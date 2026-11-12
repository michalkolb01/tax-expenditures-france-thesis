# Section 6.4 – Sources for the three pairs

Each claim made about the pairs is listed with its source. Debate passages
are reproduced by `02_extract_pair_debates.py` (files `data/pair_*_passages.csv`).
**Status:** ✅ checked against the source; ⚠️ to verify before submission.

2011 scores and costs from the panel come from
`data/intermediate/tax_expenditures_panel_2009_2026.xlsx` (built by
`1_data/1_2_panel_2009_2026/`, from the annexes *Évaluation des voies et moyens*, tome II).

---

## Pair A – Pension increases and school fees (finance bill for 2014, debated October 2013)

| Claim | Source | Status |
|---|---|---|
| Exemption of pension increases for parents of 3+ children (code 120114), scored 0 | Panel; Comité d'évaluation (2011) | ✅ |
| School-fee reductions: two codes, 110215 (secondary, scored 0) and 110242 (higher education, scored 1) | Panel | ✅ |
| Both proposed for removal in the finance bill for 2014 (bill no. 1395), articles 6 and 4 | Bill no. 1395 | ⚠️ article numbers |
| Committee examination 9 October 2013; plenary 17 October 2013 | Committee minutes (committee_blocks_14, session 13-14); DILA plenary record of 17 October 2013 | ✅ (17 Oct: known-item test, 6.2.2) |
| Pension exemption abolished (article adopted, eight amendments to keep it rejected) | Plenary record, 17 October 2013 | ⚠️ count of amendments |
| School-fee article deleted in committee and then unanimously in plenary; government left the decision to the Assembly | Committee minutes 9 Oct 2013; plenary 17 Oct 2013 | ⚠️ |
| School-fee reductions survived later removal proposals in 2022, 2023, 2024 and 2026 | Amendments (amendments_classified.csv); PLF 2026 article 5 and final law | ⚠️ 2022–2024 to cite individually |
| Cost: pension exemption about €1.2 bn; school fees about €440 m (two codes together) | Annex to the PLF 2014 (VMT II), costs for 2013 | ⚠️ cite the annex lines |
| €810 m of €1.2 bn to the three highest deciles (rapporteur général) | Rapporteur général's report on the PLF 2014 / plenary 17 Oct 2013 | ⚠️ page reference |
| Richest tenth +1.8% vs poorest half +0.1% (minister) | Plenary 17 October 2013 | ⚠️ |
| Reduction amounts: €61, €153, €183 per child | CGI art. 199 quater F | ✅ |
| About 3.8 million taxable retirees (about 70%) received the pension increase | Plenary 17 October 2013 (speaker figure) | ✅ quoted as "figures given in the debate" |
| 2.2–2.7 million taxable families claimed the school-fee reductions | Plenary 2013; committee 2025 | ⚠️ settle one figure |
| Defenders: family policy, natality, burden on large families | Plenary 17 and 25 October 2013 | ✅ |
| The 2011 evaluation cited once on school fees (Dalloz, quoting the rapporteur général's report: "impossible to take away from families") | evaluation2011_candidates_RAW_reviewed.csv, 17 Oct 2013 | ✅ |

## Pair B – Work medal bonuses and long-term illness allowances (finance bill for 2026, debated October 2025)

| Claim | Source | Status |
|---|---|---|
| Codes 120116 (work medal bonuses) and 120204 (long-term illness allowances), both scored 0 | Panel; `tables/plf2026_article5_scores.csv` | ✅ |
| Both in article 5 of the PLF 2026 (bill no. 1906), abolishing 23 tax expenditures | Bill no. 1906 and impact assessment (Évaluations préalables, art. 5) | ✅ |
| Costs: €11 m (medal) and €828 m (illness allowances) in 2026 | Impact assessment, art. 5, table 4.2.1 | ✅ (the text cites ~€800 m via amendment CF2247; the impact assessment figure, €828 m, is the better source) |
| Committee examination 20 October 2025; rapporteur général Philippe Juvin | Committee minutes, 20 Oct 2025 (`pair_B_passages.csv`) | ✅ |
| One amendment to keep the medal exemption (RN); rapporteur général: no incentive effect, "a distinction for having done one's job" | Committee minutes 20 Oct 2025 | ✅ |
| Opponents of taxing the allowances: 50% of gross wage, capped at €41.50/day; "tax on cancer"; justice and humanity; 14 million chronic patients | Committee minutes 20 Oct 2025 | ✅ |
| Rapporteur général: allowances for sick leave unrelated to the illness could be taxed; de Courson: tax half | Committee minutes 20 Oct 2025 | ✅ |
| Committee voted to keep the exemption (identical amendments I-CF528, I-CF1182, I-CF1867, I-CF1876 adopted) | Committee minutes 20 Oct 2025 | ✅ |
| Assembly first voted on the floor to keep the medal exemption; abolition retained by the joint committee | Finance Committee report no. 2935 on bill no. 2790 | ✅ |
| Final law: medal exemption abolished; illness allowances kept fully exempt | BOFiP BOI-RSA-CHAMP-20-50-40-20260506; Senioractu (2026) | ⚠️ cite the law article (loi de finances pour 2026; check its number and date) |
| Senate first voted a 50% exemption | Public Sénat | ✅ (dropped from the text) |
| Minister: average gain about €27 per recipient | Amendment no. 15 to bill no. 2790 (LFI), reporting the minister | ⚠️ find the plenary passage |
| Restoration bill no. 2790 (12 May 2026): bonus is symbolic recognition of work, out of line with other honours | Bill no. 2790 | ✅ |
| Finance Committee rejected bill no. 2790 | Report no. 2935 | ✅ |
| Government declined to support restoration | Written answer, 30 June 2026 (question no. 14485) | ⚠️ add the reference |

## Pair C – Local investment funds, mainland and Corsica (finance bill for 2025, debated October 2024)

| Claim | Source | Status |
|---|---|---|
| Codes 110228 (FIP, mainland) and 110245 (FIP invested in Corsica), both scored 0 | Panel | ✅ |
| Costs: about €9–17 m (mainland) and €5–10 m (Corsica) a year in recent years | Panel (annex figures, 2019–2026) | ✅ |
| Debated together in the bills for 2021, 2022 and 2025 | `tables/pair_candidates_same_bill.csv`; amendments_classified.csv | ✅ |
| 11 October 2023: Castellani (LIOT) proposed raising the Corsican rate to 45%, citing the island's structural difficulties; rapporteur général Cazeneuve refused, ruling out any cut to the 30% | Committee minutes 11 Oct 2023 (`pair_C_passages.csv`) | ✅ |
| 17 October 2024: amendment I-CF1161 (Castellani) abolishing the mainland reduction and keeping Corsica and overseas, adopted | Committee minutes 17 Oct 2024 | ✅ |
| Castellani: mainland funds no longer required to invest regionally since 2019; Corsican/overseas funds must invest 70% locally | Committee minutes 17 Oct 2024 | ✅ |
| Rapporteur général de Courson: no mainland fund shows a positive return; tax advantage at best offsets part of the losses; Corsica and overseas "of real interest" | Committee minutes 17 Oct 2024 | ✅ |
| Arrighi (EcoS) withdrew her amendment, "sensitive to the Corsican appeal" | Committee minutes 17 Oct 2024 | ✅ |
| Floor amendment I-3572 (19 Oct 2024, rejected) cited the IGF report of March 2024, delayed removal to 2026 for fund managers, kept Corsica and overseas | Amendment I-3572 | ✅ |
| Final law: mainland reduction ends for subscriptions from 1 January 2026; Corsica kept at 30% | Loi n° 2025-127 du 14 février 2025 (art. 12); France Épargne (2026) | ✅ |
| Removal of the Corsican reduction rejected again in October 2025 (amendment CF1505) | Amendment I-CF1505 (PLF 2026) | ✅ |
| Overseas FIP (FIPOM, 110260) also kept | Panel; France Épargne (2026) | ✅ |
| 20 Corsica-specific measures in the annex (title contains "Corse"); 10 in force in 2026, 7 of these scored 0 and 3 were not in the 2011 report | Panel (keyword search on titles) | ✅ (state the keyword rule) |

## Selection of the pairs

See `01_pair_search.py`: search 1 (same bill, same family, different fate) and
search 2 (article 5 of the PLF 2026 with 2011 scores).
