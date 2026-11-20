from pathlib import Path
import subprocess
import sys

import pandas as pd
import streamlit as st

from engine.readiness_engine import scan_model, save_report
from engine.scoring import calculate_readiness_score

from engine.ai_enrichment import (
    MAX_FINDINGS_PER_REQUEST,
    prepare_safe_payload,
    enrich_findings_with_gemini
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Talk-to-Data Readiness Analyzer",
    page_icon="🧭",
    layout="wide"
)

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
BENCHMARK_REPORT_PATH = REPORTS_DIR / "benchmark_results.csv"


# =========================================================
# MODEL CONFIGURATION
# =========================================================

MODEL_CONFIGS = {
    "Finance": {
        "model": (
            ROOT / "data" / "starter_kit" / "model"
            / "finance_model" / "model_definition.md"
        ),
        "glossary": (
            ROOT / "data" / "starter_kit" / "model"
            / "finance_model" / "business_glossary.md"
        ),
        "report": REPORTS_DIR / "finance_readiness_report.csv"
    },

    "Sales": {
        "model": (
            ROOT / "data" / "starter_kit" / "model"
            / "sales_model" / "model_definition.md"
        ),
        "glossary": (
            ROOT / "data" / "starter_kit" / "model"
            / "sales_model" / "business_glossary.md"
        ),
        "report": REPORTS_DIR / "sales_readiness_report.csv"
    },

    "HR": {
        "model": (
            ROOT / "data" / "starter_kit" / "model"
            / "hr_model" / "model_definition.md"
        ),
        "glossary": (
            ROOT / "data" / "starter_kit" / "model"
            / "hr_model" / "business_glossary.md"
        ),
        "report": REPORTS_DIR / "hr_readiness_report.csv"
    }
}


REQUIRED_COLUMNS = [
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


CATEGORIES = [
    "Metadata",
    "Business Logic",
    "Security & Governance"
]


# =========================================================
# SCAN ALL MODELS
# =========================================================

def scan_all_models():

    reports = {}

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for model_name, config in MODEL_CONFIGS.items():

        if not config["model"].exists():
            raise FileNotFoundError(
                f"{model_name} model file not found: "
                f"{config['model']}"
            )

        if not config["glossary"].exists():
            raise FileNotFoundError(
                f"{model_name} glossary not found: "
                f"{config['glossary']}"
            )

        report = scan_model(
            config["model"],
            config["glossary"]
        )

        save_report(
            report,
            config["report"]
        )

        reports[model_name] = report

    return reports


# =========================================================
# LOAD EXISTING REPORTS
# =========================================================

def load_existing_reports():

    reports = {}

    for model_name, config in MODEL_CONFIGS.items():

        report_path = config["report"]

        if not report_path.exists():
            return None

        report = pd.read_csv(report_path)

        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in report.columns
        ]

        if missing_columns:
            return None

        reports[model_name] = report

    return reports


# =========================================================
# COMBINE FINDINGS
# =========================================================

def get_all_findings(reports):

    all_reports = []

    for model_name, report in reports.items():

        model_report = report.copy()
        model_report["Model"] = model_name

        all_reports.append(model_report)

    if not all_reports:
        return pd.DataFrame()

    return pd.concat(
        all_reports,
        ignore_index=True
    )


# =========================================================
# INITIALIZE REPORTS
# =========================================================

if "reports" not in st.session_state:

    try:

        with st.spinner(
            "Loading semantic model reports..."
        ):

            existing_reports = load_existing_reports()

            if existing_reports is not None:

                st.session_state.reports = existing_reports
                st.session_state.report_source = "Saved reports"

            else:

                st.session_state.reports = scan_all_models()
                st.session_state.report_source = "Fresh scan"

    except Exception as error:

        st.error(
            f"Unable to load reports: {error}"
        )

        st.stop()


reports = st.session_state.reports

combined = get_all_findings(reports)

