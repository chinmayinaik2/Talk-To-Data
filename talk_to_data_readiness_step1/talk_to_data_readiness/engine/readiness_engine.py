
from pathlib import Path
import re

import pandas as pd

from engine.metadata_parser import parse_model
from engine.generic_rules import scan_generic, find_date_tables
from engine.business_rules import scan_business
from engine.governance_rules import scan_governance


REPORT_COLUMNS = [
    "object",
    "object_type",
    "issue",
    "severity",
    "fix",
    "category",
    "model_name",
    "rule_id",
    "evidence",
    "confidence",
    "business_impact",
    "validation_status"
]


# ---------------------------------------------------------
# HELPER: Read business glossary definitions
# ---------------------------------------------------------

def read_glossary(glossary_path):
    definitions = {}

    try:
        with open(
            glossary_path,
            "r",
            encoding="utf-8"
        ) as file:
            for line in file:
                match = re.match(
                    r"[-*]\s*\*\*(.+?):\*\*\s*(.+)",
                    line.strip()
                )

                if match:
                    term = match.group(1).strip()
                    definition = match.group(2).strip()
                    definitions[term] = definition

    except FileNotFoundError:
        pass

    return definitions


# ---------------------------------------------------------
# HELPER: Identify table and column from object name
# ---------------------------------------------------------

def split_object_name(object_name):
    match = re.match(
        r"^(.+)\[([^\]]+)\]$",
        str(object_name)
    )

    if match:
        return match.group(1), match.group(2)

    return None, None


# ---------------------------------------------------------
# HELPER: Find relationship evidence
# ---------------------------------------------------------

def find_relationship_evidence(object_name, metadata):
    for relationship in metadata.get("relationships", []):

        relationship_name = (
            f"{relationship.get('from', '')} -> "
            f"{relationship.get('to', '')}"
        )

        if relationship_name == object_name:
            return relationship

    return None


# ---------------------------------------------------------
# HELPER: Generate a stable rule ID
# ---------------------------------------------------------

def get_rule_id(category, issue):

    issue = str(issue).lower()

    if category == "Metadata":

        if "description" in issue:
            return "MD-DESCRIPTION"

        if "technical abbreviation" in issue:
            return "MD-TECHNICAL-NAME"

        if "identifier is visible" in issue:
            return "MD-IDENTIFIER-VISIBILITY"

        if "summarization" in issue:
            return "MD-AGGREGATION"

        if "inactive relationship" in issue:
            return "MD-INACTIVE-RELATIONSHIP"

        if "bidirectional" in issue:
            return "MD-BIDIRECTIONAL-RELATIONSHIP"

        if "date table" in issue:
            return "MD-DATE-TABLE"

        if "month name" in issue:
            return "MD-MONTH-SORT"

    elif category == "Business Logic":

        if "no clearly matching measure" in issue:
            return "BL-GLOSSARY-COVERAGE"

        if "includes conditions" in issue:
            return "BL-DEFINITION-VALIDATION"

        if "open-record condition" in issue:
            return "BL-OPEN-POPULATION"

        if "exited-employee population" in issue:
            return "BL-EXIT-POPULATION"

    elif category == "Security & Governance":

        if "sensitive" in issue:
            return "GOV-SENSITIVE-FIELD"

    return "GENERAL-REVIEW"


# ---------------------------------------------------------
# HELPER: Add evidence and context to every finding
# ---------------------------------------------------------

