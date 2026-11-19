
from pathlib import Path

from engine.metadata_parser import parse_model
from engine.generic_rules import scan_generic


ROOT = Path(__file__).resolve().parent

MODEL_FOLDERS = [
    "finance_model",
    "sales_model",
    "hr_model"
]


def test_all_models():
    for folder in MODEL_FOLDERS:

        model_path = (
            ROOT / "data" / "starter_kit" /
            "model" / folder / "model_definition.md"
        )

        metadata = parse_model(model_path)
        report = scan_generic(metadata)

        print("\n" + "=" * 55)
        print("MODEL:", metadata["model_name"])
        print("=" * 55)

        print("Total generic findings:", len(report))


        print("\nFindings grouped by issue:")
        print(report["issue"].value_counts().to_string())

        print("\nFindings excluding missing descriptions:")
        other_findings = report[
            ~report["issue"].str.contains(
                "Missing table description|Missing column description",
                case=False,
                regex=True
            )
        ]

        print(
            other_findings[
                ["object", "object_type", "issue", "severity"]
            ].to_string(index=False)
        )


        print("\nSample findings:")
        print(
              report[
              ["object", "object_type", "issue", "severity"]
              ].head(10).to_string(index=False)
            )

        print("\nFindings by severity:")
        print(report["severity"].value_counts())

        print("\nFindings by type:")
        print(report["object_type"].value_counts())

        assert not report.empty

        assert list(report.columns) == [
            "object",
            "object_type",
            "issue",
            "severity",
            "fix"
        ]

        assert set(report["severity"]).issubset({
            "Critical", "High", "Medium", "Low"
        })


if __name__ == "__main__":
    test_all_models()
    print("\nALL GENERIC RULE TESTS PASSED!")
