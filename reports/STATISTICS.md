# Massachusetts housing need — statistics (Outcome 1)

Generated 2026-11-10 by `pipeline.stats_report` from the loaded database (the same services as the API). Sources and years are given per figure; dataset details in DATA_SOURCES.md. **Official** homelessness counts exist only per Continuum of Care; any homelessness figure below CoC level is a modelled **estimate**.

## 1. Statewide

| Figure | Value | Source, year |
|---|---|---|
| Population | 7,044,056 | acs5, 2024 |
| People experiencing homelessness, PIT 2025 (official CoC count, sum of 11 CoCs) | 28,311 | hud_pit, 2025 |
| — sheltered | 26,563 | hud_pit, 2025 |
| — unsheltered | 1,748 | hud_pit, 2025 |
| Change from 2024 | -1,049 (-3.6%) | hud_pit |
| Change from 2012 | +10,810 (61.8%) | hud_pit |
| Year-round shelter beds, HIC 2025 (official CoC count) | 19,647 | hud_hic, 2025 |
| Year-round beds per person counted | 0.69 | computed (HIC beds / PIT total, same year) |
| Extremely-low-income (<=30% AMI) renter households | 314,258 | hud_chas, 2022 |
| — of which severely rent-burdened (at-risk households) | 170,134 | hud_chas, 2022 |
| Units affordable and available to ELI renters | 144,912 | hud_chas, 2022 |
| Affordable housing gap (ELI) | shortage of 169,346 | hud_chas, 2022 |
| Affordable & available units per 100 ELI renter households | 46.1 | hud_chas, 2022 |
| Housing units | 3,030,406 | acs5, 2024 |
| Vacancy rate | 8.1% | acs5, 2024 |
| HUD-assisted units | 192,839 | hud_psh, 2025 |
| LIHTC low-income units | 57,646 | hud_lihtc, 2024 |
| Housing Need Index (population-weighted mean of tracts, 0-100) | 49.5 | computed from 8 components (REPORT.md 3.3), 2026 |
| Sum of tract homeless estimates (check: equals the official total) | 28,311 (estimate) | modelled, PIT 2025 |

## 2. Homelessness trend, Massachusetts (official CoC counts)

HUD Point-in-Time counts summed over the Massachusetts CoCs (one night each January) and HUD Housing Inventory Count year-round beds. Highest count in the series: 29,360 (2024); lowest: 15,079 (2021).

| Year | Total | Sheltered | Unsheltered | Change | Change % | Year-round beds |
|---|---|---|---|---|---|---|
| 2012 | 17,501 | 16,779 | 722 | n/a | n/a | 14,782 |
| 2013 | 19,029 | 18,179 | 850 | +1,528 | +8.7% | 15,055 |
| 2014 | 21,237 | 20,478 | 759 | +2,208 | +11.6% | 15,471 |
| 2015 | 21,135 | 20,542 | 593 | -102 | -0.5% | 17,707 |
| 2016 | 19,608 | 18,848 | 760 | -1,527 | -7.2% | 17,382 |
| 2017 | 17,565 | 16,574 | 991 | -2,043 | -10.4% | 16,614 |
| 2018 | 20,068 | 19,083 | 985 | +2,503 | +14.2% | 17,310 |
| 2019 | 18,471 | 17,642 | 829 | -1,597 | -8.0% | 17,472 |
| 2020 | 17,975 | 16,681 | 1,294 | -496 | -2.7% | 17,528 |
| 2021 | 15,079 | 13,944 | 1,135 | -2,896 | -16.1% | 16,909 |
| 2022 | 15,507 | 14,372 | 1,135 | +428 | +2.8% | 17,908 |
| 2023 | 19,141 | 17,779 | 1,362 | +3,634 | +23.4% | 17,971 |
| 2024 | 29,360 | 27,725 | 1,635 | +10,219 | +53.4% | 21,531 |
| 2025 | 28,311 | 26,563 | 1,748 | -1,049 | -3.6% | 19,647 |

## 3. Homelessness by Continuum of Care (official CoC counts)

These are the only exact homelessness figures: HUD publishes PIT and HIC per CoC.

