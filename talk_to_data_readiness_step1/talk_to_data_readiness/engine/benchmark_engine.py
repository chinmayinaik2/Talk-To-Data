
from pathlib import Path
import re

import pandas as pd

from engine.metadata_parser import parse_model


# =========================================================
# CONFIGURATION
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

BENCHMARK_FILE = (
    ROOT / "data" / "benchmark" / "benchmark_questions.csv"
)

MODEL_CONFIGS = {
    "Finance": (
        ROOT / "data" / "starter_kit" / "model"
        / "finance_model" / "model_definition.md"
    ),
    "Sales": (
        ROOT / "data" / "starter_kit" / "model"
        / "sales_model" / "model_definition.md"
    ),
    "HR": (
        ROOT / "data" / "starter_kit" / "model"
        / "hr_model" / "model_definition.md"
    )
}


BENCHMARK_COLUMNS = [
    "question_id",
    "model",
    "question",
    "metric",
    "initial_hypothesis",
    "computed_result",
    "measure_check",
    "table_check",
    "column_check",
    "filter_check",
    "relationship_check",
    "date_check",
    "assessment_reasons",
    "recommended_action"
]


# =========================================================
# HELPER 1: LOAD BENCHMARK QUESTIONS
# =========================================================

def load_benchmark_questions(path=None):

    path = Path(path or BENCHMARK_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Benchmark questions file not found: {path}"
        )

    df = pd.read_csv(
        path,
        sep=None,
        engine="python",
        dtype=str,
        keep_default_na=False
    )

    required_columns = [
        "question_id",
        "model",
        "question",
        "metric",
        "required_measures",
        "required_tables",
        "required_columns",
        "required_filters",
        "required_relationships",
        "initial_hypothesis",
        "reason"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Benchmark CSV is missing columns: {missing}"
        )

    if df["question_id"].duplicated().any():
        raise ValueError(
            "Duplicate benchmark question IDs were found."
        )

    return df


# =========================================================
# HELPER 2: SPLIT MULTIPLE REQUIREMENTS
# =========================================================

def split_requirements(value):

    if value is None:
        return []

    value = str(value).strip()

    if not value:
        return []

    return [
        item.strip()
        for item in value.split(";")
        if item.strip()
    ]


# =========================================================
# HELPER 3: NORMALIZE NAMES
# =========================================================

def normalize(value):

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


# =========================================================
# HELPER 4: CHECK REQUIRED TABLES
# =========================================================

def check_required_tables(required_tables, metadata):

    available_tables = metadata.get("tables", {})

    missing = [
        table
        for table in required_tables
        if table not in available_tables
    ]

    if missing:
        return {
            "status": "Missing",
            "missing": missing,
            "message": (
                "Required tables are missing: "
                + ", ".join(missing)
            )
        }

    return {
        "status": "Present",
        "missing": [],
        "message": "All required tables are present."
    }


# =========================================================
# HELPER 5: CHECK REQUIRED COLUMNS
# =========================================================

def check_required_columns(required_columns, metadata):

    available_tables = metadata.get("tables", {})

    missing = []

    for requirement in required_columns:

        if "." not in requirement:

            missing.append(requirement)
            continue

        table, column = requirement.split(".", 1)

        table_columns = available_tables.get(table)

        if table_columns is None:
            missing.append(requirement)
            continue

        normalized_columns = {
            normalize(existing)
            for existing in table_columns
        }

        if normalize(column) not in normalized_columns:
            missing.append(requirement)

    if missing:
        return {
            "status": "Missing",
            "missing": missing,
            "message": (
                "Required columns are missing: "
                + ", ".join(missing)
            )
        }

    return {
        "status": "Present",
        "missing": [],
        "message": "All required columns are present."
    }


# =========================================================
# HELPER 6: CHECK REQUIRED MEASURES
# =========================================================

def check_required_measures(required_measures, metadata):

    available_measures = metadata.get("measures", {})

    normalized_measures = {
        normalize(name): name
        for name in available_measures
    }

    missing = []
    matched = []

    for measure in required_measures:

        normalized_name = normalize(measure)

        if normalized_name in normalized_measures:

            matched.append(
                normalized_measures[normalized_name]
            )

        else:
            missing.append(measure)

    if missing:
        return {
            "status": "Missing",
            "missing": missing,
            "matched": matched,
            "message": (
                "Required measures are not defined: "
                + ", ".join(missing)
            )
        }

    if not required_measures:
        return {
            "status": "Not specified",
            "missing": [],
            "matched": [],
            "message": (
                "No specific existing DAX measure was "
                "specified for this question."
            )
        }

    return {
        "status": "Present",
        "missing": [],
        "matched": matched,
        "message": "All specified measures are present."
    }


