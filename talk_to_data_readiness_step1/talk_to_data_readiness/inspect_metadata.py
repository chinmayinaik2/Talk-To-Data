
from pathlib import Path
from pprint import pprint

from engine.metadata_parser import parse_model

ROOT = Path(__file__).resolve().parent

for model_folder in ["finance_model", "sales_model", "hr_model"]:
    model_path = (
        ROOT / "data" / "starter_kit" / "model" /
        model_folder / "model_definition.md"
    )

    metadata = parse_model(model_path)

    print("\n", "=" * 50)
    print("MODEL:", metadata["model_name"])
    print("=" * 50)

    print("\nMetadata keys:")
    print(list(metadata.keys()))

    print("\nOne table:")
    pprint(next(iter(metadata["tables"].items())))

    print("\nOne relationship:")
    pprint(metadata["relationships"][0])

    print("\nOne measure:")
    pprint(next(iter(metadata["measures"].items())))

    print("\nSettings:")
    pprint(metadata["settings"])