| CoC | Year | Total | Sheltered | Unsheltered | Change from previous year | Long-run change | Year-round beds |
|---|---|---|---|---|---|---|---|
| MA-516 Massachusetts Balance of State CoC | 2025 | 10,539 | 10,037 | 502 | -1,013 (-8.8%) | 197.4% since 2012 | 4,783 |
| MA-500 Boston CoC | 2025 | 5,540 | 5,408 | 132 | -358 (-6.1%) | -1.2% since 2012 | 5,386 |
| MA-506 Worcester City & County CoC | 2025 | 2,864 | 2,643 | 221 | +937 (+48.6%) | 82.2% since 2012 | 1,899 |
| MA-504 Springfield/Hampden County CoC | 2025 | 2,709 | 2,498 | 211 | -309 (-10.2%) | 10.8% since 2012 | 2,376 |
| MA-511 Quincy, Brockton, Weymouth, Plymouth City and County CoC | 2025 | 1,799 | 1,725 | 74 | -86 (-4.6%) | 26.3% since 2012 | 1,121 |
| MA-502 Lynn CoC | 2025 | 1,271 | 1,223 | 48 | +171 (+15.5%) | 207.0% since 2012 | 1,270 |
| MA-505 New Bedford, Attleboro, Taunton/Bristol County CoC | 2025 | 1,125 | 1,024 | 101 | -54 (-4.6%) | 80.6% since 2012 | 1,084 |
| MA-507 Pittsfield/Berkshire, Franklin, Hampshire Counties CoC | 2025 | 867 | 760 | 107 | -94 (-9.8%) | 20.9% since 2012 | 638 |
| MA-515 Fall River CoC | 2025 | 657 | 442 | 215 | +134 (+25.6%) | 114.0% since 2012 | 389 |
| MA-509 Cambridge CoC | 2025 | 575 | 498 | 77 | -172 (-23.0%) | 18.6% since 2012 | 376 |
| MA-503 Cape Cod Islands CoC | 2025 | 365 | 305 | 60 | -205 (-36.0%) | 0.3% since 2012 | 325 |

## 4. Counties

Homeless figures per county are **estimates**: the sum of modelled tract estimates (method in REPORT.md 3.2), not counts. The CoCs that overlap each county are listed; their official totals are in section 3 and cover the whole CoC. Affordable gap from HUD CHAS 2018-2022; Need Index is the population-weighted tract mean.

Largest ELI shortages: Suffolk County (shortage of 34,964); Middlesex County (shortage of 33,346); Essex County (shortage of 23,301).

| County | Population | Homeless (estimate) | CoCs | ELI renter households | Affordable & available units | Gap | Units per 100 ELI | Need Index |
|---|---|---|---|---|---|---|---|---|
| Barnstable County | 231,668 | 335 (estimate) | MA-503 | 5,408 | 2,548 | shortage of 2,860 | 47.1 | 47.9 |
| Berkshire County | 129,430 | 336 (estimate) | MA-507 | 4,802 | 2,206 | shortage of 2,596 | 45.9 | 50.6 |
| Bristol County | 582,270 | 1,782 (estimate) | MA-505, MA-515 | 25,895 | 11,296 | shortage of 14,599 | 43.6 | 52.3 |
| Dukes County | 20,933 | 17 (estimate) | MA-503 | 380 | 164 | shortage of 216 | 43.2 | 38.4 |
| Essex County | 813,054 | 4,462 (estimate) | MA-502, MA-516 | 40,524 | 17,223 | shortage of 23,301 | 42.5 | 52.6 |
| Franklin County | 70,944 | 182 (estimate) | MA-507 | 2,805 | 1,210 | shortage of 1,595 | 43.1 | 55.1 |
| Hampden County | 462,815 | 2,709 (estimate) | MA-504 | 25,969 | 12,307 | shortage of 13,662 | 47.4 | 51.4 |
| Hampshire County | 162,028 | 349 (estimate) | MA-507 | 5,087 | 2,041 | shortage of 3,046 | 40.1 | 48.1 |
| Middlesex County | 1,638,365 | 5,667 (estimate) | MA-509, MA-516 | 59,561 | 26,215 | shortage of 33,346 | 44.0 | 45.4 |
| Nantucket County | 14,483 | 13 (estimate) | MA-503 | 194 | 74 | shortage of 120 | 38.1 | 44.0 |
| Norfolk County | 730,082 | 2,134 (estimate) | MA-511, MA-516 | 24,124 | 10,947 | shortage of 13,177 | 45.4 | 47.1 |
| Plymouth County | 535,075 | 1,060 (estimate) | MA-511 | 13,898 | 7,226 | shortage of 6,672 | 52.0 | 48.4 |
| Suffolk County | 785,121 | 6,401 (estimate) | MA-500, MA-516 | 71,709 | 36,745 | shortage of 34,964 | 51.2 | 53.2 |
| Worcester County | 867,788 | 2,864 (estimate) | MA-506 | 33,902 | 14,710 | shortage of 19,192 | 43.4 | 51.4 |

