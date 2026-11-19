
from pathlib import Path
import re
import pandas as pd


TABLE_COLUMNS = {
    "F_TRX": [
        "TRX_ID", "LN", "DT_KEY", "SHP_DT_KEY",
        "CUST_KEY", "PRD_KEY", "REP_KEY", "QTY",
        "AMT1", "AMT2", "AMT3", "STS_CD", "FLG_1"
    ],
    "D_CUST": [
        "CUST_KEY", "NM", "RGN_CD", "SEG", "CRT_DT"
    ],
    "D_PRD": [
        "PRD_KEY", "NM", "CAT_CD", "SUB_CAT", "LST_PRC"
    ],
    "D_CAL": [
        "DT_KEY", "DT", "YR", "QTR", "MO", "MO_NM", "YR_MO"
    ],
    "D_REP": [
        "REP_KEY", "NM", "RGN_CD", "HIRE_DT", "ANNUAL_COMP"
    ],
}


def add_issue(findings, obj, obj_type, issue, severity, fix):
    findings.append({
        "object": obj,
        "object_type": obj_type,
        "issue": issue,
        "severity": severity,
        "fix": fix
    })


def scan_model(model_path, glossary_path):

    model = Path(model_path).read_text(encoding="utf-8")
    glossary = Path(glossary_path).read_text(encoding="utf-8")

    findings = []

    # -------------------------------------------------
    # 1. MISSING DESCRIPTIONS
    # -------------------------------------------------

    if "No table or column has a description" in model:

        for table, columns in TABLE_COLUMNS.items():

            add_issue(
                findings, table, "Table",
                "Missing table description",
                "Medium",
                "Add a clear business-purpose description."
            )

            for column in columns:
                add_issue(
                    findings, f"{table}[{column}]", "Column",
                    "Missing column description",
                    "Medium",
                    "Add a business-friendly description "
                    "including units or code meanings."
                )

    # -------------------------------------------------
    # 2. UNCLEAR NAMING
    # -------------------------------------------------

    unclear_names = {
        "F_TRX[LN]": "Describe as transaction line number.",
        "F_TRX[AMT1]": "Describe as invoiced sales value.",
        "F_TRX[AMT2]": "Describe as cost of goods.",
        "F_TRX[AMT3]": "Describe as discount amount.",
        "F_TRX[STS_CD]": "Document order status codes.",
        "F_TRX[FLG_1]": "Describe as online order indicator.",
        "D_CUST[NM]": "Describe as customer name.",
        "D_CUST[RGN_CD]": "Document region codes.",
        "D_CUST[SEG]": "Document customer segment codes.",
        "D_PRD[NM]": "Describe as product name.",
        "D_PRD[CAT_CD]": "Document product category codes.",
        "D_PRD[SUB_CAT]": "Describe as product subcategory.",
        "D_REP[NM]": "Describe as sales representative name.",
        "D_REP[RGN_CD]": "Document region codes."
    }

    for obj, fix in unclear_names.items():
        add_issue(
            findings, obj, "Column",
            "Abbreviated or unclear business name",
            "Medium", fix
        )

    # -------------------------------------------------
    # 3. MISSING SYNONYMS
    # -------------------------------------------------

    synonym_columns = [
        "D_CUST[RGN_CD]",
        "D_CUST[SEG]",
        "D_PRD[CAT_CD]",
        "F_TRX[STS_CD]",
        "F_TRX[FLG_1]"
    ]

    for obj in synonym_columns:
        add_issue(
            findings, obj, "Column",
            "Business synonyms are not documented",
            "Medium",
            "Add business terms and alternative names "
            "used by business users."
        )

    # -------------------------------------------------
    # 4. AMBIGUOUS OR INCORRECT MEASURES
    # -------------------------------------------------

    measure_rules = [
        (
            "F_TRX[Measure 1]",
            "Generic measure name is ambiguous",
            "High",
            "Rename to a meaningful business metric "
            "and document its definition."
        ),
        (
            "F_TRX[Rev]",
            "Revenue measure does not use the official "
            "Finance-approved business name",
            "High",
            "Rename to Net Revenue and document its "
            "completed-order filter."
        ),
        (
            "F_TRX[Margin]",
            "Margin formula conflicts with the "
            "Finance-approved definition",
            "Critical",
            "Calculate official Margin using Net Revenue "
            "minus cost of completed lines."
        ),
        (
            "F_TRX[Margin %]",
            "Margin percentage uses an ambiguous "
            "denominator",
            "High",
            "Divide official Margin by Net Revenue."
        )
    ]

    for obj, issue, severity, fix in measure_rules:
        measure = obj.split("[")[1].rstrip("]")

        if re.search(
            rf"^\s*{re.escape(measure)}\s*=",
            model,
            re.MULTILINE
        ):
            add_issue(
                findings, obj, "Measure",
                issue, severity, fix
            )

    # -------------------------------------------------
    # 5. VISIBLE IDENTIFIER / KEY COLUMNS
    # -------------------------------------------------

    key_columns = [
        "F_TRX[TRX_ID]",
        "F_TRX[DT_KEY]",
        "F_TRX[SHP_DT_KEY]",
        "F_TRX[CUST_KEY]",
        "F_TRX[PRD_KEY]",
        "F_TRX[REP_KEY]",
        "D_CUST[CUST_KEY]",
        "D_PRD[PRD_KEY]",
        "D_CAL[DT_KEY]",
        "D_REP[REP_KEY]"
    ]

    if "All columns are visible" in model:
        for obj in key_columns:
            add_issue(
                findings, obj, "Column",
                "Technical identifier is visible to users",
                "Medium",
                "Hide technical keys from the business-facing "
                "field list while retaining relationships."
            )

    # -------------------------------------------------
    # 6. SUMMARIZATION SETTINGS
    # -------------------------------------------------

    if 'default "Sum" summarization' in model:

        numeric_keys = [
            "F_TRX[TRX_ID]",
            "F_TRX[DT_KEY]",
            "F_TRX[SHP_DT_KEY]",
            "F_TRX[CUST_KEY]",
            "F_TRX[PRD_KEY]",
            "F_TRX[REP_KEY]",
            "D_CUST[CUST_KEY]",
            "D_PRD[PRD_KEY]",
            "D_CAL[DT_KEY]",
            "D_CAL[YR]",
            "D_REP[REP_KEY]"
        ]

        for obj in numeric_keys:
            add_issue(
                findings, obj, "Column",
                "Numeric identifier or year uses Sum summarization",
                "High",
                "Set summarization to Do not summarize "
                "and validate the intended aggregation."
            )

    # -------------------------------------------------
    # 7. RELATIONSHIP CONFIGURATION
    # -------------------------------------------------

    if "No | Single" in model or "SHP_DT_KEY" in model:
        add_issue(
            findings,
            "F_TRX[SHP_DT_KEY] -> D_CAL[DT_KEY]",
            "Relationship",
            "Shipping date relationship is inactive",
            "High",
            "Document the inactive relationship and use "
            "an explicit shipping-date calculation strategy."
        )

    if "Both" in model:
        add_issue(
            findings,
            "F_TRX[CUST_KEY] -> D_CUST[CUST_KEY]",
            "Relationship",
            "Customer relationship uses bidirectional filtering",
            "Medium",
            "Prefer single-direction filtering unless "
            "bidirectional filtering is explicitly required."
        )

    # -------------------------------------------------
    # 8. DATE HANDLING
    # -------------------------------------------------

    if "not marked as a date table" in model:
        add_issue(
            findings, "D_CAL", "Table",
            "Calendar table is not marked as a date table",
            "High",
            "Mark D_CAL[DT] as the model date column "
            "and validate date continuity."
        )

    if "not sorted by MO" in model:
        add_issue(
            findings, "D_CAL[MO_NM]", "Column",
            "Month name is not sorted by month number",
            "Medium",
            "Sort MO_NM by D_CAL[MO]."
        )

    # -------------------------------------------------
    # 9. SENSITIVE DATA
    # -------------------------------------------------

    if (
        "All columns are visible" in model
        and "Sales rep compensation" in glossary
    ):
        add_issue(
            findings, "D_REP[ANNUAL_COMP]", "Column",
            "Confidential compensation data is visible",
            "Critical",
            "Hide the field and enforce appropriate "
            "permissions before enabling AI access."
        )

    # Create report
    report = pd.DataFrame(
        findings,
        columns=[
            "object",
            "object_type",
            "issue",
            "severity",
            "fix"
        ]
    )

    return report.drop_duplicates().reset_index(drop=True)


def save_report(report, output_path):

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report.to_csv(output_path, index=False)
