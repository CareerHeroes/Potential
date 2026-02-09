import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import engine


def load_flows() -> dict:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "flows.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def route_operators(inputs: dict, top_n: int) -> dict:
    scores = {
        "op.card01_state_standard": 0,
        "op.card02_resulting_valence": 0,
        "op.card03_controllability": 0,
        "op.card04_multicausality": 0,
        "op.card05_attribution": 0,
        "op.card06_identity": 0,
        "op.card07_laws_rules": 0,
        "op.card08_action_outcome": 0,
        "op.card08_1_capacity_phase": 0,
        "op.card09_thresholds": 0,
        "op.card10_transition_ambiguity": 0,
        "op.card11_learning_staircase": 0,
        "op.card12_abduction": 0,
        "op.card13_leverage": 0,
        "op.card14_pragmatic_idealism": 0,
        "op.card15_mental_immune": 0,
        "op.card16_mental_hygiene": 0,
        "op.card17_self_responsibility": 0,
        "op.card18_sufficiency": 0,
        "op.card19_goal_pyramid": 0,
        "op.card20_learning_pathways": 0
        ,
        "op.work_rule": 0,
        "op.potential_temporal": 0,
        "op.constraint_release": 0,
        "op.velocity_definition": 0,
        "op.homeostasis_clarification": 0
    }

    if inputs.get("state_is_verifiable") is False or inputs.get("standard_value") in (None, ""):
        scores["op.card01_state_standard"] += 50
    if inputs.get("procrastination_reported") is True or inputs.get("resulting_valence", 1) <= 0:
        scores["op.card02_resulting_valence"] += 40
    if inputs.get("controllability_scalar", 1) <= 0.3 or inputs.get("cites_external_factors") is True:
        scores["op.card03_controllability"] += 40
    if inputs.get("delegates_to_others") is True or inputs.get("user_causal_weight", 1) < 1:
        scores["op.card04_multicausality"] += 30
    if (
        inputs.get("attribution_locus") == "INTERNAL"
        and inputs.get("attribution_stability") == "PERMANENT"
        and inputs.get("attribution_scope") == "GLOBAL"
    ):
        scores["op.card05_attribution"] += 30
    if inputs.get("attempts_identity_change") is True and inputs.get("successful_transitions_count", 0) < inputs.get("identity_update_threshold", 1):
        scores["op.card06_identity"] += 25
    if inputs.get("constraint_type") not in (None, "LAW", "RULE"):
        scores["op.card07_laws_rules"] += 20
    if inputs.get("aor_verified") is False:
        scores["op.card08_action_outcome"] += 35
    if (
        inputs.get("action_defined") is False
        or inputs.get("success_signal_defined") is False
        or inputs.get("adaptation_defined") is False
    ):
        scores["op.card08_1_capacity_phase"] += 35
    if inputs.get("effort_correct") is True and inputs.get("input_level", 0) <= inputs.get("threshold_value", 0):
        scores["op.card09_thresholds"] += 30
    if inputs.get("transition_phase") is True and inputs.get("confusion_reported") is True:
        scores["op.card10_transition_ambiguity"] += 20
    if inputs.get("learning_stage") == 2 and inputs.get("discomfort_reported") is True:
        scores["op.card11_learning_staircase"] += 20
    if inputs.get("demands_certainty") is True:
        scores["op.card12_abduction"] += 25
    if inputs.get("resulting_valence", 1) <= 0 and inputs.get("effort", 0) > 0:
        scores["op.card13_leverage"] += 30
    if inputs.get("ideal_changed") is True:
        scores["op.card14_pragmatic_idealism"] += 25
    if inputs.get("data_rejected") is True:
        scores["op.card15_mental_immune"] += 30
    if inputs.get("borrowed_standard_removed") is False:
        scores["op.card16_mental_hygiene"] += 25
    if inputs.get("guilt_framing") is True:
        scores["op.card17_self_responsibility"] += 20
    if inputs.get("necessary_claimed") is True and inputs.get("alternative_sufficiencies_count", 0) < 3:
        scores["op.card18_sufficiency"] += 25
    if inputs.get("behavior_stuck") is True and inputs.get("higher_layer_conflict") is True:
        scores["op.card19_goal_pyramid"] += 30
    if inputs.get("fear_reported") is True and inputs.get("evidence_interpreted_as_inability") is True:
        scores["op.card20_learning_pathways"] += 20
    if inputs.get("energy_expended") is True and inputs.get("displacement_observed") is False:
        scores["op.work_rule"] += 30
    if inputs.get("internal_kinetic_spent") is True and inputs.get("capacity_increased") is True:
        scores["op.potential_temporal"] += 20
    if inputs.get("constraints_lowered") is True and inputs.get("impulsive_action_observed") is True:
        scores["op.constraint_release"] += 25
    if inputs.get("goal_defined") is False and inputs.get("motion_coherent") is False:
        scores["op.velocity_definition"] += 20
    if inputs.get("short_term_imbalance_for_long_term_stability") is True:
        scores["op.homeostasis_clarification"] += 15
    if (
        inputs.get("commitment_action_defined") is True
        and inputs.get("commitment_timeframe_defined") is True
    ):
        scores["op.conclusion_detection"] = 30

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top = [op for op, score in ranked if score > 0][:top_n]
    if not top:
        top = ["op.card01_state_standard", "op.card02_resulting_valence", "op.card03_controllability"]

    return {"operators": top, "scores": scores}