## 5. Top need areas

Cities and towns by population-weighted Housing Need Index. Small towns (one or two tracts) can rank high on a single tract, so towns with at least 10,000 residents are also ranked separately. Tract-level rankings are in reports/top_tracts.csv.

### 5.1 All towns, top 15

| Rank | Town | County | Need Index | Population | Gap | Units per 100 ELI | Homeless (estimate) |
|---|---|---|---|---|---|---|---|
| 1 | Royalston | Worcester County | 72.3 | 1,460 | shortage of 10 | 66.7 | 2.3 |
| 2 | Hamilton | Essex County | 67.5 | 7,600 | shortage of 140 | 17.6 | 15.5 |
| 3 | Ware | Hampshire County | 66.3 | 10,048 | shortage of 265 | 41.8 | 31.8 |
| 4 | Conway | Franklin County | 65.7 | 1,765 | shortage of 29 | 0.0 | 2.7 |
| 5 | Ashfield | Franklin County | 65.7 | 1,883 | shortage of 31 | 0.0 | 2.9 |
| 6 | Brookfield | Worcester County | 64.0 | 3,460 | shortage of 20 | 0.0 | 3.1 |
| 7 | Becket | Berkshire County | 64.0 | 2,145 | shortage of 5 | 40.0 | 0.4 |
| 8 | Washington | Berkshire County | 64.0 | 343 | shortage of 1 | 40.0 | 0.1 |
| 9 | Lawrence | Essex County | 63.8 | 88,736 | shortage of 4,321 | 41.8 | 718.5 |
| 10 | Orange | Franklin County | 63.5 | 7,573 | shortage of 110 | 69.0 | 15.6 |
| 11 | Shutesbury | Franklin County | 63.0 | 1,822 | shortage of 26 | 13.3 | 3.1 |
| 12 | New Salem | Franklin County | 63.0 | 983 | shortage of 14 | 13.3 | 1.7 |
| 13 | Leverett | Franklin County | 63.0 | 1,767 | shortage of 25 | 13.3 | 3.0 |
| 14 | Lynn | Essex County | 62.8 | 101,709 | shortage of 4,430 | 48.4 | 1,271.0 |
| 15 | Hull | Plymouth County | 61.9 | 10,138 | shortage of 160 | 31.9 | 19.7 |

### 5.2 Towns with 10,000+ residents, top 15

| Rank | Town | County | Need Index | Population | Gap | Units per 100 ELI | Homeless (estimate) |
|---|---|---|---|---|---|---|---|
| 1 | Ware | Hampshire County | 66.3 | 10,048 | shortage of 265 | 41.8 | 31.8 |
| 2 | Lawrence | Essex County | 63.8 | 88,736 | shortage of 4,321 | 41.8 | 718.5 |
| 3 | Lynn | Essex County | 62.8 | 101,709 | shortage of 4,430 | 48.4 | 1,271.0 |
| 4 | Hull | Plymouth County | 61.9 | 10,138 | shortage of 160 | 31.9 | 19.7 |
| 5 | Lowell | Middlesex County | 61.8 | 118,368 | shortage of 4,580 | 41.9 | 814.7 |
| 6 | Fall River | Bristol County | 61.7 | 94,082 | shortage of 4,686 | 44.9 | 657.0 |
| 7 | Southbridge Town | Worcester County | 61.3 | 17,928 | shortage of 885 | 42.7 | 161.0 |
| 8 | Gardner | Worcester County | 60.7 | 21,148 | shortage of 755 | 31.7 | 102.4 |
| 9 | Chelsea | Suffolk County | 60.7 | 39,908 | shortage of 2,195 | 41.2 | 376.0 |
| 10 | Fitchburg | Worcester County | 60.0 | 41,798 | shortage of 1,281 | 40.7 | 186.0 |
| 11 | Winchendon | Worcester County | 59.9 | 10,440 | shortage of 110 | 61.4 | 12.5 |
| 12 | Athol | Worcester County | 59.7 | 12,011 | shortage of 185 | 44.8 | 30.5 |
| 13 | Springfield | Hampden County | 59.7 | 154,749 | shortage of 7,001 | 49.5 | 1,423.9 |
| 14 | Worcester | Worcester County | 59.5 | 207,055 | shortage of 9,303 | 44.2 | 1,380.7 |
| 15 | Seekonk | Bristol County | 59.2 | 15,694 | shortage of 135 | 35.7 | 13.6 |

