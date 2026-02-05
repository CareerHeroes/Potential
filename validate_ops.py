import json
import os
import sys


REQUIRED_KEYS = {"id", "name", "rules", "gates"}


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_operator(path: str) -> list:
    errors = []
    try:
        op = load_json(path)
    except Exception as exc:
        return [f"{path}: failed to load JSON ({exc})"]

    missing = REQUIRED_KEYS - set(op.keys())
    if missing:
        errors.append(f"{path}: missing keys {sorted(missing)}")

    rules = op.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append(f"{path}: rules must be a non-empty list")

    gates = op.get("gates")
    if not isinstance(gates, list):
        errors.append(f"{path}: gates must be a list")

    return errors


def main() -> int:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    operators_dir = os.path.join(base_dir, "operators")

    errors = []
    for fname in sorted(os.listdir(operators_dir)):
        if fname.endswith(".json"):
            errors.extend(validate_operator(os.path.join(operators_dir, fname)))

    if errors:
        print("Operator validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("All operators valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
