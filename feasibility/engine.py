from optimization.terminal_selection.planner import choose_terminals


def check_feasibility(db, cargo, vessel, **kwargs):
    result = choose_terminals(db, cargo, vessel, **kwargs)
    return {
        "passed": result["passed"],
        "status": "PASS" if result["passed"] else "FAIL",
        "reasons": result["reasons"],
        "plan": result.get("best_plan"),
        "terminal_options": result["plans"],
        "provenance": {
            "source_name": "Synthetic operational fixture",
            "source_date": "2026-10-06",
            "verification_status": "SIMULATED",
            "last_verified": None,
        },
    }
