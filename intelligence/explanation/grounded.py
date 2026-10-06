def explain_failures(feasibility):
    """Display engine evidence verbatim; an LLM cannot rewrite a FAIL as a PASS."""
    return {
        "status": feasibility["status"],
        "reasons": feasibility["reasons"],
        "source": feasibility["provenance"],
    }