# =========================================================
# HELPER 7: CHECK FILTERS AGAINST DAX
# =========================================================

def check_filter_in_expression(filter_requirement, expression):

    """
    Supported requirement examples:

    F_TRX.STS_CD=C
    F_TRX.STS_CD!=X
    F_OPPORTUNITY.STAGE_CD IN Q|P|N
    """

    match = re.match(
        r"^\s*([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)"
        r"\s*(IN|!=|<>|=)\s*(.*?)\s*$",
        filter_requirement,
        re.IGNORECASE
    )

    if not match:
        return None

    table, column, operator, expected = match.groups()

    # Find the field in the DAX expression.
    field_pattern = (
        rf"{re.escape(table)}\s*"
        rf"\[\s*{re.escape(column)}\s*\]"
    )

    field_match = re.search(
        field_pattern,
        expression,
        re.IGNORECASE
    )

    if not field_match:
        return False

    # Inspect the expression following the field reference.
    tail = expression[field_match.end():field_match.end() + 250]

    expected_values = [
        value.strip().strip("\"'")
        for value in expected.split("|")
        if value.strip()
    ]

    operator = operator.upper()

    if operator == "IN":

        if not re.search(
            r"\bIN\b",
            tail,
            re.IGNORECASE
        ):
            return False

        return all(
            re.search(
                rf"['\"]{re.escape(value)}['\"]",
                tail,
                re.IGNORECASE
            )
            for value in expected_values
        )

    if len(expected_values) != 1:
        return False

    value = re.escape(expected_values[0])

    if operator == "=":

        return bool(
            re.search(
                rf"^\s*=\s*['\"]?{value}['\"]?",
                tail,
                re.IGNORECASE
            )
        )

    if operator in {"!=", "<>"}:

        return bool(
            re.search(
                rf"^\s*(?:!=|<>)\s*['\"]?{value}['\"]?",
                tail,
                re.IGNORECASE
            )
        )

    return False


def check_required_filters(
    required_filters,
    required_measures,
    metadata
):

    if not required_filters:
        return {
            "status": "Not required",
            "message": "No explicit filter requirement."
        }

    measures = metadata.get("measures", {})

    if not required_measures:
        return {
            "status": "Needs validation",
            "message": (
                "Filter requirements exist, but no specific DAX "
                "measure was supplied for direct inspection."
            )
        }

    expressions = []

    for measure in required_measures:

        for name, expression in measures.items():

            if normalize(name) == normalize(measure):
                expressions.append(str(expression))

    if not expressions:
        return {
            "status": "Needs validation",
            "message": (
                "Could not retrieve the specified DAX expressions "
                "for filter validation."
            )
        }

    results = []

    for filter_requirement in required_filters:

        checks = [
            check_filter_in_expression(
                filter_requirement,
                expression
            )
            for expression in expressions
        ]

        # None means the requirement could not be parsed.
        if all(result is None for result in checks):
            results.append("Not assessable")

        elif any(result is True for result in checks):
            results.append("Present")

        else:
            results.append("Not visible in DAX")

    if all(result == "Present" for result in results):
        return {
            "status": "Present",
            "message": (
                "All specified filter conditions are visible "
                "in the required DAX measures."
            )
        }

    return {
        "status": "Needs validation",
        "message": (
            "One or more required filters were not verified "
            "in the listed DAX measures. Check upstream "
            "transformations and indirect calculation logic."
        )
    }


# =========================================================
# HELPER 8: CHECK RELATIONSHIPS
# =========================================================

