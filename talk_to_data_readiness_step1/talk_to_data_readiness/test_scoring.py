
from pathlib import Path

import pandas as pd

from engine.scoring import calculate_readiness_score


reports_folder = Path("reports")

for report_path in sorted(reports_folder.glob("*_readiness_report.csv")):
    print("\n" + "=" * 55)
    print(f"MODEL: {report_path.name}")
    print("=" * 55)

    report = pd.read_csv(report_path)

    result = calculate_readiness_score(report)

    print("Total findings:", len(report))
    print("Readiness score:", result["readiness_score"])
    print("Category risks:", result["category_risks"])
    print("Note:", result["message"])
    print("Category status:", result["category_status"])
    print("Category details:", result["category_details"])
    print("Validation queue:", result["validation_queue"])
