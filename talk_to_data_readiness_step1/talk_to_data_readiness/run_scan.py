
from pathlib import Path
from engine.scanner import scan_model, save_report


ROOT = Path(__file__).resolve().parent

KIT = ROOT / "data" / "starter_kit"

MODEL_FILE = KIT / "model" / "model_definition.md"
GLOSSARY_FILE = KIT / "glossary" / "business_glossary.md"

OUTPUT_FILE = ROOT / "output" / "readiness_report.csv"


def main():

    print("\n======================================")
    print(" TALK-TO-DATA READINESS SCANNER")
    print("======================================")

    # Validate source files
    for file in [MODEL_FILE, GLOSSARY_FILE]:
        if not file.exists():
            raise FileNotFoundError(f"Missing input: {file}")

    print("\nLoading model definition and business glossary...")

    report = scan_model(MODEL_FILE, GLOSSARY_FILE)

    save_report(report, OUTPUT_FILE)

    print("\nScan completed!")
    print(f"Total findings: {len(report)}")

    print("\nSeverity breakdown:")
    print(report["severity"].value_counts().to_string())

    print("\nCategory breakdown:")
    print(report["object_type"].value_counts().to_string())

    print("\nFindings:")
    print(report.to_string(index=False))

    print(f"\nReport saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
