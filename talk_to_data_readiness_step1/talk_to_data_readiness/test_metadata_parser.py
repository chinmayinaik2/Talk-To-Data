
from pathlib import Path
from engine.metadata_parser import parse_model


ROOT = Path(__file__).resolve().parent

MODEL_FILE = (
    ROOT / "data" / "starter_kit" / "model"
    / "finance_model" / "model_definition.md"
)


def main():
    metadata = parse_model(MODEL_FILE)

    print("\nMODEL NAME")
    print(metadata["model_name"])

    print("\nDISCOVERED TABLES AND COLUMNS")

    for table, columns in metadata["tables"].items():
        print(f"\n{table}: {len(columns)} columns")
        print(columns)

    print("\nDISCOVERED RELATIONSHIPS")

    for relationship in metadata["relationships"]:
        print(relationship)

    print("\nDISCOVERED MEASURES")

    for measure, expression in metadata["measures"].items():
        print(f"{measure} = {expression}")

    print("\nMODEL SETTINGS")
    print(metadata["settings"])

    # Basic validation
    assert len(metadata["tables"]) > 0
    assert len(metadata["relationships"]) > 0
    assert len(metadata["measures"]) > 0

    print("\nPARSER TEST PASSED!")


if __name__ == "__main__":
    main()

from pathlib import Path
import re

text = Path(
    "data/starter_kit/model/finance_model/model_definition.md"
).read_text(encoding="utf-8")

print("\n--- MEASURE SECTION DIAGNOSTIC ---")

for line in text.splitlines():
    if "Measures" in line or "Measure 1" in line:
        print(repr(line))

print("\n--- CODE BLOCKS ---")

blocks = re.findall(r"```(.*?)```", text, re.DOTALL)

for block in blocks:
    print(repr(block))