scores = {
    model_name: calculate_readiness_score(report)
    for model_name, report in reports.items()
}


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🧭 Talk-to-Data")

    st.caption("Multi-Model Readiness Analyzer")

    st.divider()

    st.markdown("### Workspace")

    st.write(f"Models loaded: **{len(reports)}**")

    st.write(f"Total findings: **{len(combined)}**")

    st.caption(
        f"Data source: {st.session_state.report_source}"
    )

    st.divider()

    if st.button(
        "🔄 Run Full Scan",
        use_container_width=True
    ):

        try:

            with st.spinner(
                "Scanning Finance, Sales and HR models..."
            ):

                st.session_state.reports = scan_all_models()

                st.session_state.report_source = "Fresh scan"

                # Old AI suggestions belong to previous report data.
                st.session_state.pop("ai_results", None)

            st.success("All model scans completed.")

            st.rerun()

        except Exception as error:

            st.error(
                f"Scan failed: {error}"
            )

    st.divider()

    st.caption(
        "Make your data AI-ready before making it AI-powered."
    )


# =========================================================
# RELOAD CURRENT REPORT REFERENCES
# =========================================================

reports = st.session_state.reports

combined = get_all_findings(reports)

scores = {
    model_name: calculate_readiness_score(report)
    for model_name, report in reports.items()
}


# =========================================================
# HEADER
# =========================================================

st.title("Talk-to-Data Readiness Analyzer")

st.markdown(
    "Evaluate whether semantic models are prepared for "
    "accurate, understandable and governed natural-language analytics."
)

st.caption(
    "Current prototype supports Finance, Sales and HR semantic models."
)

st.divider()


# =========================================================
# DASHBOARD TABS
# =========================================================

(
    overview_tab,
    model_tab,
    findings_tab,
    validation_tab,
    ai_tab,
    benchmark_tab
) = st.tabs([
    "   Overview",
    "   Model Analysis",
    "   Findings Explorer",
    "   Validation Backlog",
    "   AI Enrichment",
    "   Question Benchmark"
])


# =========================================================
# TAB 1: OVERVIEW
# =========================================================

with overview_tab:

    st.subheader("Portfolio Overview")

    total_findings = len(combined)

    high_count = int(
        (combined["severity"] == "High").sum()
    )

    average_score = (
        round(
            sum(
                result["readiness_score"]
                for result in scores.values()
            ) / len(scores),
            2
        )
        if scores else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Models Scanned",
        len(reports)
    )

    col2.metric(
        "Total Findings",
        total_findings
    )

    col3.metric(
        "High Severity",
        high_count
    )

    col4.metric(
        "Average Readiness Index",
        f"{average_score:.2f}"
    )

    st.caption(
        "Readiness index is a preliminary, confidence-adjusted "
        "and rule-grouped risk index. It is not a certified "
        "probability of AI answer accuracy."
    )

    st.divider()

    # Model comparison

    st.subheader("Model Readiness Comparison")

    comparison_data = []

    for model_name, result in scores.items():

        comparison_data.append({
            "Model": model_name,
            "Readiness Index": result["readiness_score"],
            "Total Findings": len(reports[model_name]),
            "High Findings": int(
                (
                    reports[model_name]["severity"] == "High"
                ).sum()
            )
        })

    comparison_df = pd.DataFrame(
        comparison_data
    )

    left, right = st.columns([1.5, 1])

    with left:

        st.markdown("**Readiness index by model**")

        chart_df = comparison_df.set_index("Model")[
            ["Readiness Index"]
        ]

        st.bar_chart(chart_df)

    with right:

        st.markdown("**Model summary**")

        st.dataframe(
            comparison_df,
            hide_index=True,
            use_container_width=True
        )

    st.divider()

    # Category risk

    st.subheader("Risk by Category")

    risk_data = []

    for model_name, result in scores.items():

        row = {
            "Model": model_name
        }

        for category in CATEGORIES:

            row[category] = result[
                "category_risks"
            ].get(category, 0)

        risk_data.append(row)

    risk_df = pd.DataFrame(
        risk_data
    ).set_index("Model")

    st.bar_chart(risk_df)

    st.caption(
        "Category risk represents prototype risk intensity. "
        "Zero means no matching findings were detected, "
        "not that the category is verified safe."
    )

    st.divider()

    # Severity distribution

    st.subheader("Finding Severity Distribution")

    severity_counts = (
        combined["severity"]
        .value_counts()
        .reindex(
            ["High", "Medium", "Low"],
            fill_value=0
        )
    )

    severity_df = pd.DataFrame({
        "Severity": severity_counts.index,
        "Findings": severity_counts.values
    }).set_index("Severity")

    st.bar_chart(severity_df)


