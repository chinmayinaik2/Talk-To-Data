
from pathlib import Path
import re


def normalize_markdown(text: str) -> str:
    """Normalize Markdown formatting without changing code blocks."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def get_section(text: str, heading: str) -> str:
    """Extract a Markdown section using its heading."""
    pattern = (
        rf"^##\s+{re.escape(heading)}.*?"
        rf"(?=^##\s+|\Z)"
    )

    match = re.search(
        pattern,
        text,
        re.DOTALL | re.MULTILINE | re.IGNORECASE
    )

    return match.group() if match else ""


def parse_table_columns(model_text: str) -> dict:
    tables = {}
    section = get_section(model_text, "Tables and columns")

    for line in section.splitlines():
        line = line.strip()

        if not line.startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in line.strip("|").split("|")
        ]

        if len(cells) != 2:
            continue

        table_name, columns_text = cells

        if table_name.lower() == "table":
            continue

        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name) is None:
            continue

        columns = [
            column.strip()
            for column in columns_text.split(",")
            if column.strip()
        ]

        tables[table_name] = columns

    return tables

def clean_markdown_value(value: str) -> str:
    """Remove simple Markdown emphasis markers from metadata values."""
    return re.sub(r"\*+", "", value).strip()


def parse_relationships(model_text: str) -> list:
    relationships = []
    section = get_section(model_text, "Relationships")

    for line in section.splitlines():
        line = line.strip()

        if not line.startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in line.strip("|").split("|")
        ]

        if len(cells) != 5:
            continue

        if cells[0].lower() == "from":
            continue

        if not cells[0] or set(cells[0]) == {"-"}:
            continue


        relationships.append({
            "from": clean_markdown_value(cells[0]),
            "to": clean_markdown_value(cells[1]),
            "cardinality": clean_markdown_value(cells[2]),
            "active": clean_markdown_value(cells[3]),
            "cross_filter": clean_markdown_value(cells[4])
        })

    return relationships


def parse_measures(model_text: str) -> dict:
    measures = {}
    section = get_section(model_text, "Measures")

    if not section:
        return measures

    code_blocks = re.findall(
        r"```(.*?)```",
        section,
        re.DOTALL
    )

    for block in code_blocks:
        for line in block.splitlines():
            line = line.strip()

            if not line or "=" not in line:
                continue

            name, expression = line.split("=", 1)

            name = name.strip()
            expression = expression.strip()

            if name and expression:
                measures[name] = expression

    return measures


def parse_model_settings(model_text: str) -> dict:
    text = re.sub(r"\*+", "", model_text).lower()

    return {
        "descriptions_missing": (
            "no table or column has a description" in text
        ),
        "all_columns_visible": (
            "all columns are visible" in text
        ),
        "default_sum_summarization": (
            'default "sum" summarization' in text
        ),
        "date_table_not_marked": (
            "not marked as a date table" in text
        ),
        "month_not_sorted": (
            "not sorted by mo" in text
        )
    }


def parse_model(model_path) -> dict:
    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model definition not found: {model_path}"
        )

    original_text = model_path.read_text(encoding="utf-8")
    model_text = normalize_markdown(original_text)

    model_name_match = re.search(
        r'^#\s*Semantic model:\s*["\']?([^"\']+)',
        model_text,
        re.IGNORECASE | re.MULTILINE
    )

    model_name = (
        model_name_match.group(1).strip()
        if model_name_match
        else model_path.parent.name
    )

    return {
        "model_name": model_name,
        "tables": parse_table_columns(model_text),
        "relationships": parse_relationships(model_text),
        "measures": parse_measures(model_text),
        "settings": parse_model_settings(model_text)
    }
