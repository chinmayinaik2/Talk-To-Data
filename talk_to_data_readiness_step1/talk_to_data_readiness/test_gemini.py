
from engine.llm_helper import generate_text

prompt = """
You are a data analytics assistant.

Explain in two simple sentences why business-friendly
column names are important in a Power BI semantic model.
"""

try:
    result = generate_text(prompt)
    print("\nGEMINI CONNECTION SUCCESSFUL")
    print("--------------------------------")
    print(result)

except Exception as error:
    print("\nGEMINI CONNECTION FAILED")
    print("--------------------------------")
    print(type(error).__name__)
    print(error)
