
from pathlib import Path
from engine.metadata_parser import parse_model

ROOT = Path(__file__).resolve().parent

MODEL_FOLDERS = [
    "finance_model",
    "sales_model",
    "hr_model"
]

for folder in MODEL_FOLDERS:
    print("\n" + "=" * 55)
    print(f"TESTING MODEL: {folder.upper()}")
    print("=" * 55)

    model_path = (
        ROOT / "data" / "starter_kit" / "model" /
        folder / "model_definition.md"
    )

    metadata = parse_model(model_path)

    print("Model name:", metadata["model_name"])
    print("Tables:", len(metadata["tables"]))
    print("Columns:", sum(
        len(columns) for columns in metadata["tables"].values()
    ))
    print("Relationships:", len(metadata["relationships"]))
    print("Measures:", len(metadata["measures"]))

    print("\nDiscovered table names:")
    for table in metadata["tables"]:
        print("-", table)

    assert len(metadata["tables"]) > 0, f"No tables found in {folder}"
    assert len(metadata["relationships"]) > 0, f"No relationships found in {folder}"
    assert len(metadata["measures"]) > 0, f"No measures found in {folder}"

print("\nALL THREE MODEL PARSER TESTS PASSED!")
