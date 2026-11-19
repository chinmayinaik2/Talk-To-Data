
from pathlib import Path
import re

file_path = Path(
    "data/starter_kit/model/finance_model/model_definition.md"
)

text = file_path.read_text(encoding="utf-8")

print("\n--- LINES CONTAINING MEASURE REFERENCES ---")

for line_number, line in enumerate(text.splitlines(), start=1):
    if "measure" in line.lower() or "rev" in line.lower():
        print(f"Line {line_number}: {repr(line)}")

print("\n--- ALL MARKDOWN HEADINGS ---")

for line in text.splitlines():
    if line.strip().startswith("#"):
        print(repr(line))

print("\n--- ALL CODE BLOCKS ---")

blocks = re.findall(r"```(.*?)```", text, re.DOTALL)

for index, block in enumerate(blocks, start=1):
    print(f"\nCode block {index}:")
    print(repr(block))
