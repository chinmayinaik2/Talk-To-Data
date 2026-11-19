from engine.source_verifier import verify_evidence
import pandas as pd
from pathlib import Path

from engine.llm_enricher import enrich_finding

ROOT = Path(__file__).resolve().parent

REPORT_FILE = ROOT / "output" / "readiness_report.csv"

GLOSSARY_FILE = (
    ROOT / "data" / "starter_kit" /
    "glossary" / "business_glossary.md"
)

MODEL_FILE = (
    ROOT / "data" / "starter_kit" /
    "model" / "model_definition.md"
)

report = pd.read_csv(REPORT_FILE)

glossary = GLOSSARY_FILE.read_text(encoding="utf-8")
model_definition = MODEL_FILE.read_text(encoding="utf-8")

finding = report.iloc[0].to_dict()

result = enrich_finding(
    finding,
    glossary,
    model_definition
)

# Verify original scanner information is unchanged
assert result["original_finding"]["severity"] == finding["severity"]
assert result["original_finding"]["issue"] == finding["issue"]

print("\nORIGINAL FINDING")
print("----------------")
print(finding)

print("\nAI-ENRICHED RESULT")
print("------------------")

for key, value in result.items():
    print(f"\n{key}: {value}")


verification = verify_evidence(
    result,
    glossary,
    model_definition
)

print("\nSOURCE EVIDENCE VERIFICATION")
print("----------------------------")

print("Verified evidence:", verification["verified_count"])
print("Unverified evidence:", verification["unverified_count"])

print("\nVerified claims:")
for item in verification["verified_evidence"]:
    print("-", item["claim"])

print("\nUnverified claims:")
for item in verification["unverified_evidence"]:
    print("-", item["claim"])
    print("  Reason:", item["verification_reason"])