
from pathlib import Path
import pandas as pd

for path in sorted(Path("reports").glob("*_readiness_report.csv")):
    report = pd.read_csv(path)

    print("\n", "=" * 65)
    print(path.name)
    print("=" * 65)

    for category in report["category"].dropna().unique():
        findings = report[report["category"] == category]

        print(f"\nCATEGORY: {category}")
        print(findings[
            ["object", "issue", "severity", "fix"]
        ].to_string(index=False))
