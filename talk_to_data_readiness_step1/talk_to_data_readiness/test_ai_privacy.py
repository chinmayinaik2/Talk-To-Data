
import pandas as pd

from engine.ai_enrichment import prepare_safe_payload


sample_findings = pd.DataFrame([
    {
        "object": "D_DATE[MONTH_NAME]",
        "object_type": "Column",
        "issue": "Month name may not be sorted correctly",
        "fix": "Sort month name using month number.",
        "category": "Metadata",
        "model_name": "Demo Model",
        "rule_id": "MD-MONTH-SORT"
    },
    {
        "object": "D_EMPLOYEE[SALARY]",
        "object_type": "Sensitive Column",
        "issue": "Sensitive compensation field detected",
        "fix": "Review access permissions.",
        "category": "Security & Governance",
        "model_name": "HR Model",
        "rule_id": "GOV-SENSITIVE-FIELD"
    },
    {
        "object": "D_EMPLOYEE[EMAIL]",
        "object_type": "Column",
        "issue": "Column description is missing",
        "fix": "Add a description.",
        "category": "Metadata",
        "model_name": "HR Model",
        "rule_id": "MD-DESCRIPTION"
    }
])

result = prepare_safe_payload(sample_findings)

print("Eligible findings:", result["eligible_count"])
print("Submitted findings:", result["submitted_count"])
print("Security findings excluded:", result["excluded_security"])
print("Sensitive findings excluded:", result["excluded_sensitive"])
print("\nSafe payload:")
print(result["findings"])

assert result["submitted_count"] == 1
assert result["excluded_security"] == 1
assert result["excluded_sensitive"] == 1

print("\nPRIVACY FILTER TEST PASSED!")
