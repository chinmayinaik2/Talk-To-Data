# Semantic model: "Sales_Model_v2"

This is the model as the customer's BI team built it. Recreate it in Power BI Desktop (or as a Fabric semantic model) from the CSV files in `data/`, **exactly as described**, problems included. Fixing it is your job, later.

## Tables and columns (as named in the source)

| Table | Columns |
|---|---|
| F_TRX | TRX_ID, LN, DT_KEY, SHP_DT_KEY, CUST_KEY, PRD_KEY, REP_KEY, QTY, AMT1, AMT2, AMT3, STS_CD, FLG_1 |
| D_CUST | CUST_KEY, NM, RGN_CD, SEG, CRT_DT |
| D_PRD | PRD_KEY, NM, CAT_CD, SUB_CAT, LST_PRC |
| D_CAL | DT_KEY, DT, YR, QTR, MO, MO_NM, YR_MO |
| D_REP | REP_KEY, NM, RGN_CD, HIRE_DT, ANNUAL_COMP |

No table or column has a description. All columns are visible. Numeric columns keep the default "Sum" summarization (including keys and YR).

## Relationships

| From | To | Cardinality | Active | Cross-filter |
|---|---|---|---|---|
| F_TRX[DT_KEY] | D_CAL[DT_KEY] | many-to-one | Yes | Single |
| F_TRX[SHP_DT_KEY] | D_CAL[DT_KEY] | many-to-one | **No** | Single |
| F_TRX[CUST_KEY] | D_CUST[CUST_KEY] | many-to-one | Yes | **Both** |
| F_TRX[PRD_KEY] | D_PRD[PRD_KEY] | many-to-one | Yes | Single |
| F_TRX[REP_KEY] | D_REP[REP_KEY] | many-to-one | Yes | Single |

D_CAL is **not** marked as a date table. MO_NM is **not** sorted by MO.

## Measures (in table F_TRX)

```
Measure 1 = SUM ( F_TRX[AMT1] )
Rev       = CALCULATE ( SUM ( F_TRX[AMT1] ), F_TRX[STS_CD] = "C" )
Margin    = SUM ( F_TRX[AMT1] ) - SUM ( F_TRX[AMT2] )
Margin %  = DIVIDE ( [Margin], [Measure 1] )
Cnt       = COUNTROWS ( F_TRX )
Cust #    = DISTINCTCOUNT ( F_TRX[CUST_KEY] )
Disc      = SUM ( F_TRX[AMT3] )
```

## What the codes mean (known to the BI team, not written anywhere in the model)

| Column | Codes |
|---|---|
| D_CUST[RGN_CD], D_REP[RGN_CD] | N North, S South, E East, W West |
| D_CUST[SEG] | E Enterprise, S SMB, C Consumer |
| D_PRD[CAT_CD] | BK Bikes, AC Accessories, CL Clothing, CP Components |
| F_TRX[STS_CD] | C Completed, X Cancelled, R Returned |
| F_TRX[FLG_1] | 1 = online order, 0 = store or phone |
| F_TRX[AMT1] | Invoiced sales value of the line |
| F_TRX[AMT2] | Cost of goods for the line |
| F_TRX[AMT3] | Discount: list price value minus invoiced value |

Data covers 1 Jan 2024 to 31 Dec 2025.