### 5.3 Largest affordable shortages (ELI households), top 15

| Rank | Town | County | Need Index | Population | Gap | Units per 100 ELI | Homeless (estimate) |
|---|---|---|---|---|---|---|---|
| 1 | Boston | Suffolk County | 52.6 | 666,442 | shortage of 30,053 | 52.3 | 5,540.0 |
| 2 | Worcester | Worcester County | 59.5 | 207,055 | shortage of 9,303 | 44.2 | 1,380.7 |
| 3 | Springfield | Hampden County | 59.7 | 154,749 | shortage of 7,001 | 49.5 | 1,423.9 |
| 4 | Fall River | Bristol County | 61.7 | 94,082 | shortage of 4,686 | 44.9 | 657.0 |
| 5 | Lowell | Middlesex County | 61.8 | 118,368 | shortage of 4,580 | 41.9 | 814.7 |
| 6 | Lynn | Essex County | 62.8 | 101,709 | shortage of 4,430 | 48.4 | 1,271.0 |
| 7 | Lawrence | Essex County | 63.8 | 88,736 | shortage of 4,321 | 41.8 | 718.5 |
| 8 | New Bedford | Bristol County | 59.0 | 100,998 | shortage of 4,311 | 42.9 | 495.0 |
| 9 | Cambridge | Middlesex County | 45.5 | 118,796 | shortage of 3,862 | 44.2 | 575.0 |
| 10 | Quincy | Norfolk County | 51.1 | 102,140 | shortage of 3,724 | 42.4 | 532.7 |
| 11 | Everett | Middlesex County | 56.2 | 50,045 | shortage of 2,750 | 26.8 | 451.5 |
| 12 | Salem | Essex County | 58.2 | 44,795 | shortage of 2,611 | 29.1 | 402.6 |
| 13 | Malden | Middlesex County | 52.6 | 65,906 | shortage of 2,605 | 42.0 | 402.6 |
| 14 | Brockton | Plymouth County | 58.8 | 105,386 | shortage of 2,220 | 58.7 | 333.8 |
| 15 | Chelsea | Suffolk County | 60.7 | 39,908 | shortage of 2,195 | 41.2 | 376.0 |

## 6. Top candidate construction sites

40,873 screened parcels (vacant or developable land use, at least 0.5 acre, no more than 50% in protected open space, wetlands or FEMA 100-year flood zones) scored 0-100 (weights in REPORT.md 3.5). Ring figures are area-share-weighted tract totals within 5 km; homeless figures within rings are estimates. Full lists in reports/candidate_sites.csv and the site explorer.

Top site: Fall River — 8.3-acre parcel of developable industrial land in Fall River. Scores well on: Need Index within 5 km (population-weighted); affordable-home shortage for extremely-low-income renters within 5 km; estimated people experiencing homelessness within 5 km; closeness to the nearest MBTA/RTA stop; inside an MBTA Communities (Section 3A) multifamily district; larger lot. Need Index within 5 km is 61 of 100. Within 5 km there is an estimated shortage of 4,635 homes affordable to extremely-low-income renters. About 649 people experiencing homelessness are estimated within 5 km (modelled estimate). Nearest transit stop: William St and Beach St (bus, 0.2 km). Inside an MBTA Communities multifamily zoning district. Estimated land cost about $9.0 M ($25/sq ft tract median assessed land value). Note: partly in FEMA 100-year flood zone (12% of lot).

### 6.1 Statewide, top 15

