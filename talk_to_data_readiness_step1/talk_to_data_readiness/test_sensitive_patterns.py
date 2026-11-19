
from engine.ai_enrichment import SENSITIVE_PATTERN

test_cases = {
    "EMP_SALARY": True,
    "CUST_EMAIL": True,
    "USER_PHONE": True,
    "ANNUAL_COMP": True,
    "D_EMPLOYEE[SALARY]": True,
    "CUSTOMER_NAME": False,
    "PRODUCT_CATEGORY": False,
    "MONTH_NAME": False,
    "EMAILING_STATUS": False
}

for value, expected in test_cases.items():

    actual = bool(SENSITIVE_PATTERN.search(value))

    print(
        f"{value:25} Expected: {expected} | Actual: {actual}"
    )

    assert actual == expected, (
        f"Failed for {value}"
    )

print("\nALL SENSITIVE PATTERN TESTS PASSED!")
