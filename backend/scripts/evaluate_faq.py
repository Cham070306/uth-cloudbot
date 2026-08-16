"""Evaluate local FAQ retrieval without calling Gemini or Firestore."""
import json
import sys
from pathlib import Path

from services.faq_service import find_faq


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data/evaluation/faq_questions.json"
MIN_ACCURACY = 0.85


def evaluate(dataset=DATASET):
    cases = json.loads(Path(dataset).read_text(encoding="utf-8"))["cases"]
    incorrect = []
    for case in cases:
        match = find_faq(case["message"])
        actual = match["id"] if match else None
        if actual != case["expected_faq_id"]:
            incorrect.append({
                "id": case["id"],
                "message": case["message"],
                "expected": case["expected_faq_id"],
                "actual": actual,
            })
    correct = len(cases) - len(incorrect)
    accuracy = correct / len(cases) if cases else 0.0
    return {"total": len(cases), "correct": correct, "incorrect": incorrect, "accuracy": accuracy}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = evaluate()
    print(f"Total cases: {result['total']}")
    print(f"Correct cases: {result['correct']}")
    print(f"Incorrect cases: {len(result['incorrect'])}")
    print(f"Accuracy: {result['accuracy']:.2%}")
    if result["incorrect"]:
        print("Incorrect case details:")
        for item in result["incorrect"]:
            print(
                f"- {item['id']}: expected={item['expected']} actual={item['actual']} "
                f"message={item['message']!r}"
            )
    return 0 if result["accuracy"] >= MIN_ACCURACY else 1


if __name__ == "__main__":
    raise SystemExit(main())
