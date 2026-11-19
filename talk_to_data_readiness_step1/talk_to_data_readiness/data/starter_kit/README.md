# Theme 04 · Talk-to-Data Readiness Kit · Starter kit

**Intent:** As a BI lead about to switch on Copilot for business users, I want our semantic model made AI-ready and measured, so that people trust the answers from the first day.

## What's in this kit

```
model/
  data/                     CSV files for the customer's model (F_TRX, D_CUST, D_PRD, D_CAL, D_REP)
  model_definition.md       How the model is built today, problems included
glossary/business_glossary.md   Finance-approved definitions
questions/candidate_questions.csv   40 business questions; choose 25 for your eval set
templates/
  readiness_report_template.csv
  eval_results_template.csv
```

## What you build

1. Recreate the model as-is, then run your **readiness scorecard** over it: naming, descriptions, synonyms, ambiguous measures, visible keys, summarization, relationships, date handling, sensitive data.
2. Generate the missing context: descriptions, synonyms and AI instructions for tables, columns and measures (and fix what should be fixed).
3. Pick 25 questions, write the expected answer for each from the data and the glossary, and run them through Copilot or a Fabric Data Agent **before** and **after** your changes.
4. Write a short findings summary.

If Copilot or a Data Agent isn't available in your sandbox, run the same eval through any AI tool you connect to the model or its metadata, and say so in your results.

## Output contract

| File | Columns |
|---|---|
| readiness_report.csv | object, object_type, issue, severity, fix |
| model_context.json | descriptions, synonyms and instructions you generated |
| eval_results.csv | question_id, question, expected, answer_before, answer_after, pass_before, pass_after |

## How you'll be judged on proof

Answer accuracy on your eval set before and after, with each readiness issue explained.

## Ground rules

- All data in this kit is synthetic. Names, emails and identifiers are invented.
- Do not upload any customer data, and do not put credentials or secrets in prompts or code.
- Use only the approved AI tools on the provided sandbox.
- Anything that changes data or systems needs a human approval step.
- If you can't explain it in Q&A, it doesn't count.