def check_required_relationships(
    required_relationships,
    metadata
):

    if not required_relationships:
        return {
            "status": "Not required",
            "message": "No explicit relationship requirement."
        }

    available_relationships = metadata.get(
        "relationships",
        []
    )

    reviews = []
    missing = []

    for requirement in required_relationships:

        # Free-text dependencies require manual inspection.
        if "->" not in requirement:

            if re.search(
                r"exit|terminat",
                requirement,
                re.IGNORECASE
            ):

                employee_columns = []

                for table, columns in metadata.get("tables", {}).items():

                    if "EMPLOYEE" in table.upper():
                        employee_columns.extend(
                            str(column).upper()
                            for column in columns
                        )

                exit_fields = [
                    column
                    for column in employee_columns
                    if (
                        "EXIT" in column
                        or "TERMINAT" in column
                        or "DEPARTURE" in column
                    )
                ]

                if not exit_fields:
                    missing.append(
                        "Employee exit/termination field"
                    )
                else:
                    reviews.append(
                        "Employee exit-date relationship needs review."
                    )

            else:
                reviews.append(
                    f"Manual relationship validation required: {requirement}"
                )

            continue

        source, target = requirement.split("->", 1)

        source = normalize(source)
        target = normalize(target.strip())

        matched_relationship = None

        for relationship in available_relationships:

            actual_source = normalize(
                relationship.get("from", "")
            )

            actual_target = normalize(
                relationship.get("to", "")
            )

            if (
                actual_source == source
                and actual_target == target
            ):
                matched_relationship = relationship
                break

        if matched_relationship is None:

            missing.append(requirement)
            continue

        active = str(
            matched_relationship.get("active", "")
        ).strip().lower()

        cross_filter = str(
            matched_relationship.get("cross_filter", "")
        ).strip().lower()

        if active in {"no", "false", "inactive", "0"}:

            reviews.append(
                f"Required relationship is inactive: {requirement}"
            )

        if cross_filter == "both":

            reviews.append(
                f"Bidirectional relationship requires review: {requirement}"
            )

    if missing:

        return {
            "status": "Missing",
            "missing": missing,
            "message": (
                "Required relationship dependencies are missing: "
                + "; ".join(missing)
            )
        }

    if reviews:

        return {
            "status": "Needs validation",
            "message": "; ".join(reviews)
        }

    return {
        "status": "Present",
        "message": "All specified relationships are present and active."
    }


# =========================================================
# HELPER 9: CHECK DATE CONFIGURATION
# =========================================================

def check_date_configuration(question_row, metadata):

    question_text = (
        str(question_row.get("question", ""))
        + " "
        + str(question_row.get("required_columns", ""))
    ).lower()

    date_terms = [
        "month",
        "quarter",
        "year",
        "last quarter",
        "by month",
        "by quarter"
    ]

    depends_on_dates = any(
        term in question_text
        for term in date_terms
    )

    if not depends_on_dates:

        return {
            "status": "Not required",
            "message": "No explicit date requirement."
        }

    settings = metadata.get("settings", {})

    problems = []

    if settings.get("date_table_not_marked", False):
        problems.append(
            "Likely date table is not marked as a date table."
        )

    if settings.get("month_not_sorted", False):

        if "month" in question_text:
            problems.append(
                "Month-name sorting requires validation."
            )

    if problems:

        return {
            "status": "Needs validation",
            "message": " ".join(problems)
        }

    return {
        "status": "Present",
        "message": (
            "No date configuration issue was identified "
            "by the available parser flags."
        )
    }


# =========================================================
# HELPER 10: EVALUATE ONE QUESTION
# =========================================================