# =========================================================
# TAB 2: MODEL ANALYSIS
# =========================================================

with model_tab:

    st.subheader("Individual Model Analysis")

    selected_model = st.selectbox(
        "Select semantic model",
        list(reports.keys()),
        key="analysis_model"
    )

    model_report = reports[selected_model]

    model_score = scores[selected_model]

    st.divider()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Readiness Index",
        f"{model_score['readiness_score']:.2f}"
    )

    c2.metric(
        "Total Findings",
        len(model_report)
    )

    c3.metric(
        "High Severity",
        int(
            (model_report["severity"] == "High").sum()
        )
    )

    st.divider()

    st.markdown("### Category Risk Breakdown")

    category_rows = []

    for category in CATEGORIES:

        details = model_score[
            "category_details"
        ][category]

        category_rows.append({
            "Category": category,
            "Risk Intensity": model_score[
                "category_risks"
            ][category],
            "Findings": details["finding_count"],
            "Distinct Rules": details["distinct_rules"],
            "Low Confidence": details["low_confidence_findings"]
        })

    category_df = pd.DataFrame(
        category_rows
    )

    left, right = st.columns([1.1, 1])

    with left:

        st.dataframe(
            category_df,
            hide_index=True,
            use_container_width=True
        )

    with right:

        st.bar_chart(
            category_df.set_index("Category")[
                ["Risk Intensity"]
            ]
        )

    st.divider()

    st.markdown("### Category Review Status")

    for category in CATEGORIES:

        with st.expander(category):

            st.write(
                model_score["category_status"][category]
            )

            details = model_score[
                "category_details"
            ][category]

            st.write(
                f"Findings requiring review: "
                f"{details['validation_required']}"
            )

            st.write(
                f"Low-confidence findings: "
                f"{details['low_confidence_findings']}"
            )

    st.divider()

    st.markdown("### Download Model Report")

    model_csv = model_report.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label=f"Download {selected_model} Report",
        data=model_csv,
        file_name=(
            f"{selected_model.lower()}_readiness_report.csv"
        ),
        mime="text/csv"
    )


    # TAB 3: FINDINGS EXPLORER
# =========================================================

