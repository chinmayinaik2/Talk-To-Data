
import re
import pandas as pd


REPORT_COLUMNS = [
    "object",
    "object_type",
    "issue",
    "severity",
    "fix"
]


UNCLEAR_TOKENS = {
    "NM",
    "CD",
    "FLG",
    "AMT",
    "QTY",
    "DT",
    "YR",
    "MO",
    "NO",
    "CNT"
}


# ---------------------------------------------------------
# HELPER: Add a finding to the report
# ---------------------------------------------------------

def add_issue(
    findings,
    object_name,
    object_type,
    issue,
    severity,
    fix
):
    findings.append({
        "object": object_name,
        "object_type": object_type,
        "issue": issue,
        "severity": severity,
        "fix": fix
    })


# ---------------------------------------------------------
# HELPER: Identify technical identifier columns
# ---------------------------------------------------------

def find_identifier_columns(columns):
    identifiers = []

    for column in columns:
        column_name = str(column).upper()

        if (
            column_name.endswith("_ID")
            or column_name.endswith("_KEY")
            or column_name in {"ID", "KEY"}
        ):
            identifiers.append(column)

    return identifiers


# ---------------------------------------------------------
# HELPER: Identify unclear technical abbreviations
# ---------------------------------------------------------

def find_unclear_columns(columns):
    unclear = []

    for column in columns:
        tokens = re.split(
            r"[_\d]+",
            str(column).upper()
        )

        if any(token in UNCLEAR_TOKENS for token in tokens):
            unclear.append(column)

    return unclear


# ---------------------------------------------------------
# HELPER: Discover likely date tables
# ---------------------------------------------------------

def find_date_tables(metadata):
    date_tables = []

    tables = metadata.get("tables", {})

    date_column_names = {
        "DATE",
        "DT",
        "FULL_DATE",
        "CALENDAR_DATE"
    }

    date_key_names = {
        "DATE_KEY",
        "DT_KEY"
    }

    for table, columns in tables.items():
        normalized_columns = {
            str(column).upper()
            for column in columns
        }

        has_date_column = bool(
            normalized_columns.intersection(date_column_names)
        )

        has_date_key = bool(
            normalized_columns.intersection(date_key_names)
        )

        if has_date_column and has_date_key:
            date_tables.append(table)

    return date_tables


# ---------------------------------------------------------
# MAIN: Generic metadata scanner
# ---------------------------------------------------------

def scan_generic(metadata):

    findings = []

    tables = metadata.get("tables", {})
    settings = metadata.get("settings", {})

    # 1. Missing descriptions
    #
    # The current parser only provides a model-level flag.
    # It cannot identify individual tables or columns whose
    # descriptions are missing.
    #
    # Therefore, generate one model-level finding.

    if settings.get("descriptions_missing", False):

        add_issue(
            findings,
            metadata.get("model_name", "Semantic model"),
            "Model",
            "One or more descriptions may be missing",
            "Medium",
            "The available metadata indicates that descriptions "
            "are missing, but does not identify the affected "
            "tables or columns. Inspect individual object "
            "descriptions to confirm."
        )

    # 2. Technical abbreviations in column names

    for table, columns in tables.items():

        unclear_columns = find_unclear_columns(columns)

        for column in unclear_columns:

            add_issue(
                findings,
                f"{table}[{column}]",
                "Column",
                "Column name contains a technical abbreviation",
                "Medium",
                "Use a clear business-friendly name or document "
                "the abbreviation with a description and synonyms."
            )

    # 3. Technical identifiers potentially visible to users
    #
    # This is based on a model-level visibility flag.
    # It does not establish individual column visibility.

    if settings.get("all_columns_visible", False):

        for table, columns in tables.items():

            identifier_columns = find_identifier_columns(columns)

            for column in identifier_columns:

                add_issue(
                    findings,
                    f"{table}[{column}]",
                    "Column",
                    "Technical identifier is visible to users",
                    "Medium",
                    "Consider hiding technical identifiers from "
                    "the business-facing field list. Verify the "
                    "individual column visibility setting."
                )

    # 4. Identifier or year columns may have inappropriate Sum
    #
    # The parser currently captures only the model-level
    # default summarization flag, not individual settings.
    # Therefore, these are Medium review recommendations.

    if settings.get("default_sum_summarization", False):

        for table, columns in tables.items():

            identifier_columns = find_identifier_columns(columns)

            year_columns = [
                column
                for column in columns
                if str(column).upper() in {"YEAR", "YR"}
            ]

            candidates = identifier_columns + year_columns

            for column in columns:

                if column in candidates:

                    add_issue(
                        findings,
                        f"{table}[{column}]",
                        "Column",
                        "Identifier or year may have inappropriate "
                        "Sum summarization",
                        "Medium",
                        "Validate the column's summarization setting. "
                        "Identifiers and year values generally should "
                        "not be summed."
                    )

    # 5. Relationship checks

    relationships = metadata.get("relationships", [])

    for relationship in relationships:

        from_column = relationship.get("from", "")
        to_column = relationship.get("to", "")

        active = str(
            relationship.get("active", "")
        ).strip().lower()

        cross_filter = str(
            relationship.get("cross_filter", "")
        ).strip().lower()

        relationship_name = (
            f"{from_column} -> {to_column}"
        )

        # Inactive relationships

        if active in {"no", "false", "inactive", "0"}:

            add_issue(
                findings,
                relationship_name,
                "Relationship",
                "Inactive relationship requires documentation",
                "Low",
                "Document why the relationship is inactive and "
                "explain how users should activate it when needed."
            )

        # Bidirectional relationships

        if cross_filter == "both":

            add_issue(
                findings,
                relationship_name,
                "Relationship",
                "Bidirectional cross-filtering requires review",
                "Medium",
                "Review whether bidirectional filtering is necessary "
                "and whether it could introduce ambiguous filter paths."
            )

    # 6. Date table configuration

    if settings.get("date_table_not_marked", False):

        date_tables = find_date_tables(metadata)

        for table in date_tables:

            add_issue(
                findings,
                table,
                "Table",
                "Likely date table is not marked as a date table",
                "High",
                "Mark the appropriate date column as the "
                "model's date table column."
            )

    # 7. Month-name sorting

    if settings.get("month_not_sorted", False):

        for table, columns in tables.items():

            for column in columns:

                if str(column).upper() in {
                    "MO_NM",
                    "MONTH_NAME"
                }:

                    add_issue(
                        findings,
                        f"{table}[{column}]",
                        "Column",
                        "Month name may not be sorted by month number",
                        "Medium",
                        "Sort the month-name column by its "
                        "corresponding month-number column."
                    )

    # Convert findings into a DataFrame

    report = pd.DataFrame(
        findings,
        columns=REPORT_COLUMNS
    )

    report.attrs["model_name"] = metadata.get(
        "model_name",
        "Unknown"
    )

    return report
