
# =========================================================
# CONFIGURATION
# =========================================================

CATEGORY_WEIGHTS = {
    "Metadata": 0.25,
    "Business Logic": 0.40,
    "Security & Governance": 0.35
}

SEVERITY_WEIGHTS = {
    "High": 5,
    "Medium": 2,
    "Low": 1
}

CONFIDENCE_FACTORS = {
    "High": 1.0,
    "Medium": 0.7,
    "Low": 0.4
}


# =========================================================
# HELPER: GENERATE EFFECTIVE RULE GROUPING KEYS
# =========================================================

def get_effective_rule_keys(report):
    """
    Use genuine rule IDs for grouping.

    Missing or GENERAL-REVIEW rule IDs receive an
    object-specific fallback key.

    This prevents unrelated findings from being collapsed
    into one generic rule group.
    """

    rule_ids = (
        report["rule_id"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fallback_mask = (
        rule_ids.eq("")
        | rule_ids.str.upper().eq("GENERAL-REVIEW")
    )

    # Construct a unique fallback from the finding identity.
    fallback_keys = (
        "UNMAPPED::"
        + report["category"]
            .fillna("Unknown")
            .astype(str)
        + "::"
        + report["model_name"]
            .fillna("Unknown")
            .astype(str)
        + "::"
        + report["object_type"]
            .fillna("Unknown")
            .astype(str)
        + "::"
        + report["object"]
            .fillna("Unknown")
            .astype(str)
        + "::"
        + report["issue"]
            .fillna("Unknown")
            .astype(str)
    )

    return rule_ids.where(
        ~fallback_mask,
        fallback_keys
    )


# =========================================================
# HELPER: CALCULATE CATEGORY RISK
# =========================================================

def calculate_category_risk(report, category):

    category_report = report[
        report["category"] == category
    ].copy()

    if category_report.empty:
        return 0.0

    # Convert severity into numeric risk points.
    severity_points = (
        category_report["severity"]
        .map(SEVERITY_WEIGHTS)
        .fillna(0)
    )

    # Apply confidence adjustment.
    confidence_factor = (
        category_report["confidence"]
        .map(CONFIDENCE_FACTORS)
        .fillna(0.4)
    )

    # Calculate risk for each individual finding.
    category_report["finding_risk"] = (
        severity_points / 5 * 100 * confidence_factor
    )

    # Generate effective rule IDs.
    category_report["rule_key"] = get_effective_rule_keys(
        category_report
    )

    # Group repeated findings under the same rule.
    # Keep the maximum risk within each group.
    rule_risks = (
        category_report
        .groupby("rule_key")["finding_risk"]
        .max()
    )

    if rule_risks.empty:
        return 0.0

    # Average risk across distinct rule groups.
    return round(
        float(rule_risks.mean()),
        2
    )


# =========================================================
# MAIN: CALCULATE READINESS SCORE
# =========================================================

def calculate_readiness_score(report):

    if report.empty:

        return {
            "readiness_score": None,
            "category_risks": {},
            "category_status": {},
            "category_details": {},
            "validation_queue": 0,
            "message": (
                "No findings were generated. "
                "Readiness cannot be independently assessed."
            )
        }

    category_risks = {}
    category_status = {}
    category_details = {}

    for category in CATEGORY_WEIGHTS:

        category_report = report[
            report["category"] == category
        ]

        # Calculate category risk.
        risk = calculate_category_risk(
            report,
            category
        )

        category_risks[category] = risk

        finding_count = len(category_report)

        # Count distinct effective rule groups.
        if category_report.empty:

            distinct_rules = 0

            category_status[category] = (
                "No matching findings detected. "
                "This is not proof of zero risk."
            )

        else:

            effective_rule_ids = get_effective_rule_keys(
                category_report
            )

            distinct_rules = effective_rule_ids.nunique()

            category_status[category] = (
                f"{finding_count} findings across "
                f"{distinct_rules} distinct rule groups."
            )

        # -------------------------------------------------
        # VALIDATION QUEUE
        # Retained as in the previous implementation.
        # Every finding with validation guidance is counted.
        # -------------------------------------------------

        validation_count = 0

        if "validation_status" in category_report.columns:

            validation_count = int(
                category_report["validation_status"]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

        # -------------------------------------------------
        # LOW CONFIDENCE FINDINGS
        # -------------------------------------------------

        low_confidence_count = 0

        if "confidence" in category_report.columns:

            low_confidence_count = int(
                category_report["confidence"]
                .eq("Low")
                .sum()
            )

        # -------------------------------------------------
        # CATEGORY DETAILS
        # -------------------------------------------------

        category_details[category] = {
            "finding_count": finding_count,
            "distinct_rules": int(distinct_rules),
            "validation_required": validation_count,
            "low_confidence_findings": low_confidence_count
        }

    # =====================================================
    # OVERALL WEIGHTED RISK
    # =====================================================

    total_risk = sum(
        category_risks[category] * CATEGORY_WEIGHTS[category]
        for category in CATEGORY_WEIGHTS
    )

    readiness_score = max(
        0,
        100 - total_risk
    )

    # =====================================================
    # TOTAL VALIDATION QUEUE
    # Retained for compatibility with existing dashboard.
    # =====================================================

    validation_queue = sum(
        details["validation_required"]
        for details in category_details.values()
    )

    return {
        "readiness_score": round(
            readiness_score,
            2
        ),
        "category_risks": category_risks,
        "category_status": category_status,
        "category_details": category_details,
        "validation_queue": int(validation_queue),
        "message": (
            "Preliminary confidence-adjusted, "
            "rule-grouped risk index. Requires "
            "validation and calibration."
        )
    }