with findings_tab:

    st.subheader("Explore Detected Findings")

    st.caption(
        "Filter findings, inspect their evidence and understand "
        "their business implications."
    )

    filter1, filter2, filter3 = st.columns(3)

    with filter1:

        selected_models = st.multiselect(
            "Model",
            list(reports.keys()),
            default=list(reports.keys()),
            key="findings_models"
        )

    with filter2:

        selected_categories = st.multiselect(
            "Category",
            CATEGORIES,
            default=CATEGORIES,
            key="findings_categories"
        )

    with filter3:

        selected_severities = st.multiselect(
            "Severity",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
            key="findings_severities"
        )

    filter4, filter5 = st.columns(2)

    with filter4:

        selected_confidence = st.multiselect(
            "Confidence",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
            key="findings_confidence"
        )

    with filter5:

        search_text = st.text_input(
            "Search object, issue or rule ID",
            placeholder="Example: SALARY, Open Deals...",
            key="findings_search"
        )

    filtered = combined[
        combined["Model"].isin(selected_models)
        & combined["category"].isin(selected_categories)
        & combined["severity"].isin(selected_severities)
        & combined["confidence"].isin(selected_confidence)
    ].copy()

    if search_text.strip():

        search_columns = [
            "object",
            "issue",
            "rule_id",
            "category",
            "business_impact"
        ]

        search_mask = pd.Series(
            False,
            index=filtered.index
        )

        for column in search_columns:

            search_mask = search_mask | (
                filtered[column]
                .fillna("")
                .astype(str)
                .str.contains(
                    search_text,
                    case=False,
                    regex=False
                )
            )

        filtered = filtered[search_mask]

    st.divider()

    st.metric(
        "Matching Findings",
        len(filtered)
    )

    display_columns = [
        "Model",
        "object",
        "object_type",
        "category",
        "issue",
        "severity",
        "confidence",
        "rule_id"
    ]

    if filtered.empty:

        st.info(
            "No findings match your selected filters."
        )

    else:

        st.dataframe(
            filtered[display_columns],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.markdown("### Inspect Finding Evidence")

        filtered = filtered.reset_index(drop=True)

        finding_options = list(range(len(filtered)))

        selected_finding = st.selectbox(
            "Choose a finding",
            finding_options,
            format_func=lambda index: (
                f"{filtered.iloc[index]['Model']} | "
                f"{filtered.iloc[index]['object']} | "
                f"{filtered.iloc[index]['issue']}"
            ),
            key="inspect_finding"
        )

        finding = filtered.iloc[selected_finding]

        st.markdown(
            f"**{finding['object']}**"
        )

        a, b, c = st.columns(3)

        a.metric(
            "Severity",
            finding["severity"]
        )

        b.metric(
            "Confidence",
            finding["confidence"]
        )

        c.metric(
            "Rule ID",
            finding["rule_id"]
        )

        with st.expander(
            "Evidence",
            expanded=True
        ):
            st.write(finding["evidence"])

        with st.expander("Business Impact"):
            st.write(finding["business_impact"])

        with st.expander("Recommended Fix"):
            st.write(finding["fix"])

        with st.expander("Validation Guidance"):
            st.write(finding["validation_status"])

        filtered_csv = filtered.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Filtered Findings",
            data=filtered_csv,
            file_name="filtered_readiness_findings.csv",
            mime="text/csv"
        )


# =========================================================
# TAB 4: VALIDATION BACKLOG
# =========================================================

with validation_tab:

    st.subheader("Validation Backlog")

    st.caption(
        "Review findings that contain validation guidance. "
        "These are review recommendations, not necessarily "
        "confirmed defects."
    )

    backlog = combined[
        combined["validation_status"].notna()
        & (
            combined["validation_status"]
            .astype(str)
            .str.strip() != ""
        )
    ].copy()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Findings to Review",
        len(backlog)
    )

    col2.metric(
        "Low Confidence",
        int(
            (backlog["confidence"] == "Low").sum()
        )
    )

    col3.metric(
        "High Severity",
        int(
            (backlog["severity"] == "High").sum()
        )
    )

    st.divider()

    backlog_category = st.multiselect(
        "Filter by category",
        CATEGORIES,
        default=CATEGORIES,
        key="backlog_category"
    )

    backlog = backlog[
        backlog["category"].isin(backlog_category)
    ]

    backlog_columns = [
        "Model",
        "object",
        "category",
        "issue",
        "severity",
        "confidence",
        "validation_status"
    ]

    if backlog.empty:

        st.info(
            "No validation items match this filter."
        )

    else:

        st.dataframe(
            backlog[backlog_columns],
            use_container_width=True,
            hide_index=True
        )

        backlog_csv = backlog.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Validation Backlog",
            data=backlog_csv,
            file_name="validation_backlog.csv",
            mime="text/csv"
        )


# =========================================================

# TAB 5: GEMINI AI ENRICHMENT
# =========================================================

