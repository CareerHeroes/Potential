import json
import os
import sys

import engine


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def matches_expected(result: dict, expected: dict) -> bool:
    if not expected:
        return True
    exp_status = expected.get("status")
    if exp_status and exp_status != result.get("status"):
        return False
    exp_state = expected.get("state", {})
    for key, value in exp_state.items():
        if result.get("state", {}).get(key) != value:
            return False
    return True


def main() -> int:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cases_dir = os.path.join(base_dir, "cases")
    operators_dir = os.path.join(base_dir, "operators")

    case_files = sorted(
        fname for fname in os.listdir(cases_dir) if fname.endswith(".json")
    )

    total = 0
    ok = 0
    gated = 0
    fail = 0

    for fname in case_files:
        total += 1
        path = os.path.join(cases_dir, fname)
        case = load_json(path)
        expected = case.get("expected", {})

        result = engine.run_case(path, operators_dir)
        status = result.get("status")

        if not matches_expected(result, expected):
            print(f"[FAIL] {fname}")
            fail += 1
            continue

        if status == "GATED":
            print(f"[GATED] {fname}")
            gated += 1
        else:
            print(f"[OK] {fname}")
            ok += 1

    print(f"Summary: total={total} ok={ok} gated={gated} fail={fail}")
    return 1 if fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
