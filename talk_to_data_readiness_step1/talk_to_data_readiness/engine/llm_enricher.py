
import json
from engine.llm_helper import generate_text


def enrich_finding(
    finding: dict,
    glossary: str,
    model_definition: str
) -> dict:
    """
    Enrich a scanner finding using only supplied source material.
    Original scanner fields are preserved.
    """

    prompt = f"""
You are a senior Power BI and data analytics consultant.

Analyze the scanner finding using ONLY the source material below.

BUSINESS GLOSSARY:
{glossary}

MODEL DEFINITION:
{model_definition}

SCANNER FINDING:
Object: {finding.get("object")}
Object type: {finding.get("object_type")}
Issue: {finding.get("issue")}
Severity: {finding.get("severity")}
Existing fix: {finding.get("fix")}

Return ONLY valid JSON in this structure:

{{
  "business_explanation": "Simple explanation of the issue",
  "business_impact": "Potential impact on analytics users",
  "recommended_action": "Specific corrective action",
  "suggested_business_terms": ["term 1", "term 2"],
  "supporting_evidence": [
    {{
      "claim": "A factual claim made in your response",
      "source": "Business glossary or Model definition",
      "evidence": "Exact supporting information"
    }}
  ],
  "insufficient_context": false,
  "limitations": []
}}

STRICT RULES:
1. Do not invent table grain, metrics, relationships or definitions.
2. Every factual business claim must have supporting evidence.
3. If evidence is unavailable, mention that information is not documented.
4. Do not change the original scanner severity or issue.
5. Do not treat a suggested term as an officially approved synonym.
6. Set insufficient_context to true if important information is missing.
7. Return valid JSON only.
"""

    response = generate_text(prompt)

    cleaned = response.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Gemini did not return valid JSON: {response}"
        ) from error

    required_fields = [
        "business_explanation",
        "business_impact",
        "recommended_action",
        "suggested_business_terms",
        "supporting_evidence",
        "insufficient_context",
        "limitations"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(
                f"Gemini response is missing: {field}"
            )

    return {
        **result,
        "original_finding": finding
    }