| State rank | Town | County | Score | Acres | Need Index (5 km) | ELI gap (5 km) | Homeless within 5 km | Nearest stop (km) | 3A district |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Fall River | Bristol County | 87.2 | 8.30 | 61.3 | shortage of 4,635 | 648.8 (estimate) | 0.22 | yes |
| 2 | Lawrence | Essex County | 86.4 | 3.95 | 60.2 | shortage of 5,609 | 939.1 (estimate) | 0.17 | yes |
| 3 | Worcester | Worcester County | 86.0 | 1.96 | 60.3 | shortage of 8,528 | 1,263.3 (estimate) | 0.26 | yes |
| 4 | Worcester | Worcester County | 86.0 | 1.92 | 59.6 | shortage of 8,676 | 1,290.8 (estimate) | 0.07 | yes |
| 5 | Worcester | Worcester County | 86.0 | 1.26 | 60.3 | shortage of 8,550 | 1,267.9 (estimate) | 0.11 | yes |
| 6 | Worcester | Worcester County | 85.8 | 1.69 | 60.3 | shortage of 8,709 | 1,293.3 (estimate) | 0.06 | yes |
| 7 | Worcester | Worcester County | 85.7 | 1.55 | 59.6 | shortage of 8,693 | 1,292.9 (estimate) | 0.05 | yes |
| 8 | Worcester | Worcester County | 85.3 | 1.11 | 60.3 | shortage of 8,457 | 1,252.6 (estimate) | 0.22 | yes |
| 9 | Worcester | Worcester County | 85.1 | 0.74 | 60.3 | shortage of 8,525 | 1,264.1 (estimate) | 0.05 | yes |
| 10 | Worcester | Worcester County | 84.8 | 1.09 | 60.3 | shortage of 8,480 | 1,255.4 (estimate) | 0.32 | yes |
| 11 | Taunton | Bristol County | 84.8 | 8.58 | 57.2 | shortage of 1,416 | 172.4 (estimate) | 0.39 | yes |
| 12 | Lowell | Middlesex County | 84.5 | 1.07 | 60.6 | shortage of 4,979 | 885.1 (estimate) | 0.17 | yes |
| 13 | Lawrence | Essex County | 84.2 | 0.90 | 60.0 | shortage of 5,649 | 947.4 (estimate) | 0.07 | yes |
| 14 | Lowell | Middlesex County | 84.1 | 0.74 | 60.8 | shortage of 4,943 | 875.0 (estimate) | 0.09 | yes |
| 15 | Worcester | Worcester County | 83.9 | 0.64 | 60.2 | shortage of 8,740 | 1,298.7 (estimate) | 0.11 | yes |

### 6.2 Best site in each county

| State rank | Town | County | Score | Acres | Need Index (5 km) | ELI gap (5 km) | Homeless within 5 km | Nearest stop (km) | 3A district |
|---|---|---|---|---|---|---|---|---|---|
| 1413 | Yarmouth | Barnstable County | 72.2 | 27.83 | 60.9 | shortage of 805 | 104.1 (estimate) | 0.57 | no |
| 475 | Pittsfield | Berkshire County | 74.8 | 36.45 | 56.0 | shortage of 1,243 | 143.3 (estimate) | 0.19 | no |
| 1 | Fall River | Bristol County | 87.2 | 8.30 | 61.3 | shortage of 4,635 | 648.8 (estimate) | 0.22 | yes |
| 20920 | Edgartown | Dukes County | 43.7 | 1.90 | 53.8 | shortage of 43 | 1.2 (estimate) | 0.25 | no |
| 2 | Lawrence | Essex County | 86.4 | 3.95 | 60.2 | shortage of 5,609 | 939.1 (estimate) | 0.17 | yes |
| 910 | Greenfield | Franklin County | 73.5 | 50.06 | 56.6 | shortage of 588 | 77.3 (estimate) | 0.36 | no |
| 27 | Springfield | Hampden County | 81.7 | 6.16 | 60.6 | shortage of 7,237 | 1,478.5 (estimate) | 0.16 | no |
| 174 | Pelham | Hampshire County | 76.7 | 21.25 | 59.4 | shortage of 732 | 78.0 (estimate) | 0.62 | no |
| 12 | Lowell | Middlesex County | 84.5 | 1.07 | 60.6 | shortage of 4,979 | 885.1 (estimate) | 0.17 | yes |
| 22083 | Nantucket | Nantucket County | 42.4 | 8.31 | 45.0 | shortage of 118 | 12.3 (estimate) | 0.23 | no |
| 44 | Milton | Norfolk County | 79.4 | 7.16 | 51.8 | shortage of 4,947 | 911.2 (estimate) | 0.12 | yes |
| 26 | Brockton | Plymouth County | 82.0 | 1.03 | 57.5 | shortage of 2,324 | 349.9 (estimate) | 0.10 | yes |
| 492 | Revere | Suffolk County | 74.8 | 29.59 | 56.0 | shortage of 8,438 | 1,450.5 (estimate) | 0.19 | no |
| 3 | Worcester | Worcester County | 86.0 | 1.96 | 60.3 | shortage of 8,528 | 1,263.3 (estimate) | 0.26 | yes |
