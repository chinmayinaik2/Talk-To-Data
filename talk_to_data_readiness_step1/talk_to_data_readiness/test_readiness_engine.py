
from pathlib import Path

from engine.readiness_engine import (
    scan_model,
    get_readiness_summary,
    save_report
)


ROOT = Path(__file__).resolve().parent

MODELS = {
    "Finance": (
        ROOT / "data/starter_kit/model/finance_model/model_definition.md",
        ROOT / "data/starter_kit/model/finance_model/business_glossary.md"
    ),

    "Sales": (
        ROOT / "data/starter_kit/model/sales_model/model_definition.md",
        ROOT / "data/starter_kit/model/sales_model/business_glossary.md"
    ),

    "HR": (
        ROOT / "data/starter_kit/model/hr_model/model_definition.md",
        ROOT / "data/starter_kit/model/hr_model/business_glossary.md"
    )
}


for model_name, (model_path, glossary_path) in MODELS.items():

    print("\n" + "=" * 65)
    print(f"{model_name.upper()} READINESS REPORT")
    print("=" * 65)

    report = scan_model(model_path, glossary_path)

    summary = get_readiness_summary(report)

    print("\nSUMMARY")
    print("-" * 40)

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nFINDINGS BY CATEGORY")
    print("-" * 40)

    if report.empty:
        print("No findings detected.")
    else:
        print(
            report.groupby(
                ["category", "severity"]
            ).size().to_string()
        )

        print("\nDETAILED FINDINGS")
        print("-" * 40)

        print(report.to_string(index=False))

    output_path = (
        ROOT / "reports" / f"{model_name.lower()}_readiness_report.csv"
    )

    save_report(report, output_path)

print("\nAll three models scanned successfully.")
