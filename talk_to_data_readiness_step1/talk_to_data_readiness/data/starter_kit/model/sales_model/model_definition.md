# Semantic model: "Sales_Performance_Model"

## Tables and columns (as named in the source)

| Table | Columns |
|---|---|
| F_OPPORTUNITY | OPP_ID, ACCOUNT_ID, REP_ID, CREATED_DATE_KEY, CLOSE_DATE_KEY, STAGE_CD, AMOUNT, PROBABILITY, FORECAST_AMT, SOURCE_CD |
| D_ACCOUNT | ACCOUNT_ID, ACCOUNT_NAME, INDUSTRY_CD, REGION_CD, CREATED_DATE |
| D_REP | REP_ID, REP_NAME, REGION_CD, HIRE_DATE |
| D_DATE | DATE_KEY, FULL_DATE, YEAR, QUARTER, MONTH, MONTH_NAME, YEAR_MONTH |
| F_ACTIVITY | ACTIVITY_ID, OPP_ID, REP_ID, ACTIVITY_DATE_KEY, ACTIVITY_TYPE, DURATION_MIN |

No table or column has a description. All columns are visible. Numeric columns keep default "Sum" summarization, including identifiers and YEAR.

## Relationships

| From | To | Cardinality | Active | Cross-filter |
|---|---|---|---|---|
| F_OPPORTUNITY[ACCOUNT_ID] | D_ACCOUNT[ACCOUNT_ID] | many-to-one | Yes | Single |
| F_OPPORTUNITY[REP_ID] | D_REP[REP_ID] | many-to-one | Yes | Both |
| F_OPPORTUNITY[CREATED_DATE_KEY] | D_DATE[DATE_KEY] | many-to-one | Yes | Single |
| F_OPPORTUNITY[CLOSE_DATE_KEY] | D_DATE[DATE_KEY] | many-to-one | No | Single |
| F_ACTIVITY[OPP_ID] | F_OPPORTUNITY[OPP_ID] | many-to-one | Yes | Both |
| F_ACTIVITY[REP_ID] | D_REP[REP_ID] | many-to-one | Yes | Single |
| F_ACTIVITY[ACTIVITY_DATE_KEY] | D_DATE[DATE_KEY] | many-to-one | Yes | Single |

D_DATE is not marked as a date table. MONTH_NAME is not sorted by MONTH.

## Measures (in table F_OPPORTUNITY)

```dax
Total Pipeline = SUM ( F_OPPORTUNITY[AMOUNT] )
Weighted Pipeline = SUM ( F_OPPORTUNITY[FORECAST_AMT] )
Won Revenue = CALCULATE ( SUM ( F_OPPORTUNITY[AMOUNT] ), F_OPPORTUNITY[STAGE_CD] = "W" )
Open Deals = DISTINCTCOUNT ( F_OPPORTUNITY[OPP_ID] )
Win Rate = DIVIDE ( [Won Revenue], [Total Pipeline] )
Average Deal Size = AVERAGE ( F_OPPORTUNITY[AMOUNT] )
Activity Count = COUNTROWS ( F_ACTIVITY )
```

## What the codes mean

- F_OPPORTUNITY[STAGE_CD]: Q = Qualified, P = Proposal, N = Negotiation, W = Won, L = Lost.
- F_OPPORTUNITY[SOURCE_CD]: W = Website, R = Referral, C = Campaign, E = Events.
- D_ACCOUNT[INDUSTRY_CD]: T = Technology, F = Finance, H = Healthcare, M = Manufacturing.
- D_ACCOUNT[REGION_CD] and D_REP[REGION_CD]: N = North, S = South, E = East, W = West.

## Business context

The model tracks sales opportunities, accounts, sales representatives, and sales activities. Opportunity amount represents the potential deal value. Forecast amount represents the probability-weighted opportunity value. Won Revenue includes opportunities whose stage is Won.

The data covers the sales reporting period from January 2025 to December 2026.