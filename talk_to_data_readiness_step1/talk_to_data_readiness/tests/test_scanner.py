
from pathlib import Path
from engine.scanner import scan_model

ROOT = Path(__file__).resolve().parents[1]

MODEL = ROOT / "data" / "starter_kit" / "model" / "model_definition.md"
GLOSSARY = ROOT / "data" / "starter_kit" / "glossary" / "business_glossary.md"


def get_report():
    return scan_model(MODEL, GLOSSARY)


def test_report_is_not_empty():
    report = get_report()
    assert not report.empty


def test_report_has_required_columns():
    report = get_report()
    assert list(report.columns) == [
        "object", "object_type", "issue", "severity", "fix"
    ]


def test_sensitive_compensation_is_detected():
    report = get_report()
    assert "D_REP[ANNUAL_COMP]" in report["object"].values


def test_margin_issue_is_detected():
    report = get_report()
    assert "F_TRX[Margin]" in report["object"].values


def test_shipping_relationship_is_detected():
    report = get_report()
    assert (
        "F_TRX[SHP_DT_KEY] -> D_CAL[DT_KEY]"
        in report["object"].values
    )


def test_severity_values_are_valid():
    report = get_report()
    assert set(report["severity"]).issubset(
        {"Critical", "High", "Medium", "Low"}
    )
