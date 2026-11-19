
from pathlib import Path
import pandas as pd

required_columns = [
    "rule_id",
    "evidence",
    "confidence",
    "business_impact",
    "validation_status"
]

for path in sorted(Path("reports").glob("*_readiness_report.csv")):

    report = pd.read_csv(path)

    print("\n", "=" * 55)
    print(path.name)
    print("=" * 55)

    missing_columns = [
        column
        for column in required_columns
        if column not in report.columns
    ]

    print("Total findings:", len(report))
    print("Missing required columns:", missing_columns)

    if not missing_columns:
        print(
            "Missing evidence values:",
            report["evidence"].isna().sum()
        )
        print(
            "Missing confidence values:",
            report["confidence"].isna().sum()
        )
        print(
            "Confidence distribution:",
            report["confidence"].value_counts().to_dict()
        )

    assert not missing_columns, "Required columns are missing!"
    assert report["evidence"].notna().all()
    assert report["confidence"].notna().all()

print("\nALL ENRICHED REPORTS VERIFIED!")