def build_finding_context(row, metadata, glossary):

    object_name = str(row["object"])
    issue = str(row["issue"])
    category = str(row["category"])

    tables = metadata.get("tables", {})
    measures = metadata.get("measures", {})
    settings = metadata.get("settings", {})

    table_name, column_name = split_object_name(object_name)

    evidence = ""
    confidence = "Medium"
    business_impact = ""
    validation_status = "Manual validation required"

    # -----------------------------------------------------
    # METADATA FINDINGS
    # -----------------------------------------------------

    if category == "Metadata":

        # Missing descriptions

        if "descriptions may be missing" in issue.lower():

            evidence = (
                "The parser reports descriptions_missing=True "
                "at the model level. It does not identify the "
                "individual tables or columns affected."
            )

            confidence = "Medium"

            business_impact = (
                "Missing descriptions can make it harder for "
                "natural-language analytics to understand "
                "business objects and their meaning."
            )

            validation_status = (
                "Inspect individual table and column descriptions."
            )

        # Technical abbreviations

        elif "technical abbreviation" in issue.lower():

            evidence = (
                f"The column name '{column_name}' contains "
                "technical abbreviations identified by the "
                "scanner's naming heuristic."
            )

            confidence = "Medium"

            business_impact = (
                "Unclear field names can make it difficult for "
                "users and language models to identify the "
                "correct business concept."
            )

            validation_status = (
                "Review the business meaning and add descriptions "
                "or synonyms where needed."
            )

        # Technical identifier visibility

        elif "identifier is visible" in issue.lower():

            evidence = (
                f"The field {object_name} matches the identifier "
                "naming rule. The parser reports "
                f"all_columns_visible={settings.get('all_columns_visible')} "
                "at the model level. Individual column visibility "
                "was not captured."
            )

            confidence = "Low"

            business_impact = (
                "Technical identifiers can create confusing "
                "natural-language field choices and may expose "
                "unnecessary technical details."
            )

            validation_status = (
                "Verify individual column visibility in the "
                "semantic model."
            )

        # Aggregation and summarization

        elif "summarization" in issue.lower():

            evidence = (
                f"The field {object_name} matches an identifier "
                "or year naming pattern. The parser reports "
                f"default_sum_summarization="
                f"{settings.get('default_sum_summarization')}. "
                "The individual column summarization setting "
                "was not captured."
            )

            confidence = "Low"

            business_impact = (
                "Incorrect aggregation can produce misleading "
                "results when users ask questions about counts, "
                "years or identifiers."
            )

            validation_status = (
                "Inspect the actual summarization setting "
                "for this column."
            )

        # Relationship checks

        elif (
            "inactive relationship" in issue.lower()
            or "bidirectional" in issue.lower()
        ):

            relationship = find_relationship_evidence(
                object_name,
                metadata
            )

            if relationship:
                evidence = (
                    f"Relationship from "
                    f"{relationship.get('from')} to "
                    f"{relationship.get('to')}; "
                    f"cardinality={relationship.get('cardinality')}; "
                    f"active={relationship.get('active')}; "
                    f"cross_filter={relationship.get('cross_filter')}."
                )

            confidence = "High"

            business_impact = (
                "Relationship configuration affects how filters "
                "propagate between tables and can influence "
                "analytical results."
            )

            validation_status = (
                "Review the relationship design and intended "
                "filtering behaviour. This is not automatically "
                "a defect."
            )

        # Date table

        elif "date table" in issue.lower():

            detected_tables = find_date_tables(metadata)

            columns = tables.get(object_name, [])

            evidence = (
                f"The parser reports date_table_not_marked="
                f"{settings.get('date_table_not_marked')}. "
                f"Detected likely date tables: {detected_tables}. "
                f"Columns for this table: {columns}."
            )

            confidence = "Medium"

            business_impact = (
                "Incorrect date-table configuration can affect "
                "time intelligence calculations and date-based "
                "natural-language questions."
            )

            validation_status = (
                "Verify the intended date table and its "
                "date column configuration."
            )

        # Month sorting

        elif "month name" in issue.lower():

            evidence = (
                f"The parser reports month_not_sorted="
                f"{settings.get('month_not_sorted')}. "
                f"Detected field: {object_name}."
            )

            confidence = "Medium"

            business_impact = (
                "Month names sorted alphabetically instead of "
                "chronologically can produce misleading "
                "visualizations and time-based answers."
            )

            validation_status = (
                "Verify that the month-name field is sorted "
                "using its corresponding month-number field."
            )

    # -----------------------------------------------------
    # BUSINESS LOGIC FINDINGS
    # -----------------------------------------------------

    elif category == "Business Logic":

        glossary_definition = glossary.get(object_name)

        dax_expression = measures.get(object_name)

        # Glossary metric without exact measure-name match

        if "no clearly matching measure" in issue.lower():

            available_measures = ", ".join(
                measures.keys()
            ) or "No measures found"

            evidence = (
                f"Glossary term: {object_name}. "
                f"Definition: {glossary_definition or 'Not found'}. "
                f"Available measure names: {available_measures}. "
                "No exact measure-name match was identified."
            )

            confidence = "Medium"

            business_impact = (
                "Users may not have a clearly mapped calculation "
                "for an important business metric. An existing "
                "measure with a different name or synonym may "
                "still represent the same concept."
            )

            validation_status = (
                "Review glossary-to-measure mapping and decide "
                "whether an approved measure or synonym is needed."
            )

        # Definition conditions and qualifiers

        elif "includes conditions" in issue.lower():

            evidence = (
                f"Glossary definition: "
                f"{glossary_definition or 'Not found'}. "
                f"DAX expression: "
                f"{dax_expression or 'Not available'}."
            )

            confidence = "Medium"

            business_impact = (
                "If approved business conditions are not reflected "
                "in a calculation, natural-language answers may "
                "disagree with official business reporting."
            )

            validation_status = (
                "Compare the approved definition with the DAX "
                "expression and underlying source logic."
            )

        # Open population calculation

        elif "open-record condition" in issue.lower():

            evidence = (
                f"Glossary definition: "
                f"{glossary_definition or 'Not found'}. "
                f"DAX expression: "
                f"{dax_expression or 'Not available'}."
            )

            confidence = "Medium"

            business_impact = (
                "Including closed opportunities in an open-deals "
                "metric may produce an incorrect pipeline count."
            )

            validation_status = (
                "Validate that all closed stages are excluded. "
                "Check for upstream filters or indirect measure logic."
            )

        # Exited employee population

        elif "exited-employee population" in issue.lower():

            employee_tables = {
                name: columns
                for name, columns in tables.items()
                if "EMPLOYEE" in name.upper()
            }

            evidence = (
                f"Glossary definition: "
                f"{glossary_definition or 'Not found'}. "
                f"DAX expression: "
                f"{dax_expression or 'Not available'}. "
                f"Employee table columns: {employee_tables}. "
                "No obvious exit-status or termination field "
                "was identified by the available column names."
            )

            confidence = "Medium"

            business_impact = (
                "An incorrect exited-employee population can "
                "distort attrition reporting and workforce decisions."
            )

            validation_status = (
                "Confirm the approved exit definition and inspect "
                "upstream data transformations for exit logic."
            )

    # -----------------------------------------------------
    # SECURITY AND GOVERNANCE FINDINGS
    # -----------------------------------------------------

    elif category == "Security & Governance":

        if "sensitive" in issue.lower():

            evidence = (
                f"Detected sensitive field: {object_name}. "
                f"Scanner finding: {issue}. "
                f"Model-level all_columns_visible flag: "
                f"{settings.get('all_columns_visible')}. "
                "Individual column permissions, RLS, OLS and "
                "actual user access were not inspected."
            )

            confidence = "High"

            business_impact = (
                "Sensitive attributes could be exposed through "
                "natural-language analytics if access controls "
                "are not properly configured."
            )

            validation_status = (
                "Potential exposure. Review field visibility, "
                "RLS, OLS and approved user permissions."
            )

    # -----------------------------------------------------
    # FALLBACK CONTEXT
    # -----------------------------------------------------

    if not evidence:

        evidence = (
            f"Finding detected by the {category} scanner. "
            f"Original finding: {issue}"
        )

        if category == "Security & Governance":

            business_impact = (
                "Review the field and its access implications "
                "before exposing it to natural-language analytics."
            )

            validation_status = (
                "Security review required."
            )

        elif category == "Business Logic":

            business_impact = (
                "Unverified business logic may lead to "
                "inconsistent analytical answers."
            )

            validation_status = (
                "Business-owner validation required."
            )

        else:

            business_impact = (
                "Metadata quality can affect discoverability "
                "and interpretation of model objects."
            )

    return {
        "rule_id": get_rule_id(category, issue),
        "evidence": evidence,
        "confidence": confidence,
        "business_impact": business_impact,
        "validation_status": validation_status
    }


