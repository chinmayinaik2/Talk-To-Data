
import re
from pathlib import Path

import pandas as pd

from engine.generic_rules import add_issue, REPORT_COLUMNS


def normalize(text):
    """Normalize text for matching."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()



def parse_glossary(glossary_path):
    """Extract business terms and definitions from a Markdown glossary."""
    glossary_path = Path(glossary_path)

    if not glossary_path.exists():
        raise FileNotFoundError(f"Glossary not found: {glossary_path}")

    content = glossary_path.read_text(encoding="utf-8")

    terms = []

    # Supports: - **Metric Name:** Definition
    pattern = r"[-*]\s*\*\*(.+?):\*\*\s*(.+)"

    for match in re.finditer(pattern, content):
        term = match.group(1).strip()
        definition = match.group(2).strip()

        terms.append({
            "term": term,
            "definition": definition
        })

    return terms


def match_measure(term, measures):
    """Match a glossary term to a measure without loose substring matches."""

    normalized_term = normalize(term)

    # First preference: exact match
    for measure_name in measures:
        if normalize(measure_name) == normalized_term:
            return measure_name

    # Second preference: token-equivalent match
    term_tokens = set(normalized_term.split())

    for measure_name in measures:
        measure_tokens = set(normalize(measure_name).split())

        if term_tokens == measure_tokens:
            return measure_name

    # No reliable match found
    return None


def check_glossary_coverage(metadata, glossary_path):
    """Check whether glossary metrics have corresponding model measures."""
    findings = []
    measures = metadata.get("measures", {})

    glossary_terms = parse_glossary(glossary_path)

    for item in glossary_terms:
        term = item["term"]

        # Only check terms that appear to describe measurable metrics.
        metric_words = (
            "rate", "count", "revenue", "sales", "margin",
            "profit", "average", "total", "hours", "pipeline",
            "employees", "deals", "orders", "discount",
            "attrition", "time to hire"
        )

        if not any(word in normalize(term).split() for word in metric_words):
            continue

        matched_measure = match_measure(term, measures)

        if matched_measure is None:
            findings.append({
                "object": term,
                "object_type": "Business Metric",
                "issue": (
                    "Business glossary metric has no clearly matching "
                    "measure. Natural-language queries may not have a "
                    "dedicated calculation."
                ),
                "severity": "Medium",
                "fix": (
                    "Review whether this metric needs a dedicated DAX "
                    "measure and document its approved calculation."
                )
            })

    return findings


def check_qualified_definitions(metadata, glossary_path):
    """
    Flag measures where a glossary definition includes important
    business conditions that cannot be verified from the DAX expression.
    """
    findings = []
    measures = metadata.get("measures", {})

    glossary_terms = parse_glossary(glossary_path)

    qualifiers = (
        "excluding",
        "only",
        "completed",
        "cancelled",
        "returned",
        "approved",
        "active",
        "exited",
        "probability",
        "weighted",
        "per employee",
        "per order"
    )

    for item in glossary_terms:
        term = item["term"]
        definition = item["definition"]
        measure_name = match_measure(term, measures)

        if not measure_name:
            continue

        definition_text = normalize(definition)
        expression = normalize(measures[measure_name])

        relevant_qualifiers = [
            word for word in qualifiers
            if word in definition_text
        ]

        if not relevant_qualifiers:
            continue

        # This is a review flag, not proof that the measure is incorrect.
        findings.append({
            "object": measure_name,
            "object_type": "Measure",
            "issue": (
                f"Business definition includes conditions "
                f"({', '.join(relevant_qualifiers)}) that should be "
                "validated against the DAX calculation. The available "
                "metadata may not be sufficient to verify them."
            ),
            "severity": "Medium",
            "fix": (
                "Compare the approved business definition with the DAX "
                "expression and underlying column logic. Confirm that all "
                "required filters and conditions are implemented."
            )
        })

    return findings


def check_open_population_measure(metadata, glossary_path):
    """
    Check whether a measure defined around open/in-progress records
    visibly accounts for the closed statuses in its DAX expression.
    """
    findings = []
    measures = metadata.get("measures", {})

    for item in parse_glossary(glossary_path):
        term = normalize(item["term"])
        definition = normalize(item["definition"])

        # Look for glossary definitions describing an open population.
        describes_open_population = (
            "open" in term.split()
            and any(word in definition for word in [
                "not been marked won or lost",
                "not won or lost",
                "open opportunities",
                "open deals"
            ])
        )

        if not describes_open_population:
            continue

        measure_name = match_measure(item["term"], measures)

        if not measure_name:
            continue

        expression = normalize(measures[measure_name])

        # Look for evidence that the DAX uses a stage/status condition.
        has_stage_reference = any(
            token in expression.split()
            for token in ["stage", "stage cd", "status", "status cd"]
        )

        if not has_stage_reference:
            findings.append({
                "object": measure_name,
                "object_type": "Measure",
                "issue": (
                    "The glossary defines this metric using an open-record "
                    "condition, but the DAX expression does not visibly "
                    "reference a stage or status field. Closed records may "
                    "be included."
                ),
                "severity": "High",
                "fix": (
                    "Validate that the measure excludes all closed statuses "
                    "according to the business glossary. Check whether the "
                    "filter is implemented upstream or through another measure."
                )
            })

    return findings


def check_exit_population_fields(metadata, glossary_path):
    """
    Check whether the model has fields that could identify exited
    employees when the glossary defines an exited-employee metric.
    """
    findings = []
    measures = metadata.get("measures", {})
    tables = metadata.get("tables", {})

    exit_keywords = [
        "exit",
        "termination",
        "terminated",
        "end date",
        "employment status",
        "separation"
    ]

    for item in parse_glossary(glossary_path):
        term = normalize(item["term"])
        definition = normalize(item["definition"])

        describes_exited_population = (
            "exited" in term.split()
            or "left the organization" in definition
            or "left organization" in definition
        )

        if not describes_exited_population:
            continue

        measure_name = match_measure(item["term"], measures)

        if not measure_name:
            continue

        # Search employee-related tables for a possible exit indicator.
        employee_columns = []

        for table_name, columns in tables.items():
            if "employee" in normalize(table_name):
                employee_columns.extend(columns)

        has_exit_field = any(
            any(keyword in normalize(column) for keyword in exit_keywords)
            for column in employee_columns
        )

        if not has_exit_field:
            findings.append({
                "object": measure_name,
                "object_type": "Measure",
                "issue": (
                    "The glossary defines an exited-employee population, "
                    "but no obvious employee exit-status or termination "
                    "field was found in the available model metadata. "
                    "The calculation cannot be fully validated."
                ),
                "severity": "High",
                "fix": (
                    "Confirm the approved exit definition and reporting "
                    "period. Identify the source field or upstream logic "
                    "that determines whether an employee has exited."
                )
            })

    return findings


def scan_business(metadata, glossary_path):
    """Run all business-context checks for one semantic model."""
    findings = []

    findings.extend(
        check_glossary_coverage(metadata, glossary_path)
    )

    findings.extend(
        check_qualified_definitions(metadata, glossary_path)
    )

    findings.extend(
        check_open_population_measure(metadata, glossary_path)
    )

    findings.extend(
        check_exit_population_fields(metadata, glossary_path)
    )

    report = pd.DataFrame(findings, columns=REPORT_COLUMNS)
    report.attrs["model_name"] = metadata.get("model_name", "Unknown Model")

    return report
