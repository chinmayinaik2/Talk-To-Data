
from engine.benchmark_engine import (
    load_benchmark_questions,
    evaluate_all_benchmarks,
    get_benchmark_summary,
    save_benchmark_report
)


# 1. Verify benchmark questions.
questions = load_benchmark_questions()

print("Total benchmark questions:", len(questions))

print("\nQuestions by model:")
print(questions["model"].value_counts())


# 2. Evaluate all three models.
results = evaluate_all_benchmarks()

print("\n" + "=" * 60)
print("BENCHMARK RESULTS")
print("=" * 60)

for model_name in ["Finance", "Sales", "HR"]:

    model_results = results[
        results["model"] == model_name
    ]

    summary = get_benchmark_summary(
        model_results
    )

    print(f"\nMODEL: {model_name}")
    print("-" * 40)

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nIndividual questions:")

    print(
        model_results[
            [
                "question_id",
                "question",
                "computed_result",
                "assessment_reasons"
            ]
        ].to_string(index=False)
    )


# 3. Save benchmark report.
save_benchmark_report(
    results,
    "reports/benchmark_results.csv"
)


assert len(results) == 25

assert results["computed_result"].isin([
    "Likely supported",
    "Needs validation",
    "Gap detected"
]).all()

assert results["question_id"].is_unique

print("\nALL BENCHMARK ENGINE TESTS PASSED!")
