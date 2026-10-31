"""Supported maintenance item kinds and field requirements per category."""

from enum import StrEnum


class MaintenanceCategory(StrEnum):
    HOME = "home"
    AUTO = "auto"
    ITEMS = "items"


class MaintenanceItemKind(StrEnum):
    HVAC_FILTER = "hvac_filter"
    WATER_FILTER = "water_filter"
    SMOKE_DETECTOR = "smoke_detector"
    OIL_CHANGE = "oil_change"
    TIRE_ROTATION = "tire_rotation"
    GENERIC_HOME = "generic_home"
    GENERIC_AUTO = "generic_auto"
    CONSUMABLE = "consumable"


KINDS_BY_CATEGORY: dict[MaintenanceCategory, set[MaintenanceItemKind]] = {
    MaintenanceCategory.HOME: {
        MaintenanceItemKind.HVAC_FILTER,
        MaintenanceItemKind.WATER_FILTER,
        MaintenanceItemKind.SMOKE_DETECTOR,
        MaintenanceItemKind.GENERIC_HOME,
    },
    MaintenanceCategory.AUTO: {
        MaintenanceItemKind.OIL_CHANGE,
        MaintenanceItemKind.TIRE_ROTATION,
        MaintenanceItemKind.GENERIC_AUTO,
    },
    MaintenanceCategory.ITEMS: {MaintenanceItemKind.CONSUMABLE},
}


def default_interval_days(
    category: MaintenanceCategory, item_kind: MaintenanceItemKind
) -> int | None:
    if item_kind is MaintenanceItemKind.HVAC_FILTER:
        return 90
    if item_kind is MaintenanceItemKind.WATER_FILTER:
        return 180
    if item_kind is MaintenanceItemKind.SMOKE_DETECTOR:
        return 365
    if item_kind is MaintenanceItemKind.OIL_CHANGE:
        return 180
    if item_kind is MaintenanceItemKind.TIRE_ROTATION:
        return 180
    if category is MaintenanceCategory.HOME:
        return 90
    return None


def default_interval_miles(item_kind: MaintenanceItemKind) -> int | None:
    if item_kind is MaintenanceItemKind.OIL_CHANGE:
        return 5000
    if item_kind is MaintenanceItemKind.TIRE_ROTATION:
        return 7500
    return None


def requires_mileage_fields(item_kind: MaintenanceItemKind) -> bool:
    return item_kind in {
        MaintenanceItemKind.OIL_CHANGE,
        MaintenanceItemKind.TIRE_ROTATION,
        MaintenanceItemKind.GENERIC_AUTO,
    }
