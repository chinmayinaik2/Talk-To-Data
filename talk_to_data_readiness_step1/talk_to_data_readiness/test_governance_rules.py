
from pathlib import Path

from engine.metadata_parser import parse_model
from engine.governance_rules import scan_governance


ROOT = Path(__file__).resolve().parent

MODELS = {
    "Finance": ROOT / "data/starter_kit/model/finance_model/model_definition.md",
    "Sales": ROOT / "data/starter_kit/model/sales_model/model_definition.md",
    "HR": ROOT / "data/starter_kit/model/hr_model/model_definition.md"
}


for model_name, model_path in MODELS.items():

    metadata = parse_model(model_path)
    report = scan_governance(metadata)

    print("\n" + "=" * 60)
    print(f"{model_name} GOVERNANCE FINDINGS")
    print("=" * 60)

    if report.empty:
        print("No sensitive fields detected.")
    else:
        print(report.to_string(index=False))

    print("\nFinding count:", len(report))
