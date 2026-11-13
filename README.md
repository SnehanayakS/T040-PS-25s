# PS-123 – Customs Duty and Import Clearance Assessment Engine with HS Codes, Exemptions and Risk Channels — Sample Data Pack

Prepared by 10 SECONDS for Team T040.

Input for a customs assessment engine: 60 HS codes, 12 notifications, 4 anti-dumping entries, 30 days of exchange rates, 15 importers, 40 bills of entry with 153 lines and an event file (`commands.txt`) holding 60 payment/examination/amendment events plus the ASSESS and OUT_OF_CHARGE lifecycle lines. All bills are filed in October 2026.

Pack conventions where the brief is silent: AV and every duty component are rounded to the nearest rupee (half up) per line, bill totals are sums of line values; the exchange rate is the one for `bill_date`; ad-valorem anti-dumping is a % of AV, specific anti-dumping is Rs per unit of quantity; 'value' for the risk channel is the bill's total AV; working days are Monday–Saturday except 2026-10-02 and 2026-10-20; 'within 12 months' for a COO is inclusive of the same calendar date one year earlier; interest is simple, 15% p.a., daily on a 365-day year, counted from the day after the assessment date up to and including the payment date, rounded to the rupee.

## Files

| File | What it holds | Rows |
|---|---|---|
| `tariff.csv` | HS code master: BCD, IGST, cess, FTA preferential rate, sensitive flag | 60 data rows |
| `fta_countries.csv` | Countries with which India has an FTA in this pack | 7 data rows |
| `notifications.csv` | Exemption notifications (partial or conditional end-use) | 12 data rows |
| `antidumping.csv` | Anti-dumping entries by HS code and origin | 4 data rows |
| `exchange_rates.csv` | Customs exchange rates, 30 days x 5 currencies | 150 data rows |
| `importers.csv` | Importers with IEC, AEO status and starting compliance score | 15 data rows |
| `authorisations.csv` | Advance Authorisation / EPCG ledger balances | 3 data rows |
| `bills.csv` | Bills of entry (header) | 40 data rows |
| `bill_lines.csv` | Bill-of-entry lines | 153 data rows |
| `commands.txt` | Load commands, then assessment/payment/examination/amendment events in time order | 152 command lines (excluding comments) |

