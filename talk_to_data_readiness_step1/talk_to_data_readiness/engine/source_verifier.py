
import re


def normalize_text(text: str) -> str:
    """Normalize whitespace and punctuation for comparison."""
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def verify_evidence(
    enrichment: dict,
    glossary: str,
    model_definition: str
) -> dict:

    sources = {
        "business glossary": glossary,
        "model definition": model_definition
    }

    verified = []
    unverified = []

    for item in enrichment.get("supporting_evidence", []):

        source_name = str(item.get("source", "")).strip().lower()
        evidence = str(item.get("evidence", "")).strip()

        matching_source = next(
            (
                content
                for name, content in sources.items()
                if name in source_name
            ),
            None
        )

        if matching_source is None:
            unverified.append({
                **item,
                "verification_reason": "Unknown source"
            })
            continue

        source_text = normalize_text(matching_source)
        evidence_text = normalize_text(evidence)

        # First try checking the complete evidence.
        if evidence_text and evidence_text in source_text:
            verified.append(item)
            continue

        # If evidence contains multiple statements,
        # check whether each individual statement exists.
        statements = [
            normalize_text(part)
            for part in re.split(r"[;\n]", evidence)
            if len(part.strip()) >= 12
        ]

        matched = [
            statement
            for statement in statements
            if statement in source_text
        ]

        if statements and len(matched) == len(statements):
            verified.append(item)
        else:
            unverified.append({
                **item,
                "verification_reason": (
                    f"Only {len(matched)} of "
                    f"{len(statements)} evidence statements "
                    "were found in the specified source."
                )
            })

    return {
        "verified_evidence": verified,
        "unverified_evidence": unverified,
        "verified_count": len(verified),
        "unverified_count": len(unverified),
        "evidence_text_check_passed": len(unverified) == 0
    }
