def normalize_list(values: list[str]) -> set[str]:
    return {value.strip().lower() for value in values if value.strip()}


def equipment_is_approved(equipment: str, approved_equipment: list[str]) -> bool:
    return equipment.strip().lower() in normalize_list(approved_equipment)


def commodity_is_approved(commodity: str, approved_commodities: list[str]) -> bool:
    return commodity.strip().lower() in normalize_list(approved_commodities)


def approval_reasons(
    equipment: str,
    commodity: str,
    approved_equipment: list[str],
    approved_commodities: list[str],
) -> list[str]:
    reasons: list[str] = []
    if not equipment_is_approved(equipment, approved_equipment):
        reasons.append("equipment not approved")
    if not commodity_is_approved(commodity, approved_commodities):
        reasons.append("commodity not approved")
    return reasons
