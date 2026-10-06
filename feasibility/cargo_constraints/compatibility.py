def compatible(first, second):
    if not first.consolidation_allowed or not second.consolidation_allowed:
        return False
    if (
        second.cargo_type in first.prohibited_co_load_categories
        or first.cargo_type in second.prohibited_co_load_categories
    ):
        return False
    if (
        first.hazardous != second.hazardous
        or first.temperature_control_required != second.temperature_control_required
    ):
        return False
    if (
        first.cargo_type in {"cement", "construction"}
        and second.cargo_type in {"rice", "food"}
    ) or (
        second.cargo_type in {"cement", "construction"}
        and first.cargo_type in {"rice", "food"}
    ):
        return False
    return True