def evaluate_question(question_row, metadata):

    model = question_row["model"]

    required_tables = split_requirements(
        question_row["required_tables"]
    )

    required_columns = split_requirements(
        question_row["required_columns"]
    )

    required_measures = split_requirements(
        question_row["required_measures"]
    )

    required_filters = split_requirements(
        question_row["required_filters"]
    )

    required_relationships = split_requirements(
        question_row["required_relationships"]
    )

    measure_result = check_required_measures(
        required_measures,
        metadata
    )

    table_result = check_required_tables(
        required_tables,
        metadata
    )

    column_result = check_required_columns(
        required_columns,
        metadata
    )

    filter_result = check_required_filters(
        required_filters,
        required_measures,
        metadata
    )

    relationship_result = check_required_relationships(
        required_relationships,
        metadata
    )

    date_result = check_date_configuration(
        question_row,
        metadata
    )

    blockers = []
    reviews = []

    # Missing structural dependencies are concrete gaps.
    if measure_result["status"] == "Missing":
        blockers.append(measure_result["message"])

    if table_result["status"] == "Missing":
        blockers.append(table_result["message"])

    if column_result["status"] == "Missing":
        blockers.append(column_result["message"])

    if relationship_result["status"] == "Missing":
        blockers.append(relationship_result["message"])

    # Conditions requiring human or deeper source validation.
    for result in [
        filter_result,
        relationship_result,
        date_result
    ]:

        if result["status"] == "Needs validation":
            reviews.append(result["message"])

    if blockers:

        computed_result = "Gap detected"

        reasons = blockers + reviews

        recommended_action = (
            "Add or correct the missing semantic-model "
            "dependency, then validate the business definition."
        )

    elif reviews:

        computed_result = "Needs validation"

        reasons = reviews

        recommended_action = (
            "Ask the relevant data owner to validate the "
            "calculation, relationship or source logic."
        )

    else:

        computed_result = "Likely supported"

        reasons = [
            "The specified measures, tables, columns and "
            "structural dependencies were found."
        ]

        recommended_action = (
            "Run an actual natural-language query test "
            "to verify the returned result."
        )

    if measure_result["status"] == "Not specified":

        reasons.append(
            "No explicit DAX measure requirement was provided. "
            "A business metric may still require an approved "
            "calculation."
        )

        if computed_result == "Likely supported":

            computed_result = "Needs validation"

            recommended_action = (
                "Confirm whether an approved reusable measure "
                "or business calculation is required."
            )

    return {
        "question_id": question_row["question_id"],
        "model": model,
        "question": question_row["question"],
        "metric": question_row["metric"],
        "initial_hypothesis": question_row["initial_hypothesis"],
        "computed_result": computed_result,

        "measure_check": measure_result["status"],
        "table_check": table_result["status"],
        "column_check": column_result["status"],
        "filter_check": filter_result["status"],
        "relationship_check": relationship_result["status"],
        "date_check": date_result["status"],

        "assessment_reasons": " ".join(reasons),
        "recommended_action": recommended_action
    }


# =========================================================
# MAIN: EVALUATE ONE MODEL
# =========================================================

def evaluate_model_benchmark(
    model_name,
    questions_path=None,
    model_path=None
):

    questions = load_benchmark_questions()

    model_questions = questions[
        questions["model"].str.lower()
        == model_name.lower()
    ]

    if model_questions.empty:

        raise ValueError(
            f"No benchmark questions found for {model_name}."
        )

    if model_path is None:

        if model_name not in MODEL_CONFIGS:

            raise ValueError(
                f"Unknown model: {model_name}"
            )

        model_path = MODEL_CONFIGS[model_name]

    model_path = Path(model_path)

    if not model_path.exists():

        raise FileNotFoundError(
            f"Model definition not found: {model_path}"
        )

    metadata = parse_model(model_path)

    results = []

    for _, row in model_questions.iterrows():

        result = evaluate_question(
            row.to_dict(),
            metadata
        )

        results.append(result)

    return pd.DataFrame(
        results,
        columns=BENCHMARK_COLUMNS
    )


# =========================================================
# MAIN: EVALUATE ALL THREE MODELS
# =========================================================

def evaluate_all_benchmarks():

    results = []

    for model_name in MODEL_CONFIGS:

        model_result = evaluate_model_benchmark(
            model_name
        )

        results.append(model_result)

    if not results:
        return pd.DataFrame(columns=BENCHMARK_COLUMNS)

    return pd.concat(
        results,
        ignore_index=True
    )


# =========================================================
# SUMMARY: BENCHMARK RESULTS
# =========================================================

def get_benchmark_summary(report):

    if report.empty:

        return {
            "total_questions": 0,
            "likely_supported": 0,
            "needs_validation": 0,
            "gaps_detected": 0
        }

    counts = report["computed_result"].value_counts()

    return {
        "total_questions": len(report),

        "likely_supported": counts.get(
            "Likely supported",
            0
        ),

        "needs_validation": counts.get(
            "Needs validation",
            0
        ),

        "gaps_detected": counts.get(
            "Gap detected",
            0
        )
    }


# =========================================================
# EXPORT: SAVE BENCHMARK RESULTS
# =========================================================

def save_benchmark_report(report, output_path):

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report.to_csv(
        output_path,
        index=False
    )

    print(
        f"Benchmark report saved to: {output_path}"
    )