def recommend_phase(inputs: dict) -> str:
    if (
        inputs.get("potential_building_effort_low") is True
        or inputs.get("quality_impact_high") is True
        or inputs.get("user_reasoning_sound") is True
    ):
        return "BUILD_POTENTIAL"
    if (
        inputs.get("state_gap_defined") is False
        or inputs.get("aor_verified") is False
        or inputs.get("controllability_scalar", 1) < 0.4
        or inputs.get("resulting_valence", 1) <= 0
    ):
        return "BUILD_POTENTIAL"
    return "CONVERT_TO_KINETIC"


PHASE_SIGNAL_KEYS = [
    "state_gap_defined",
    "aor_verified",
    "controllability_scalar",
    "resulting_valence",
    "action_defined",
    "success_signal_defined",
    "adaptation_defined",
    "acted_recently",
    "potential_building_effort_low",
    "quality_impact_high",
    "user_reasoning_sound"
]


def phase_confidence(inputs: dict, phase: str) -> dict:
    present = [key for key in PHASE_SIGNAL_KEYS if key in inputs]
    completeness = int((len(present) / len(PHASE_SIGNAL_KEYS)) * 40)

    contradictions = 0
    if inputs.get("action_defined") is False and inputs.get("success_signal_defined") is True:
        contradictions += 1
    if inputs.get("action_defined") is False and inputs.get("adaptation_defined") is True:
        contradictions += 1
    if inputs.get("state_is_verifiable") is False and inputs.get("state_gap_defined") is True:
        contradictions += 1
    if inputs.get("procrastination_reported") is True and inputs.get("resulting_valence", 1) > 0:
        contradictions += 1
    consistency = max(0, 30 - (contradictions * 10))

    stability = 0
    prev_phase = inputs.get("phase_recommendation_prev")
    if prev_phase in ("BUILD_POTENTIAL", "CONVERT_TO_KINETIC"):
        stability = 20 if prev_phase == phase else 10

    loop_closure = 0
    if (
        inputs.get("action_defined") is True
        and inputs.get("success_signal_defined") is True
        and inputs.get("adaptation_defined") is True
    ):
        loop_closure = 10

    total = completeness + consistency + stability + loop_closure
    return {
        "score": total,
        "reasons": {
            "completeness": completeness,
            "consistency": consistency,
            "stability": stability,
            "loop_closure": loop_closure,
            "contradictions": contradictions
        }
    }


OPERATOR_INPUTS = {
    "op.card01_state_standard": [
        "state_value",
        "standard_value",
        "state_unit",
        "standard_unit",
        "state_is_verifiable"
    ],
    "op.card02_resulting_valence": [
        "attraction",
        "p_success_adj",
        "aversion",
        "p_failure",
        "cost",
        "procrastination_reported"
    ],
    "op.card03_controllability": [
        "controllability_scalar",
        "p_success",
        "cites_external_factors",
        "successful_transitions_count",
        "identity_update_threshold"
    ],
    "op.card04_multicausality": [
        "user_causal_weight",
        "delegates_to_others"
    ],
    "op.card05_attribution": [
        "attribution_locus",
        "attribution_stability",
        "attribution_scope"
    ],
    "op.card06_identity": [
        "successful_transitions_count",
        "identity_update_threshold",
        "attempts_identity_change"
    ],
    "op.card07_laws_rules": [
        "constraint_type",
        "aversion"
    ],
    "op.card08_action_outcome": [
        "aor_verified",
        "aoe_valid",
        "se_ready",
        "see_ready"
    ],
    "op.card08_1_capacity_phase": [
        "action_defined",
        "success_signal_defined",
        "adaptation_defined",
        "acted_recently"
    ],
    "op.card09_thresholds": [
        "input_level",
        "threshold_value",
        "effort_correct"
    ],
    "op.card10_transition_ambiguity": [
        "transition_phase",
        "confusion_reported"
    ],
    "op.card11_learning_staircase": [
        "learning_stage",
        "discomfort_reported"
    ],
    "op.card12_abduction": [
        "demands_certainty"
    ],
    "op.card13_leverage": [
        "displacement",
        "effort",
        "resulting_valence"
    ],
    "op.card14_pragmatic_idealism": [
        "ideal_changed"
    ],
    "op.card15_mental_immune": [
        "data_rejected"
    ],
    "op.card16_mental_hygiene": [
        "borrowed_standard_removed"
    ],
    "op.card17_self_responsibility": [
        "responsibility_framed_as_utility",
        "guilt_framing"
    ],
    "op.card18_sufficiency": [
        "necessary_claimed",
        "alternative_sufficiencies_count"
    ],
    "op.card19_goal_pyramid": [
        "behavior_stuck",
        "higher_layer_conflict"
    ],
    "op.card20_learning_pathways": [
        "fear_reported",
        "evidence_interpreted_as_inability"
    ],
    "op.conclusion_detection": [
        "commitment_action_defined",
        "commitment_timeframe_defined",
        "success_criteria_defined"
    ],
    "op.commitment_check": [
        "deadline_passed",
        "commitment_status",
        "outcome_matched"
    ],
    "op.work_rule": [
        "energy_expended",
        "displacement_observed"
    ],
    "op.potential_temporal": [
        "internal_kinetic_spent",
        "capacity_increased"
    ],
    "op.constraint_release": [
        "constraints_lowered",
        "impulsive_action_observed"
    ],
    "op.velocity_definition": [
        "goal_defined",
        "motion_coherent",
        "displacement_observed",
        "internal_motion"
    ],
    "op.homeostasis_clarification": [
        "short_term_imbalance_for_long_term_stability"
    ]
}