with ai_tab:

    st.subheader("AI-Assisted Finding Enrichment")

    st.write(
        "Browse safe findings, select the ones you want to improve, "
        "and ask Gemini to generate explanations, descriptions, "
        "synonyms and validation questions."
    )

    st.info(
        "Gemini only receives your selected eligible findings. "
        "Security & Governance findings and detected sensitive "
        "fields are excluded. AI suggestions remain drafts."
    )

    # -----------------------------------------------------
    # 1. SELECT MODEL
    # -----------------------------------------------------

    ai_model_name = st.selectbox(
        "Select semantic model",
        list(reports.keys()),
        key="ai_model_select"
    )

    ai_report = reports[ai_model_name]

    # -----------------------------------------------------
    # 2. PREPARE ALL SAFE FINDINGS
    # -----------------------------------------------------

    candidate_preview = prepare_safe_payload(
        ai_report,
        selected_finding_ids=[]
    )

    safe_findings = candidate_preview["safe_findings"]

    st.divider()

    st.markdown("### Available Safe Findings")

    st.caption(
        "These findings passed the privacy filters. "
        "You can select individual findings below."
    )

    if safe_findings:

        safe_df = pd.DataFrame(safe_findings)

        st.dataframe(
            safe_df[
                [
                    "finding_id",
                    "object",
                    "category",
                    "rule_id",
                    "issue"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # -------------------------------------------------
        # 3. USER SELECTS FINDINGS
        # -------------------------------------------------

        st.markdown("### Select Findings for Gemini")

        finding_labels = {
            finding["finding_id"]: (
                f"{finding['finding_id']} | "
                f"{finding['object']} | "
                f"{finding['issue']}"
            )
            for finding in safe_findings
        }

        selected_finding_ids = st.multiselect(
            "Choose the findings you want Gemini to enrich",
            options=[
                finding["finding_id"]
                for finding in safe_findings
            ],
            format_func=lambda finding_id: (
                finding_labels[finding_id]
            ),
            key=f"gemini_selection_{ai_model_name}"
        )

    else:

        selected_finding_ids = []

        st.warning(
            "No safe findings are available for this model."
        )

    # -----------------------------------------------------
    # 4. PREPARE EXACT USER SELECTION
    # -----------------------------------------------------

    preview = prepare_safe_payload(
        ai_report,
        selected_finding_ids=selected_finding_ids
    )

    st.divider()

    st.markdown("### Privacy and Submission Preview")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Safe Findings",
        preview["eligible_count"]
    )

    c2.metric(
        "Selected by User",
        preview["selected_count"]
    )

    c3.metric(
        "To Be Submitted",
        preview["submitted_count"]
    )

    c4.metric(
        "Security Excluded",
        preview["excluded_security"]
    )

    c5.metric(
        "Sensitive Excluded",
        preview["excluded_sensitive"]
    )

    if preview["excluded_by_limit"] > 0:

        st.warning(
            f"You selected more than "
            f"{MAX_FINDINGS_PER_REQUEST} findings. "
            "Only the first 20 would be submitted. "
            "Please select 20 or fewer before proceeding."
        )

    elif preview["selected_count"] == 0:

        st.info(
            "Select at least one safe finding to generate "
            "Gemini suggestions."
        )

    # -----------------------------------------------------
    # 5. SHOW EXACT SELECTED FINDINGS
    # -----------------------------------------------------

    if preview["findings"]:

        st.markdown("### Findings Selected for Submission")

        submitted_df = pd.DataFrame(
            preview["findings"]
        )

        st.dataframe(
            submitted_df[
                [
                    "finding_id",
                    "object",
                    "category",
                    "issue"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    # -----------------------------------------------------
    # 6. GEMINI BUTTON
    # -----------------------------------------------------

    can_submit = (
        preview["selected_count"] > 0
        and preview["selected_count"] <= MAX_FINDINGS_PER_REQUEST
    )

    st.divider()

    if st.button(
        "✨ Generate Suggestions for Selected Findings",
        disabled=not can_submit,
        use_container_width=True,
        key="run_selected_gemini"
    ):

        with st.spinner(
            "Gemini is enriching your selected findings..."
        ):

            result = enrich_findings_with_gemini(
                ai_report,
                selected_finding_ids=selected_finding_ids
            )

        if "ai_results" not in st.session_state:
            st.session_state["ai_results"] = {}

        # Store suggestions against the exact selection.
        result_key = (
            ai_model_name,
            tuple(sorted(selected_finding_ids))
        )

        st.session_state["ai_results"][result_key] = result

    # -----------------------------------------------------
    # 7. DISPLAY RESULTS FOR CURRENT SELECTION
    # -----------------------------------------------------

    result_key = (
        ai_model_name,
        tuple(sorted(selected_finding_ids))
    )

    result = st.session_state.get(
        "ai_results", {}
    ).get(result_key)

    if result:

        st.divider()

        st.markdown("### Gemini Suggestions")

        if result.get("ok"):

            st.success(
                result["message"]
            )

            st.caption(
                f"Model: {result.get('model')} | "
                f"Findings submitted: {result.get('submitted_count')}"
            )

            enrichments = result.get(
                "enrichments",
                []
            )

            # Map stable IDs to original scanner findings.
            finding_lookup = {}

            for position, (_, row) in enumerate(
                ai_report.iterrows(),
                start=1
            ):

                finding_id = f"F{position:04d}"

                finding_lookup[finding_id] = row

            if not enrichments:

                st.info(
                    "Gemini returned no usable enrichment results."
                )

            for item in enrichments:

                finding_id = item["finding_id"]

                source = finding_lookup.get(
                    finding_id
                )

                if source is None:
                    continue

                with st.expander(
                    f"{source['object']} | {source['issue']}",
                    expanded=True
                ):

                    a, b, c = st.columns(3)

                    a.metric(
                        "Original Severity",
                        source["severity"]
                    )

                    b.metric(
                        "Original Confidence",
                        source["confidence"]
                    )

                    c.metric(
                        "Rule ID",
                        source["rule_id"]
                    )

                    st.markdown("**AI Explanation**")

                    st.write(
                        item["explanation"]
                    )

                    st.markdown("**Suggested Description**")

                    st.write(
                        item["suggested_description"]
                    )

                    st.markdown("**Suggested Synonyms**")

                    synonyms = item["suggested_synonyms"]

                    if synonyms:

                        st.write(
                            ", ".join(synonyms)
                        )

                    else:

                        st.write(
                            "No synonyms suggested."
                        )

                    st.markdown("**Validation Questions**")

                    for question in item["validation_questions"]:

                        st.markdown(
                            f"- {question}"
                        )

                    st.caption(
                        "AI-generated draft. Confirm with the "
                        "relevant data owner before adopting."
                    )

        else:

            st.warning(
                result["message"]
            )

            st.caption(
                "The deterministic scanner and saved reports "
                "remain available."
            )


# =========================================================
# TAB 6: QUESTION BENCHMARK
# =========================================================

with benchmark_tab:

    st.subheader("Natural-Language Question Benchmark")

    st.write(
        "Test whether the Finance, Sales and HR semantic models expose "
        "the metadata dependencies needed by a set of 25 representative "
        "business questions."
    )

    st.info(
        "This benchmark evaluates model metadata and declared dependencies. "
        "It does not execute natural-language queries or certify answer accuracy. "
        "‘Likely supported’ means the required structural dependencies were found; "
        "‘Needs validation’ means a human review is still required; and "
        "‘Gap detected’ means a required measure or metadata dependency is missing."
    )

    # Re-run the existing tested benchmark script. This keeps benchmark
    # evaluation logic in engine/benchmark_engine.py and test_benchmark.py.
    run_col, info_col = st.columns([1, 2])

    with run_col:
        run_benchmark = st.button(
            "▶ Run 25-Question Benchmark",
            use_container_width=True,
            key="run_question_benchmark"
        )

    with info_col:
        st.caption(
            "The run uses the existing benchmark_questions.csv and refreshes "
            "reports/benchmark_results.csv. No scanner or scoring files are changed."
        )

    if run_benchmark:

        benchmark_script = ROOT / "test_benchmark.py"

        if not benchmark_script.exists():
            st.error(
                "Could not find test_benchmark.py in the project root. "
                "The saved benchmark report can still be viewed below."
            )
        else:
            try:
                with st.spinner("Evaluating the 25 benchmark questions..."):
                    completed = subprocess.run(
                        [sys.executable, str(benchmark_script)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=300,
                        check=False
                    )

                if completed.returncode == 0:
                    st.success("Benchmark completed. The results below have been refreshed.")
                else:
                    st.error(
                        "The benchmark script returned an error. "
                        "Review the output below for details."
                    )

                with st.expander("Benchmark execution output"):
                    if completed.stdout.strip():
                        st.code(completed.stdout, language="text")
                    if completed.stderr.strip():
                        st.code(completed.stderr, language="text")
                    if not completed.stdout.strip() and not completed.stderr.strip():
                        st.caption("The benchmark script produced no console output.")

            except subprocess.TimeoutExpired:
                st.error(
                    "The benchmark did not finish within 5 minutes. "
                    "Check the terminal and run python test_benchmark.py manually."
                )
            except Exception as error:
                st.error(f"Unable to run benchmark: {error}")

    st.divider()

    if not BENCHMARK_REPORT_PATH.exists():

        st.warning(
            "No benchmark results file was found yet. "
            "Use ‘Run 25-Question Benchmark’ above, or run "
            "python test_benchmark.py from the project terminal."
        )

    else:

        try:
            benchmark_df = pd.read_csv(
                BENCHMARK_REPORT_PATH,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig"
            )

            expected_columns = {
                "question_id",
                "model",
                "question",
                "computed_result",
                "assessment_reasons"
            }
            missing_columns = sorted(expected_columns - set(benchmark_df.columns))

            if missing_columns:
                st.error(
                    "The benchmark report is missing expected columns: "
                    + ", ".join(missing_columns)
                )
            else:
                result_order = [
                    "Likely supported",
                    "Needs validation",
                    "Gap detected"
                ]

                total_questions = len(benchmark_df)
                status_counts = {
                    status: int((benchmark_df["computed_result"] == status).sum())
                    for status in result_order
                }

                st.markdown("### Portfolio Results")

                metric_cols = st.columns(4)
                metric_cols[0].metric("Questions evaluated", total_questions)
                metric_cols[1].metric(
                    "Likely supported",
                    status_counts["Likely supported"]
                )
                metric_cols[2].metric(
                    "Needs validation",
                    status_counts["Needs validation"]
                )
                metric_cols[3].metric(
                    "Gaps detected",
                    status_counts["Gap detected"]
                )

                if total_questions != 25:
                    st.warning(
                        f"The saved report contains {total_questions} questions; "
                        "the intended benchmark contains 25."
                    )

                st.divider()
                st.markdown("### Results by Semantic Model")

                model_order = [
                    model for model in ["Finance", "Sales", "HR"]
                    if model in benchmark_df["model"].unique()
                ]
                model_counts = pd.crosstab(
                    benchmark_df["model"],
                    benchmark_df["computed_result"]
                )
                model_counts = model_counts.reindex(
                    index=model_order,
                    columns=result_order,
                    fill_value=0
                )
                model_counts.index.name = "Model"
                model_counts.columns.name = "Assessment"

                chart_col, table_col = st.columns([1.15, 1])
                with chart_col:
                    st.markdown("**Assessment distribution**")
                    st.bar_chart(model_counts)
                with table_col:
                    st.markdown("**Question counts**")
                    model_summary = model_counts.copy()
                    model_summary["Total"] = model_summary.sum(axis=1)
                    st.dataframe(
                        model_summary.reset_index(),
                        use_container_width=True,
                        hide_index=True
                    )

                st.divider()
                st.markdown("### Explore Individual Questions")

                filter_col1, filter_col2 = st.columns(2)
                available_models = [
                    model for model in ["Finance", "Sales", "HR"]
                    if model in benchmark_df["model"].unique()
                ]

                with filter_col1:
                    selected_benchmark_models = st.multiselect(
                        "Filter by model",
                        options=available_models,
                        default=available_models,
                        key="benchmark_model_filter"
                    )

                with filter_col2:
                    selected_benchmark_statuses = st.multiselect(
                        "Filter by assessment",
                        options=result_order,
                        default=result_order,
                        key="benchmark_status_filter"
                    )

                filtered_benchmark = benchmark_df[
                    benchmark_df["model"].isin(selected_benchmark_models)
                    & benchmark_df["computed_result"].isin(selected_benchmark_statuses)
                ].copy()

                preferred_columns = [
                    "question_id",
                    "model",
                    "question",
                    "metric",
                    "computed_result",
                    "assessment_reasons"
                ]
                visible_columns = [
                    column for column in preferred_columns
                    if column in filtered_benchmark.columns
                ]

                st.caption(f"Showing {len(filtered_benchmark)} of {total_questions} questions")

                if filtered_benchmark.empty:
                    st.info("No questions match the selected filters.")
                else:
                    st.dataframe(
                        filtered_benchmark[visible_columns],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "question_id": st.column_config.TextColumn("ID", width="small"),
                            "model": st.column_config.TextColumn("Model", width="small"),
                            "question": st.column_config.TextColumn("Business question", width="large"),
                            "metric": st.column_config.TextColumn("Metric", width="medium"),
                            "computed_result": st.column_config.TextColumn("Assessment", width="medium"),
                            "assessment_reasons": st.column_config.TextColumn("Why this result?", width="large")
                        }
                    )

                    st.markdown("#### Inspect a question")
                    filtered_benchmark = filtered_benchmark.reset_index(drop=True)
                    selected_question_index = st.selectbox(
                        "Choose a benchmark question",
                        options=list(range(len(filtered_benchmark))),
                        format_func=lambda index: (
                            f"{filtered_benchmark.iloc[index]['question_id']} | "
                            f"{filtered_benchmark.iloc[index]['model']} | "
                            f"{filtered_benchmark.iloc[index]['question']}"
                        ),
                        key="benchmark_question_inspector"
                    )

                    selected_question = filtered_benchmark.iloc[selected_question_index]
                    st.markdown(f"**{selected_question['question']}**")

                    detail_col1, detail_col2 = st.columns(2)
                    with detail_col1:
                        st.metric("Model", selected_question["model"])
                    with detail_col2:
                        st.metric("Assessment", selected_question["computed_result"])

                    st.markdown("**Assessment explanation**")
                    st.write(
                        selected_question.get(
                            "assessment_reasons",
                            "No assessment explanation was saved."
                        ) or "No assessment explanation was saved."
                    )

                    optional_detail_fields = [
                        ("metric", "Business metric"),
                        ("required_measures", "Required measures"),
                        ("required_tables", "Required tables"),
                        ("required_columns", "Required columns"),
                        ("required_filters", "Required filters"),
                        ("required_relationships", "Required relationships"),
                        ("initial_hypothesis", "Initial hypothesis"),
                        ("reason", "Benchmark rationale")
                    ]

                    with st.expander("View benchmark requirements and rationale"):
                        for field, label in optional_detail_fields:
                            if field in selected_question.index:
                                value = str(selected_question[field]).strip()
                                if value:
                                    st.markdown(f"**{label}**")
                                    st.write(value)

                st.divider()
                st.download_button(
                    label="Download Benchmark Results (CSV)",
                    data=benchmark_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="benchmark_results.csv",
                    mime="text/csv",
                    key="download_benchmark_results"
                )

        except Exception as error:
            st.error(f"Unable to load benchmark results: {error}")


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Talk-to-Data Readiness Analyzer | Prototype Version | "
    "Scores and findings require validation against actual "
    "semantic-model metadata and organizational policies."
)
