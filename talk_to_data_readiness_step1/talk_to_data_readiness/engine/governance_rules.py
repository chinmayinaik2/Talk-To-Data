
import re
import pandas as pd

from engine.generic_rules import REPORT_COLUMNS


# Sensitive field patterns and their classifications.
SENSITIVE_PATTERNS = {
    "Compensation": [
        "salary",
        "annual_comp",
        "compensation",
        "pay",
        "bonus",
        "wage"
    ],
    "Personally Identifiable Information": [
        "email",
        "phone",
        "mobile",
        "personal_address",
        "date_of_birth",
        "dob"
    ],
    "Financial Information": [
        "bank_account",
        "account_number",
        "card_number",
        "tax_id"
    ],
    "Identity Information": [
        "ssn",
        "social_security",
        "national_id",
        "passport"
    ]
}


def normalize_name(value):
    """Normalize field names for pattern matching."""
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def classify_sensitive_field(column_name):
    """Return the sensitivity category for a matching field."""
    normalized = normalize_name(column_name)

    for category, patterns in SENSITIVE_PATTERNS.items():
        for pattern in patterns:
            if pattern in normalized:
                return category

    return None


def scan_sensitive_fields(metadata):
    """
    Identify sensitive columns and assess potential exposure.

    Note:
    all_columns_visible is a model-level parser flag.
    It does not establish whether every field is accessible to
    every user or whether row-level security is configured.
    """
    findings = []

    tables = metadata.get("tables", {})
    settings = metadata.get("settings", {})

    all_columns_visible = settings.get(
        "all_columns_visible",
        False
    )

    for table_name, columns in tables.items():
        for column_name in columns:

            category = classify_sensitive_field(column_name)

            if category is None:
                continue

            if all_columns_visible:
                issue = (
                    f"Sensitive {category.lower()} field detected. "
                    "The model-level metadata indicates that all columns "
                    "are visible. Review whether this field should be "
                    "exposed to natural-language analytics."
                )

                severity = "High"

            else:
                issue = (
                    f"Sensitive {category.lower()} field detected. "
                    "Review column visibility, permissions and "
                    "natural-language query access."
                )

                severity = "Medium"

            findings.append({
                "object": f"{table_name}[{column_name}]",
                "object_type": "Sensitive Column",
                "issue": issue,
                "severity": severity,
                "fix": (
                    "Review business necessity, object-level security, "
                    "row-level security and approved user access. "
                    "Restrict sensitive attributes from unauthorized "
                    "natural-language queries."
                )
            })

    return findings


def scan_governance(metadata):
    """Run governance checks for one semantic model."""
    findings = []

    findings.extend(
        scan_sensitive_fields(metadata)
    )

    report = pd.DataFrame(
        findings,
        columns=REPORT_COLUMNS
    )

    report.attrs["model_name"] = metadata.get(
        "model_name",
        "Unknown Model"
    )

    return report
