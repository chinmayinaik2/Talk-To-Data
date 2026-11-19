
import importlib.metadata
import pandas as pd

from engine.ai_enrichment import enrich_findings_with_gemini


print("Google Gen AI SDK version:",
      importlib.metadata.version("google-genai"))

# Synthetic test finding only.
# Do not use company or personal metadata for this test.
sample_report = pd.DataFrame([
    {
        "object": "D_DATE[MONTH_NAME]",
        "object_type": "Column",
        "issue": "Month name may not be sorted by month number",
        "severity": "Medium",
        "fix": "Sort month name using month number.",
        "category": "Metadata",
        "model_name": "Demo Model",
        "rule_id": "MD-MONTH-SORT"
    }
])

print("\nSending one synthetic finding to Gemini...")

result = enrich_findings_with_gemini(sample_report)

print("\nAPI success:", result["ok"])
print("Message:", result["message"])

if result["ok"]:

    print("Model:", result["model"])
    print("Findings submitted:", result["submitted_count"])

    print("\nGEMINI SUGGESTIONS")
    print("=" * 50)

    for item in result["enrichments"]:

        print("\nFinding:", item["finding_id"])

        print("\nExplanation:")
        print(item["explanation"])

        print("\nSuggested description:")
        print(item["suggested_description"])

        print("\nSuggested synonyms:")
        print(item["suggested_synonyms"])

        print("\nValidation questions:")
        for question in item["validation_questions"]:
            print("-", question)

else:
    print("\nGemini did not return enrichment.")
    print("The deterministic scanner remains unaffected.")
