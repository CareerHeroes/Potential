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
        inputs.get("attribution_universal_helplessness") is True
        or inputs.get("attribution_action_outcome_preserved") is False
        or inputs.get("attribution_learnable_component") is False
        or (
            inputs.get("attribution_locus") in ("EXTERNAL", "INTERACTIONAL")
            and inputs.get("attribution_conditionality_defined") is False
        )
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
        "attribution_scope",
        "attribution_universal_helplessness",
        "attribution_conditionality_defined",
        "attribution_action_outcome_preserved",
        "attribution_learnable_component"
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


_PREV_SCORES = {}


def _provided_set(payload: dict, inputs: dict) -> set:
    provided = payload.get("inputs_provided")
    if isinstance(provided, list):
        return set(provided)
    return set(inputs.keys())


def _cap(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def compute_energy(inputs: dict, provided: set, gates_count: int, status: str) -> dict:
    potential = 0.0

    # State clarity (max 25)
    if "state_is_verifiable" in provided and inputs.get("state_is_verifiable") is True:
        potential += 15
    if "standard_value" in provided and inputs.get("standard_value") not in (None, ""):
        potential += 10

    # Controllability (max 35)
    if "controllability_scalar" in provided:
        potential += _cap(float(inputs.get("controllability_scalar", 0)) * 20, 0, 20)
    if "user_causal_weight" in provided:
        potential += _cap(float(inputs.get("user_causal_weight", 0)) * 10, 0, 10)
    # Identity capacity (max 10)
    if "attempts_identity_change" in provided and inputs.get("attempts_identity_change") is True:
        potential += 3
    if "successful_transitions_count" in provided:
        potential += _cap(float(inputs.get("successful_transitions_count", 0)) * 2, 0, 7)

    # AoR verified (max 5)
    if "aor_verified" in provided and inputs.get("aor_verified") is True:
        potential += 5

    # No blockers bonus (max 5)
    if (
        "fear_reported" in provided
        and "behavior_stuck" in provided
        and inputs.get("fear_reported") is False
        and inputs.get("behavior_stuck") is False
    ):
        potential += 5

    # Temporal rule bonus (max 8)
    if "internal_kinetic_spent" in provided:
        if inputs.get("internal_kinetic_spent") is True and inputs.get("capacity_increased") is True:
            potential += 8
        elif inputs.get("internal_kinetic_spent") is True:
            potential += 3

    # Velocity bonus (max 5)
    if "goal_defined" in provided and inputs.get("goal_defined") is True:
        potential += 5

    potential = _cap(potential)

    utilization = 0.0
    # Effort (max 30)
    if "effort_correct" in provided and inputs.get("effort_correct") is True:
        utilization += 10
    if "input_level" in provided:
        utilization += _cap(float(inputs.get("input_level", 0)) / 100 * 10, 0, 10)
    if "effort" in provided:
        utilization += _cap(float(inputs.get("effort", 0)) / 100 * 10, 0, 10)

    # Valence (max 25)
    if "resulting_valence" in provided:
        utilization += _cap((float(inputs.get("resulting_valence", 0)) + 1) / 2 * 25, 0, 25)

    # Learning stage (max 12)
    if "learning_stage" in provided:
        utilization += _cap(float(inputs.get("learning_stage", 0)) / 5 * 12, 0, 12)

    # Blocker absence (max 25)
    if "behavior_stuck" in provided and inputs.get("behavior_stuck") is False:
        utilization += 7
    if "procrastination_reported" in provided and inputs.get("procrastination_reported") is False:
        utilization += 6
    if "fear_reported" in provided and inputs.get("fear_reported") is False:
        utilization += 6
    if "confusion_reported" in provided and inputs.get("confusion_reported") is False:
        utilization += 6

    # Transition (max 8)
    if "transition_phase" in provided and inputs.get("transition_phase") is True:
        utilization += 5
    if "demands_certainty" in provided and inputs.get("demands_certainty") is False:
        utilization += 3

    # Penalties
    if (
        "energy_expended" in provided
        and "displacement_observed" in provided
        and inputs.get("energy_expended") is True
        and inputs.get("displacement_observed") is False
    ):
        utilization -= 10
    if (
        "goal_defined" in provided
        and "motion_coherent" in provided
        and inputs.get("goal_defined") is True
        and inputs.get("motion_coherent") is True
    ):
        utilization += 10
    if (
        "internal_motion" in provided
        and "motion_coherent" in provided
        and inputs.get("internal_motion") is True
        and inputs.get("motion_coherent") is False
    ):
        utilization -= 5
    if (
        "impulsive_action_observed" in provided
        and "constraints_lowered" in provided
        and inputs.get("impulsive_action_observed") is True
        and inputs.get("constraints_lowered") is True
    ):
        utilization -= 5
    if "short_term_imbalance_for_long_term_stability" in provided and inputs.get("short_term_imbalance_for_long_term_stability") is True:
        utilization += 5

    # Gate penalties
    if gates_count > 0:
        utilization -= (gates_count * 15)

    utilization = _cap(utilization)

    # Constraint: utilization cannot exceed potential
    utilization = min(utilization, potential)

    gap = _cap(potential - utilization)
    ready_to_act = bool(utilization >= 55 and status != "GATED" and gap < 35)

    return {
        "potential": int(round(potential)),
        "utilization": int(round(utilization)),
        "gap": int(round(gap)),
        "ready_to_act": ready_to_act
    }


def apply_ema(case_id: str, energy: dict) -> dict:
    if not case_id:
        return energy
    prev = _PREV_SCORES.get(case_id)
    if not prev:
        _PREV_SCORES[case_id] = energy
        return energy
    blended = {}
    for key in ("potential", "utilization", "gap"):
        blended[key] = int(round(0.4 * energy[key] + 0.6 * prev.get(key, energy[key])))
    blended["ready_to_act"] = bool(blended["utilization"] >= 55 and blended["gap"] < 35)
    _PREV_SCORES[case_id] = blended
    return blended


def identify_fulcrums(inputs: dict, provided: set) -> list:
    candidates = []

    if (
        "energy_expended" in provided
        and "displacement_observed" in provided
        and inputs.get("energy_expended") is True
        and inputs.get("displacement_observed") is False
    ):
        candidates.append({
            "id": "work_rule",
            "label": "No Displacement",
            "description": "Energy is being spent without changing the external state.",
            "impact": "high",
            "action_hint": "What threshold is blocking displacement right now?"
        })

    if (
        "goal_defined" in provided
        and "motion_coherent" in provided
        and (inputs.get("goal_defined") is False or inputs.get("motion_coherent") is False)
    ):
        candidates.append({
            "id": "velocity",
            "label": "Lack of Direction",
            "description": "Activity exists without a coherent goal or direction.",
            "impact": "high",
            "action_hint": "What is the specific goal this motion should serve?"
        })

    for key, label, hint in [
        ("fear_reported", "Fear Constraint", "What signal would reduce this fear?"),
        ("behavior_stuck", "Stuck Loop", "What is one smallest move that breaks the loop?"),
        ("procrastination_reported", "Procrastination", "What would make starting easier today?"),
        ("impulsive_action_observed", "Impulsivity", "What constraint needs stabilizing first?")
    ]:
        if key in provided and inputs.get(key) is True:
            candidates.append({
                "id": key,
                "label": label,
                "description": "Behavioral blocker is reducing effective motion.",
                "impact": "medium",
                "action_hint": hint
            })

    if "controllability_scalar" in provided and float(inputs.get("controllability_scalar", 1)) < 0.4:
        candidates.append({
            "id": "controllability",
            "label": "Sense of Agency",
            "description": "You feel limited in how much you can influence the outcome.",
            "impact": "medium",
            "action_hint": "What is one thing you can change right now, even if small?"
        })
    if (
        ("attribution_universal_helplessness" in provided and inputs.get("attribution_universal_helplessness") is True)
        or ("attribution_action_outcome_preserved" in provided and inputs.get("attribution_action_outcome_preserved") is False)
        or ("attribution_learnable_component" in provided and inputs.get("attribution_learnable_component") is False)
        or (
            "attribution_conditionality_defined" in provided
            and "attribution_locus" in provided
            and inputs.get("attribution_locus") in ("EXTERNAL", "INTERACTIONAL")
            and inputs.get("attribution_conditionality_defined") is False
        )
    ):
        candidates.append({
            "id": "attribution",
            "label": "Attribution Failure",
            "description": "Attribution removes individual learning pathways or action–outcome linkage.",
            "impact": "medium",
            "action_hint": "Identify a learnable skill, strategy, or behavior you can change."
        })

    if (
        ("state_is_verifiable" in provided and inputs.get("state_is_verifiable") is False)
        or ("standard_value" in provided and inputs.get("standard_value") in (None, ""))
    ):
        candidates.append({
            "id": "clarity_gap",
            "label": "Clarity Gap",
            "description": "The current state or standard is not yet clear.",
            "impact": "low",
            "action_hint": "State the current facts and the exact standard you are using."
        })

    priority = [
        "work_rule",
        "velocity",
        "fear_reported",
        "behavior_stuck",
        "procrastination_reported",
        "impulsive_action_observed",
        "controllability",
        "attribution",
        "clarity_gap"
    ]
    candidates.sort(key=lambda item: priority.index(item["id"]) if item["id"] in priority else 99)
    return candidates[:3]


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
        provided = _provided_set(payload, inputs)

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
                energy = compute_energy(inputs, provided, 0, "NEEDS_INPUTS")
                energy = apply_ema(case_id, energy)
                fulcrums = identify_fulcrums(inputs, provided)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "status": "NEEDS_INPUTS",
                    "route": routed,
                    "phase_recommendation": phase,
                    "phase_confidence": confidence,
                    "missing_inputs": missing,
                    "computed_energy": energy,
                    "fulcrums": fulcrums
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

            gates_count = len(result.get("gates_triggered", []))
            energy = compute_energy(inputs, provided, gates_count, result.get("status"))
            energy = apply_ema(case_id, energy)
            fulcrums = identify_fulcrums(inputs, provided)
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "route": routed,
                "phase_recommendation": phase,
                "phase_confidence": confidence,
                "result": result,
                "computed_energy": energy,
                "fulcrums": fulcrums
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