Row numbers quoted below are 1-based data-row numbers (the header is row 0). Line numbers for `commands.txt` are physical line numbers including comment lines.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with up to 2 places (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix. A cell shown as empty in a CSV means "not applicable" and is only allowed where the notes say so.

### `tariff.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| hs_code | string | 8 digits | unique | primary key |
| description | string | — | — | — |
| unit | enum | — | NOS, KG, PRS, LTR, GM | unit of quantity on lines |
| bcd_rate | decimal | % | 0–70 | standard Basic Customs Duty |
| igst_rate | decimal | % | 3, 5, 12, 18, 28 | — |
| cess_rate | decimal | % | 0, 12, 22 | compensation cess, same base as IGST |
| fta_rate | decimal | % | ≤ bcd_rate | BCD under any FTA in fta_countries.csv when the FTA conditions are met |
| sensitive | boolean | — | true, false | sensitive list for the risk channel |

### `fta_countries.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| country_code | string | ISO 3166 alpha-2 | — | — |
| agreement | string | — | — | — |

### `notifications.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| notification_id | string | NOTN-nn | — | — |
| hs_code | string | — | tariff.csv | — |
| notified_bcd_rate | decimal | % | — | reduced BCD |
| exemption_type | enum | — | PARTIAL, CONDITIONAL_END_USE | conditional needs bond_flag = true and an end-use certificate within 6 months |
| description | string | — | — | — |

### `antidumping.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| ad_id | string | AD-nn | — | — |
| hs_code | string | — | tariff.csv | — |
| origin_country | string | ISO alpha-2 | — | applies only to this origin |
| basis | enum | — | SPECIFIC, AD_VALOREM | — |
| rate | decimal | Rs per unit or % | — | — |
| rate_unit | enum | — | INR_PER_KG, PCT_OF_AV | — |

### `exchange_rates.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| rate_date | date | YYYY-MM-DD | 2026-10-01 … 2026-10-30 | — |
| currency | enum | — | USD, EUR, GBP, JPY, AED | — |
| inr_per_unit | decimal | Rs per 1 unit | — | JPY has 4 decimals, others 2 |

### `importers.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| importer_id | string | IMP-nn | — | — |
| importer_name | string | — | — | — |
| iec | string | 10 chars, PAN-shaped | — | fake but well-formed |
| aeo_status | enum | — | NONE, T1, T2, T3 | T2 and above get 15-day deferred payment; any AEO is upgraded one channel |
| compliance_score | integer | 0–100 | — | score at the start of the pack period |
| city | string | — | — | — |

### `authorisations.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| auth_id | string | AA-nnnnnnn / EPCG-nnnnnnn | — | — |
| importer_id | string | — | importers.csv | — |
| scheme | enum | — | ADVANCE_AUTH, EPCG | — |
| hs_code | string | — | tariff.csv | — |
| qty_balance | integer | line unit | — | remaining duty-free quantity |
| value_balance_inr | decimal | Rs | — | remaining duty-free AV |
| valid_until | date | — | — | — |

### `bills.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| bill_id | string | BE-nnnn | — | numbered in filing order |
| importer_id | string | — | importers.csv | — |
| port_code | string | — | INNSA1, INMAA1, INBLR4, INMUN1 | — |
| vessel_arrival_date | date | — | — | may be after filing (advance bill) |
| filing_ts | timestamp | — | — | — |
| bill_date | date | — | — | = filing date; selects the exchange rate |
| total_packages | integer | — | — | RED examines 10% of packages, 100% if any line is sensitive |
| customs_system_delay | boolean | — | — | true waives the late-filing charge |
| random_red_flag | boolean | — | — | true forces RED |

### `bill_lines.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| bill_id | string | — | bills.csv | — |
| line_no | integer | 1…n | — | unique within a bill |
| hs_code | string | — | tariff.csv | — |
| description | string | — | — | — |
| quantity | integer | unit column | — | — |
| unit | enum | — | as tariff | — |
| invoice_value | decimal | invoice currency | — | FOB or CIF value per incoterm |
| currency | enum | — | USD, EUR, GBP, JPY, AED | — |
| incoterm | enum | — | FOB, CIF | — |
| freight | decimal | invoice currency | — | FOB lines only; empty for CIF |
| insurance | decimal | invoice currency | — | FOB lines only; empty = not available → 1.125% of FOB |
| origin_country | string | ISO alpha-2 | — | — |
| coo_flag | boolean | — | — | certificate of origin presented |
| coo_date | date | — | — | empty when coo_flag = false |
| value_addition_pct | decimal | % | — | empty when coo_flag = false; FTA needs ≥ 35 |
| notification_id | string | — | notifications.csv | empty = no claim |
| bond_flag | boolean | — | — | end-use bond executed |
| auth_id | string | — | authorisations.csv | empty = no scheme |

## Command file format

`commands.txt` holds one command per line as `COMMAND_NAME|arg1|arg2|...`. Commands must be processed in file order, top to bottom. Lines starting with `#` are comments and blank lines are ignored. Every command used in this pack:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| LOAD_TARIFF / LOAD_FTA / LOAD_NOTIFICATIONS / LOAD_ANTIDUMPING / LOAD_EXCHANGE_RATES / LOAD_IMPORTERS / LOAD_AUTHORISATIONS | file | Load the master file |
| LOAD_BILLS | bills_file\|lines_file | Load bill headers and lines (status FILED) |
| AMEND | bill_id\|line_no\|field\|new_value\|timestamp | field is QUANTITY or INVOICE_VALUE; before ASSESS free, after ASSESS per BR-10 |
| ASSESS | bill_id\|timestamp | Compute AV, duty stack, late-filing charge and risk channel; the timestamp is the assessment time |
| PAY_DUTY | bill_id\|challan_id\|FULL\|timestamp | Pay everything outstanding on the bill at that instant (duty, differential, interest, penalty) |
| EXAM_RESULT | bill_id\|line_no\|found_quantity\|found_invoice_value\|timestamp | Examination finding for a line (found value in the line's invoice currency) |
| WAIVER_REQUEST | bill_id\|timestamp | Request the reduced 25% penalty |
| REFUND_CLAIM | bill_id\|line_no\|timestamp | Refund claim after a duty-reducing amendment |
| END_USE_CERT | bill_id\|line_no\|certificate_date | End-use certificate for a conditional exemption line |
| OUT_OF_CHARGE | bill_id\|timestamp | Clearance; a clean GREEN/ORANGE clearance adds +1 to the importer score |
| RUN_END_USE_CHECK | as_of_date | Demand differential duty + interest for bonded lines without a certificate within 6 months of clearance |
| PRINT_ASSESSMENT_SHEETS / PRINT_CHALLANS | ALL | Print the outputs below |
| PRINT_COMPLIANCE_LEDGER | as_of_date | Print the score ledger |

Commands that fail validation (unknown bill or line, duplicate challan, wrong state) are written to errors.csv and change nothing.

## Planted scenarios

Every edge case in the brief, mapped to the exact record(s) where it occurs, followed by extra traps.

- **EC-01 Freight exactly 20% of FOB**
  - bill_lines.csv row 105 (BE-0028 line 1): FOB USD 12500.00 with freight USD 2500.00 = exactly 20% of FOB — the cap is not exceeded, so the full freight is added; insurance USD 140.00 is supplied.
- **EC-02 COO dated exactly 12 months before the bill date**
  - bill_lines.csv row 94 (BE-0025 line 1, origin JP): bill_date 2026-10-19, coo_date 2025-10-19 — exactly 12 months, still valid (pack convention: 'within 12 months' is inclusive); value addition 40.00 ≥ 35 so the FTA rate applies.
- **EC-03 Advance Authorisation balance covering 90% of the line quantity**
  - bill_lines.csv row 100 (BE-0026 line 1): quantity 10000 KG under AA-3990001 whose qty_balance is 9000 (90%) — 9000 KG at zero BCD/IGST, the 1000 KG excess pays full duty on its pro-rata AV (value balance is sufficient).
- **EC-04 FTA rate equal to the notification rate (tie)**
  - bill_lines.csv row 73 (BE-0021 line 1, HS 84711000, origin KR with valid COO): FTA rate 5% and NOTN-02 rate 5% are equal — exemptions cannot stack; BCD is 5% (pack convention: on a tie report bcd_basis = FTA, the earlier step in the precedence).
- **EC-05 Bill filed exactly one day after vessel arrival**
  - bills.csv row 34 (BE-0034): vessel_arrival_date 2026-10-23, filing_ts 2026-10-24 23:10:00 — filed on the day following arrival, so no late-filing charge.
- **EC-06 Examination finding exactly 5% over declared**
  - bill_lines.csv row 80 (BE-0022 line 1, RED bill): declared quantity 200 / USD 4000.00; EXAM_RESULT at commands.txt line 79 finds 210 / USD 4200.00 = exactly 5% over — not 'more than 5%', so the differential is collected without penalty and no score deduction.
- **EC-07 Value exactly Rs 50 lakh with score 80**
  - bill_lines.csv row 56 (BE-0015, importer IMP-05 with compliance_score 80, AEO NONE, single CIF line): AV works out to exactly Rs 5000000 (50 lakh) — not 'under Rs 50 lakh', so the bill is ORANGE, not GREEN.
- **EC-08 Compliance score dropping to exactly 40**
  - bill_lines.csv row 70 (BE-0020, importer IMP-11 starting at 55, RED): EXAM_RESULT at commands.txt line 80 finds 12% over declared → −15 → score exactly 40. 40 is not 'under 40', so no 90-day forced RED; IMP-11's next bill BE-0033 is assessed at score 40.

Extra traps (not in the brief, but realistic — your validation should catch them):

- **Freight above the 20% cap and insurance missing** — bill_lines.csv row 117 (BE-0032 line 1): FOB USD 8000.00 with freight USD 2400.00 (30%) → freight capped at USD 1600.00; insurance blank → 1.125% of FOB.
- **Late filing slab** — bills.csv row 24 (BE-0024): arrival 2026-10-13, filed 2026-10-19 — 5 days after the day following arrival → 3 × Rs 5,000 + 2 × Rs 10,000 = Rs 35,000, capped at the bill's total duty.
- **Late filing waived** — bills.csv row 7 (BE-0007): filed 3 days late but customs_system_delay = true → charge waived.
- **Random RED flag** — bills.csv row 30 (BE-0030): random_red_flag = true forces RED regardless of score, value or AEO status.
- **Saturday assessment paid on Monday** — BE-0010 is assessed on a Saturday (commands.txt line 37) and paid on Monday (line 42) — Sunday is not a working day, so this is within 1 working day: no interest.
- **AEO-T2 deferred payment** — BE-0027 (importer IMP-12, AEO T2) pays 10 days after assessment (commands.txt line 144) — inside the 15-day deferment, no interest.
- **Late duty payment** — PAY_DUTY at commands.txt line(s) 116 come 4–7 days after assessment → interest at 15% p.a. from the day after the assessment date.
- **Misdeclaration with waiver request** — bill_lines.csv row 114 (BE-0031 line 1): found 10% over (commands.txt line 112); WAIVER_REQUEST at line 113 and payment at line 146 within 30 days → penalty 25% of the differential instead of 100%; importer IMP-03 score −15.
- **Amendments** — pre-assessment AMEND at commands.txt line 94 (free, assess on the amended quantity); post-assessment increase at line 97 (interest from the original assessment date, paid at line 115); post-assessment decrease at line 69 followed by REFUND_CLAIM at line 148 (inside 1 year).
- **Unknown line in an amendment** — commands.txt line 92 amends line 9 of BE-0028, which has only 4 line(s) → error line, nothing changes.
- **Duplicate payment** — commands.txt line 106 repeats challan CH-00036 of the previous PAY_DUTY for BE-0032 → reject as a duplicate challan, nothing is paid twice.
- **FTA boundary and invalid COO** — bill_lines.csv row 109 value_addition_pct exactly 35.00 (meets the 35% rule); bill_lines.csv row 83 coo_date is 3 days AFTER the bill date → FTA denied, standard BCD.
- **End-use conditional exemption** — bill_lines.csv row 64 (NOTN-03, bond true) gets END_USE_CERT at commands.txt line 149 (within 6 months); bill_lines.csv row 65 (NOTN-09, bond true) never gets one → RUN_END_USE_CHECK|2027-04-30 demands the differential duty with interest from the OUT_OF_CHARGE date.
- **EPCG line** — bill_lines.csv row 42: EPCG authorisation → zero BCD, IGST still payable.

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-12). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these files (CSV, UTF-8, header row, same conventions as above). Column order matters. Where the brief is silent on a format detail, the choice below is binding for evaluation.

### `assessment_lines.csv`

One row per bill line after the final command (re-assessed values where an examination or amendment changed them).

Columns in order: `bill_id`, `line_no`, `hs_code`, `exchange_rate`, `fob_inr`, `freight_inr`, `insurance_inr`, `cif_inr`, `landing_inr`, `av`, `bcd_basis`, `bcd_rate`, `bcd`, `sws`, `antidumping`, `igst_base`, `igst`, `cess`, `line_duty`, `scheme_exempt_qty`

### `challans.csv`

One row per bill.

Columns in order: `bill_id`, `importer_id`, `bill_date`, `assessment_ts`, `channel`, `channel_reason`, `total_av`, `total_duty`, `late_filing_charge`, `interest`, `differential_duty`, `penalty`, `total_payable`, `total_paid`, `outstanding`

### `compliance_ledger.csv`

One row per score change, in processing order.

Columns in order: `importer_id`, `timestamp`, `bill_id`, `event`, `delta`, `score_after`, `forced_red_until`

### `errors.csv`

Rejected commands.

Columns in order: `line_no`, `command`, `reason`

Binding choices: `bcd_basis` is one of STANDARD, FTA, NOTIFICATION, ADVANCE_AUTH, EPCG; `channel` is GREEN, ORANGE or RED; `channel_reason` is one of SCORE_VALUE, SENSITIVE, AEO_UPGRADE, RANDOM_FLAG, LOW_SCORE_LOCK; `forced_red_until` is a date or NONE; money columns are whole rupees written with 2 decimals (e.g. 35000.00).