# ---------------------------------------------------------
# HELPER: Enrich the complete findings report
# ---------------------------------------------------------


def enrich_findings(report, metadata, glossary_path):

    glossary = read_glossary(glossary_path)

    # Initialize all enrichment columns as object dtype.
    # This allows text values to be stored safely.
    enrichment_columns = [
        "rule_id",
        "evidence",
        "confidence",
        "business_impact",
        "validation_status"
    ]

    for column in enrichment_columns:
        report[column] = pd.Series(
            index=report.index,
            dtype="object"
        )

    # Generate evidence and context for each finding.
    for index, row in report.iterrows():

        context = build_finding_context(
            row,
            metadata,
            glossary
        )

        for field, value in context.items():
            report.at[index, field] = value

    return report


# ---------------------------------------------------------
# MAIN: Scan one semantic model
# ---------------------------------------------------------

def scan_model(model_path, glossary_path):

    model_path = Path(model_path)
    glossary_path = Path(glossary_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}"
        )

    if not glossary_path.exists():
        raise FileNotFoundError(
            f"Glossary file not found: {glossary_path}"
        )

    # Step 1: Parse semantic model metadata

    metadata = parse_model(model_path)

    # Step 2: Run generic metadata checks

    generic_report = scan_generic(metadata)
    generic_report["category"] = "Metadata"

    # Step 3: Run business-context checks

    business_report = scan_business(
        metadata,
        glossary_path
    )
    business_report["category"] = "Business Logic"

    # Step 4: Run governance checks

    governance_report = scan_governance(metadata)
    governance_report["category"] = "Security & Governance"

    # Step 5: Combine all findings

    combined_report = pd.concat(
        [
            generic_report,
            business_report,
            governance_report
        ],
        ignore_index=True
    )

    # Step 6: Ensure consistent report structure

    combined_report = combined_report.reindex(
        columns=REPORT_COLUMNS
    )

    combined_report["model_name"] = metadata.get(
        "model_name",
        model_path.stem
    )

    # Step 7: Attach evidence, confidence and business impact

    combined_report = enrich_findings(
        combined_report,
        metadata,
        glossary_path
    )

    return combined_report


# ---------------------------------------------------------
# SUMMARY: Generate readiness summary
# ---------------------------------------------------------

def get_readiness_summary(report):

    if report.empty:
        return {
            "total_findings": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "categories": {}
        }

    severity_counts = (
        report["severity"]
        .value_counts()
        .to_dict()
    )

    category_counts = (
        report["category"]
        .value_counts()
        .to_dict()
    )

    return {
        "total_findings": len(report),
        "high": severity_counts.get("High", 0),
        "medium": severity_counts.get("Medium", 0),
        "low": severity_counts.get("Low", 0),
        "categories": category_counts
    }


# ---------------------------------------------------------
# EXPORT: Save consolidated report
# ---------------------------------------------------------

def save_report(report, output_path):

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report.to_csv(
        output_path,
        index=False
    )

    print(f"Report saved to: {output_path}")
