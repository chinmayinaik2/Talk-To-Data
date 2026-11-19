
from pathlib import Path
from engine.business_rules import parse_glossary
from engine.metadata_parser import parse_model
from engine.business_rules import scan_business

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
    metadata = parse_model(model_path)
    print("\nEXTRACTED GLOSSARY TERMS:")
    print(parse_glossary(glossary_path))

    print("\nMEASURES FOUND:")
    print(metadata.get("measures", {}))
    report = scan_business(metadata, glossary_path)

    print("\nGLOSSARY FILE CONTENT:")
    print(glossary_path.read_text(encoding="utf-8"))

    print(f"\n{'=' * 60}")
    print(f"{model_name} BUSINESS RULE FINDINGS")
    print(f"{'=' * 60}")

    if report.empty:
        print("No findings.")
    else:
        print(report.to_string(index=False))
        print("\nFinding count:", len(report))
