import json
import os
import sys
import ast
import re
from typing import Any, Dict, List


ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Call,
    ast.Load,
    ast.Name,
    ast.Constant,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Attribute,
    ast.Subscript,
    ast.Index,   # older python
    ast.Slice,
    ast.List,
    ast.Tuple,
    ast.Dict,
)


def safe_eval(expr: str, env: Dict[str, Any]) -> Any:
    """
    Safely evaluate a restricted expression used in operator rules.
    Allowed: boolean logic, comparisons, arithmetic, len(), dict/list access.
    """
    expr = expr.strip()
    expr = re.sub(r"\btrue\b", "True", expr)
    expr = re.sub(r"\bfalse\b", "False", expr)
    expr = re.sub(r"\bnull\b", "None", expr)

    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ValueError(f"Disallowed expression node: {type(node).__name__}")
        if isinstance(node, ast.Call):
            # allow only len(...)
            if not isinstance(node.func, ast.Name) or node.func.id != "len":
                raise ValueError("Only len(...) calls are allowed.")
    compiled = compile(tree, "<rule>", "eval")
    return eval(compiled, {"__builtins__": {}}, {"len": len, **env})


def deep_get(d: Dict[str, Any], path: str) -> Any:
    """
    Get nested dict value by dotted path, e.g. 'evidence.job_coaching.recent_client_inquiries'
    """
    cur: Any = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def merge_env(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    out.update(updates)
    return out


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_operator(op_id: str, operators_dir: str) -> Dict[str, Any]:
    # Operator files named by id, but easier: keep one file per operator and map by filename.
    # We'll scan all and match `id`.
    for fname in os.listdir(operators_dir):
        if fname.endswith(".json"):
            op = load_json(os.path.join(operators_dir, fname))
            if op.get("id") == op_id:
                return op
    raise FileNotFoundError(f"Operator not found: {op_id}")


def apply_rules(op: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
    outputs = {}
    matched = False
    for rule in op.get("rules", []):
        cond = rule.get("when", "true")
        if cond.strip().lower() == "true":
            ok = True
        else:
            ok = bool(safe_eval(cond, env))
        if ok:
            outputs.update(rule.get("set", {}))
            set_expr = rule.get("set_expr", {})
            if isinstance(set_expr, dict):
                for key, expr in set_expr.items():
                    outputs[key] = safe_eval(str(expr), env)
            matched = True
            # first-match-wins for determinism
            break
    if not matched:
        # If no rule matches, outputs remain empty (still deterministic)
        pass
    return outputs


def check_gates(op: Dict[str, Any], env: Dict[str, Any]) -> List[Dict[str, Any]]:
    triggered = []
    for gate in op.get("gates", []):
        cond = gate.get("when", "false")
        if cond.strip().lower() == "true":
            ok = True
        else:
            ok = bool(safe_eval(cond, env))
        if ok:
            triggered.append({
                "id": gate.get("id"),
                "action": gate.get("action"),
                "message": gate.get("message")
            })
    return triggered


def build_env(case_inputs: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the environment visible to rules:
    - top-level case inputs
    - outputs accumulated in state
    - convenience variables
    """
    env = {}
    env.update(case_inputs)
    env.update(state)

    # Convenience: flatten some nested values for rule simplicity
    # Evidence shortcuts:
    env["jc_inquiries"] = deep_get(case_inputs, "evidence.job_coaching.recent_client_inquiries") or 0
    env["tool_paying_users"] = deep_get(case_inputs, "evidence.tool_development.paying_users") or 0
    env["runway_months"] = deep_get(case_inputs, "personal_constraints.financial_runway_months") or 0
    env["hours_per_week"] = deep_get(case_inputs, "personal_constraints.available_hours_per_week") or 0

    # Assumptions lists:
    env["jc_assumptions"] = deep_get(case_inputs, "assumptions.job_coaching") or []
    env["tool_assumptions"] = deep_get(case_inputs, "assumptions.tool_development") or []

    return env


def run_case(case_path: str, operators_dir: str) -> Dict[str, Any]:
    case = load_json(case_path)
    case_inputs = case.get("inputs", {})
    sequence = case.get("operator_sequence", [])

    state: Dict[str, Any] = {}   # accumulated outputs
    gate_log: List[Dict[str, Any]] = []
    op_log: List[Dict[str, Any]] = []

    for op_id in sequence:
        op = load_operator(op_id, operators_dir)
        env = build_env(case_inputs, state)

        out = apply_rules(op, env)
        state.update(out)

        env2 = build_env(case_inputs, state)
        gates = check_gates(op, env2)

        op_log.append({
            "operator": op_id,
            "outputs": out
        })

        if gates:
            gate_log.extend([{"operator": op_id, **g} for g in gates])
            # deterministic stop if any gate says BLOCK_PROGRESS or REQUIRE_COMMITMENT
            stop_actions = {"BLOCK_PROGRESS", "REQUIRE_COMMITMENT"}
            if any(g["action"] in stop_actions for g in gates):
                return {
                    "case_id": case.get("case_id"),
                    "status": "GATED",
                    "state": state,
                    "operators_ran": op_log,
                    "gates_triggered": gate_log
                }

    return {
        "case_id": case.get("case_id"),
        "status": "OK",
        "state": state,
        "operators_ran": op_log,
        "gates_triggered": gate_log
    }


def run_inputs(case_id: str, case_inputs: Dict[str, Any], sequence: List[str], operators_dir: str) -> Dict[str, Any]:
    state: Dict[str, Any] = {}
    gate_log: List[Dict[str, Any]] = []
    op_log: List[Dict[str, Any]] = []

    for op_id in sequence:
        op = load_operator(op_id, operators_dir)
        env = build_env(case_inputs, state)

        out = apply_rules(op, env)
        state.update(out)

        env2 = build_env(case_inputs, state)
        gates = check_gates(op, env2)

        op_log.append({
            "operator": op_id,
            "outputs": out
        })

        if gates:
            gate_log.extend([{"operator": op_id, **g} for g in gates])
            stop_actions = {"BLOCK_PROGRESS", "REQUIRE_COMMITMENT"}
            if any(g["action"] in stop_actions for g in gates):
                return {
                    "case_id": case_id,
                    "status": "GATED",
                    "state": state,
                    "operators_ran": op_log,
                    "gates_triggered": gate_log
                }

    return {
        "case_id": case_id,
        "status": "OK",
        "state": state,
        "operators_ran": op_log,
        "gates_triggered": gate_log
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 engine.py cases/case_x.json")
        sys.exit(1)

    case_path = sys.argv[1]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    operators_dir = os.path.join(base_dir, "operators")

    result = run_case(case_path, operators_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