def missing_inputs_for(sequence: list, inputs: dict) -> dict:
    missing = {}
    for op_id in sequence:
        required = OPERATOR_INPUTS.get(op_id, [])
        missing_keys = [key for key in required if key not in inputs]
        if missing_keys:
            missing[op_id] = missing_keys
    return missing


class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_HEAD(self):
        if self.path in ("/", "/health"):
            self._set_headers(200)
            return
        self._set_headers(404)

    def do_GET(self):
        if self.path in ("/", "/health"):
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))

    def do_POST(self):
        if self.path not in ("/evaluate", "/route", "/route_and_evaluate", "/commitment_check"):
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "invalid json"}).encode("utf-8"))
            return

        inputs = payload.get("inputs") or {}
        if not isinstance(inputs, dict):
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "inputs must be object"}).encode("utf-8"))
            return

        if self.path == "/route":
            top_n = payload.get("top_n", 3)
            if not isinstance(top_n, int) or top_n <= 0:
                top_n = 3

            result = route_operators(inputs, top_n)
            self._set_headers(200)
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        if self.path == "/commitment_check":
            sequence = ["op.commitment_check"]
            case_id = payload.get("case_id", "commitment_case")
            missing = missing_inputs_for(sequence, inputs)
            if missing:
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "NEEDS_INPUTS", "missing_inputs": missing}).encode("utf-8"))
                return

            base_dir = os.path.dirname(os.path.abspath(__file__))
            operators_dir = os.path.join(base_dir, "operators")
            try:
                result = engine.run_inputs(case_id, inputs, sequence, operators_dir)
            except Exception as exc:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
                return

            self._set_headers(200)
            self.wfile.write(json.dumps({"result": result}).encode("utf-8"))
            return

        if self.path == "/route_and_evaluate":
            top_n = payload.get("top_n", 3)
            if not isinstance(top_n, int) or top_n <= 0:
                top_n = 3
            routed = route_operators(inputs, top_n)
            phase = recommend_phase(inputs)
            confidence = phase_confidence(inputs, phase)
            sequence = routed.get("operators", [])
            case_id = payload.get("case_id", "api_case")

            if not sequence:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "routing returned empty operator list"}).encode("utf-8"))
                return

            missing = missing_inputs_for(sequence, inputs)
            if missing:
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "status": "NEEDS_INPUTS",
                    "route": routed,
                    "phase_recommendation": phase,
                    "phase_confidence": confidence,
                    "missing_inputs": missing
                }).encode("utf-8"))
                return

            base_dir = os.path.dirname(os.path.abspath(__file__))
            operators_dir = os.path.join(base_dir, "operators")
            try:
                result = engine.run_inputs(case_id, inputs, sequence, operators_dir)
            except Exception as exc:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
                return

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "route": routed,
                "phase_recommendation": phase,
                "phase_confidence": confidence,
                "result": result
            }).encode("utf-8"))
            return

        sequence = payload.get("operator_sequence")
        flow_id = payload.get("flow_id")
        case_id = payload.get("case_id", "api_case")

        flows = load_flows()
        if not sequence and flow_id:
            sequence = flows.get(flow_id)

        if not isinstance(sequence, list) or not sequence:
            self._set_headers(400)
            self.wfile.write(
                json.dumps({"error": "inputs must be object and operator_sequence must be non-empty list"}).encode("utf-8")
            )
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        operators_dir = os.path.join(base_dir, "operators")

        try:
            result = engine.run_inputs(case_id, inputs, sequence, operators_dir)
        except Exception as exc:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
            return

        self._set_headers(200)
        self.wfile.write(json.dumps(result).encode("utf-8"))


def main():
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
