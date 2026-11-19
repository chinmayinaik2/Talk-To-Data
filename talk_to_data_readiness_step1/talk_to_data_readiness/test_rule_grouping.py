
import pandas as pd

from engine.scoring import get_effective_rule_keys


sample = pd.DataFrame([
    {
        "rule_id": "GENERAL-REVIEW",
        "category": "Metadata",
        "model_name": "Demo",
        "object_type": "Column",
        "object": "D_DATE[YEAR]",
        "issue": "Unmapped issue A"
    },
    {
        "rule_id": "GENERAL-REVIEW",
        "category": "Metadata",
        "model_name": "Demo",
        "object_type": "Column",
        "object": "D_DATE[MONTH]",
        "issue": "Unmapped issue B"
    },
    {
        "rule_id": "GENERAL-REVIEW",
        "category": "Metadata",
        "model_name": "Demo",
        "object_type": "Column",
        "object": "D_DATE[YEAR]",
        "issue": "Unmapped issue A"
    },
    {
        "rule_id": "MD-DATE-TABLE",
        "category": "Metadata",
        "model_name": "Demo",
        "object_type": "Table",
        "object": "D_DATE",
        "issue": "Date table configuration"
    }
])

keys = get_effective_rule_keys(sample)

print("Generated grouping keys:")
print(keys.to_string(index=False))

print("\nDistinct groups:", keys.nunique())

assert keys.iloc[0] != keys.iloc[1]
assert keys.iloc[0] == keys.iloc[2]
assert keys.iloc[3] == "MD-DATE-TABLE"
assert keys.nunique() == 3

print("\nRULE GROUPING TEST PASSED!")
