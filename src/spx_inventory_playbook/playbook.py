"""Compact static operational playbook tables."""

from dataclasses import dataclass
from enum import Enum


class Permission(Enum):
    ALLOWED = "allowed"
    RESTRICTED = "restricted"
    FORBIDDEN = "forbidden"
    CLOSE_ONLY = "close_only"
    HEDGE_ONLY = "hedge_only"
    PREPLANNED_ONLY = "preplanned_only"


@dataclass(frozen=True)
class ActionPermissionRow:
    action: str
    generally_allowed: str
    allowed_only_with_evidence: str
    restricted: str
    forbidden: str
    always_forbidden_if: str


@dataclass(frozen=True)
class StructureQuickReferenceRow:
    structure: str
    favorable_response: str
    unfavorable_response: str
    usually_valid_adjustment: str
    usually_wrong_adjustment: str
    clean_close_trigger: str


@dataclass(frozen=True)
class ConversionTriageRow:
    starting_position: str
    conversion_candidate: str
    valid_only_if: str
    reject_if: str
    closing_superior_when: str


@dataclass(frozen=True)
class TimeOfDayPermissionRow:
    action: str
    open_930_945: Permission
    morning_945_1030: Permission
    late_morning_1030_1200: Permission
    midday_1200_1330: Permission
    early_afternoon_1330_1430: Permission
    late_afternoon_1430_1515: Permission
    final_hour_1515_1545: Permission
    final_15_1545_1555: Permission
    final_5_1555_1600: Permission
    note: str


def get_action_permission_matrix() -> list[ActionPermissionRow]:
    return [
        ActionPermissionRow(
            "Hold",
            "Yes",
            "Thesis intact; risk inside plan.",
            "Late day or size breach.",
            "Invalidation accepted.",
            "Behavior impaired and hold avoids loss acceptance.",
        ),
        ActionPermissionRow(
            "Take partial profit",
            "Yes",
            "Profit exists and remaining risk is planned.",
            "Poor liquidity or final minutes.",
            "If it adds complexity.",
            "Used to avoid the planned exit.",
        ),
        ActionPermissionRow(
            "Scale out",
            "Yes",
            "Exposure reduction is explicit.",
            "Final five minutes.",
            "If it increases residual risk.",
            "Behavior impaired and sizing is unclear.",
        ),
        ActionPermissionRow(
            "Reduce losing position",
            "Yes",
            "Loss remains inside plan.",
            "Use simpler order under poor liquidity.",
            "If reduction adds risk.",
            "Never replace reduction with loss repair.",
        ),
        ActionPermissionRow(
            "Close fully",
            "Yes",
            "Any time risk or thesis fails.",
            "Only by liquidity and order control.",
            "Never forbidden by playbook.",
            "N/A",
        ),
        ActionPermissionRow(
            "Hedge with MES/ES",
            "Yes",
            "Temporary delta control is required.",
            "Must have exit condition.",
            "If it becomes a second thesis.",
            "Used to avoid closing invalid inventory.",
        ),
        ActionPermissionRow(
            "Add to winner",
            "Restricted",
            "Risk budget remains unused.",
            "Avoid late day and poor liquidity.",
            "If size exceeds plan.",
            "Behavior impaired or adds unmanaged gamma.",
        ),
        ActionPermissionRow(
            "Add to loser",
            "No",
            "Never for loss repair.",
            "N/A",
            "Default forbidden.",
            "Loss repair, thesis invalid, or size over plan.",
        ),
        ActionPermissionRow(
            "Convert long option to vertical",
            "Restricted",
            "Lock risk or harvest remaining edge.",
            "Poor liquidity or final hour.",
            "If closing is cleaner.",
            "Behavior impaired or thesis invalid.",
        ),
        ActionPermissionRow(
            "Convert long option to butterfly",
            "Restricted",
            "Pin thesis and time remain.",
            "After 14:30 or wings illiquid.",
            "If close is simpler.",
            "Behavior impaired, late day, or loss repair.",
        ),
        ActionPermissionRow(
            "Convert debit spread to butterfly",
            "Restricted",
            "Center and max-loss improve.",
            "Only with clear width control.",
            "If it hides a failed thesis.",
            "Closing is cleaner or wings are thin.",
        ),
        ActionPermissionRow(
            "Convert debit spread to broken-wing butterfly",
            "Restricted",
            "Tail risk is reduced, not shifted.",
            "Wing liquidity weak after 14:00.",
            "If new tail is unmanaged.",
            "Stress widening or loss repair.",
        ),
        ActionPermissionRow(
            "Convert credit spread to iron condor",
            "Restricted",
            "Adds opposite risk only inside plan.",
            "Avoid when short gamma grows.",
            "If it doubles theta hope.",
            "Final hour, stress, or behavior impaired.",
        ),
        ActionPermissionRow(
            "Convert credit spread to iron fly",
            "Restricted",
            "Only if risk shrinks and center is planned.",
            "ATM short gamma needs time stop.",
            "If theta is the sole reason.",
            "Final hour or close-by-time breached.",
        ),
        ActionPermissionRow(
            "Recenter butterfly",
            "Restricted",
            "Center shift reduces risk.",
            "Wing liquidity decays after 14:00.",
            "If it chases price.",
            "Final 30 minutes or loss repair.",
        ),
        ActionPermissionRow(
            "Remove one side of iron condor",
            "Restricted",
            "Removes tested risk.",
            "Leaves directional inventory.",
            "If it creates new naked thesis.",
            "Behavior impaired or unplanned delta.",
        ),
        ActionPermissionRow(
            "Flatten delta",
            "Yes",
            "Delta is unintended.",
            "Prefer temporary futures hedge.",
            "If hedge lacks stop condition.",
            "Used to add a second view.",
        ),
        ActionPermissionRow(
            "Roll strike",
            "Restricted",
            "Reduces risk and preserves plan.",
            "Poor liquidity or late day.",
            "If rolling a loss.",
            "Loss repair, stress, or final 30 minutes.",
        ),
        ActionPermissionRow(
            "Widen spread",
            "No",
            "Rare; only preplanned risk reduction.",
            "Stress widening is forbidden.",
            "Default under pressure.",
            "Stress, poor liquidity, or loss repair.",
        ),
        ActionPermissionRow(
            "Stop trading",
            "Yes",
            "Rule breach or lockout.",
            "N/A",
            "Never forbidden by playbook.",
            "N/A",
        ),
    ]


def get_structure_quick_reference() -> list[StructureQuickReferenceRow]:
    return [
        StructureQuickReferenceRow(
            "Long call / long put",
            "Hold or partial if thesis intact.",
            "Reduce or close on invalidation.",
            "Vertical only to reduce risk.",
            "Average down after thesis failure.",
            "Time decay dominates or thesis breaks.",
        ),
        StructureQuickReferenceRow(
            "Call debit spread / put debit spread",
            "Scale or hold while target remains live.",
            "Close when spread cannot pay.",
            "Fly only if center risk improves.",
            "Roll loss to delay close.",
            "Max reward no longer compensates time.",
        ),
        StructureQuickReferenceRow(
            "Call credit spread / put credit spread",
            "Take risk down when favorable.",
            "Close or hedge if short gamma accelerates.",
            "Futures hedge can beat option repair.",
            "Add opposite premium late.",
            "Tested short near close-by-time.",
        ),
        StructureQuickReferenceRow(
            "Standard butterfly",
            "Hold only while center remains valid.",
            "Close if price exits useful range.",
            "Small recenter before wing liquidity decays.",
            "Chase center late.",
            "Center thesis fails or wings thin.",
        ),
        StructureQuickReferenceRow(
            "Broken-wing butterfly",
            "Hold if tail risk remains planned.",
            "Reduce if broken wing becomes active risk.",
            "Close tail before liquidity fades.",
            "Widen broken side under stress.",
            "Tail risk exceeds plan.",
        ),
        StructureQuickReferenceRow(
            "Iron fly",
            "Reduce while center holds.",
            "Close if ATM short gamma expands.",
            "Temporary futures hedge before close.",
            "Hold for theta after time stop.",
            "Close-by-time or center breach.",
        ),
        StructureQuickReferenceRow(
            "Iron condor",
            "Harvest only while both sides safe.",
            "Remove or close tested side.",
            "One-side removal if delta is planned.",
            "Add new side to repair tested side.",
            "Tested side loses plan control.",
        ),
        StructureQuickReferenceRow(
            "Ratio/backspread restricted",
            "Only hold if tail plan is explicit.",
            "Close if convexity flips unmanaged.",
            "Futures hedge often beats restructuring.",
            "Add ratio under stress.",
            "Tail or margin risk unclear.",
        ),
    ]


def get_conversion_triage_table() -> list[ConversionTriageRow]:
    return [
        ConversionTriageRow(
            "Long option",
            "Long option to vertical",
            "Caps risk and preserves active thesis.",
            "Thesis failed or spread is illiquid.",
            "Exit is simpler or remaining edge is weak.",
        ),
        ConversionTriageRow(
            "Long option",
            "Long option to butterfly",
            "Pin thesis is explicit and time remains.",
            "Chasing price or wings are thin.",
            "Close beats complex pin risk.",
        ),
        ConversionTriageRow(
            "Debit spread",
            "Debit spread to butterfly",
            "Center improves and max risk drops.",
            "It masks a failed direction.",
            "Close when center is not high conviction.",
        ),
        ConversionTriageRow(
            "Debit spread",
            "Debit spread to broken-wing butterfly",
            "New tail is smaller and planned.",
            "Broken wing creates unmanaged loss.",
            "Close when tail cannot be justified.",
        ),
        ConversionTriageRow(
            "Credit spread",
            "Credit spread to condor",
            "Opposite side reduces net risk.",
            "Adds short gamma to collect theta.",
            "Close when tested side drives risk.",
        ),
        ConversionTriageRow(
            "Credit spread",
            "Credit spread to iron fly",
            "Center risk is controlled and timed.",
            "ATM short gamma is unplanned.",
            "Close when close-by-time is near.",
        ),
        ConversionTriageRow(
            "Butterfly",
            "Butterfly recentering",
            "Recenter reduces risk and is early.",
            "It chases price late.",
            "Close when wings are thin or center failed.",
        ),
        ConversionTriageRow(
            "Iron condor",
            "Iron condor one-side removal",
            "Tested side is removed cleanly.",
            "Leaves unplanned directional exposure.",
            "Close when residual side lacks thesis.",
        ),
        ConversionTriageRow(
            "Short-gamma structure",
            "Short-gamma structure to futures-hedged inventory",
            "Hedge is temporary and exit is defined.",
            "Hedge becomes a new trade thesis.",
            "Close when gamma cannot be controlled.",
        ),
        ConversionTriageRow(
            "Failed directional spread",
            "Failed directional spread to controlled-loss exit",
            "Only reduces exposure to planned loss.",
            "Any leg adds risk or delays loss.",
            "Immediate close is cleaner and liquid.",
        ),
    ]


def get_time_of_day_permission_matrix() -> list[TimeOfDayPermissionRow]:
    P = Permission
    return [
        TimeOfDayPermissionRow(
            "Hold",
            P.RESTRICTED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.CLOSE_ONLY,
            P.CLOSE_ONLY,
            "Only while thesis and risk remain inside plan.",
        ),
        TimeOfDayPermissionRow(
            "Take profit",
            P.RESTRICTED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.RESTRICTED,
            P.CLOSE_ONLY,
            P.CLOSE_ONLY,
            "Prefer simpler exits as time decays.",
        ),
        TimeOfDayPermissionRow(
            "Reduce",
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.CLOSE_ONLY,
            P.CLOSE_ONLY,
            "Reduction remains valid when risk is high.",
        ),
        TimeOfDayPermissionRow(
            "Close",
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.CLOSE_ONLY,
            P.CLOSE_ONLY,
            "ATM short gamma needs close-by-time discipline.",
        ),
        TimeOfDayPermissionRow(
            "Futures hedge",
            P.RESTRICTED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.HEDGE_ONLY,
            P.HEDGE_ONLY,
            P.HEDGE_ONLY,
            "Temporary inventory control only.",
        ),
        TimeOfDayPermissionRow(
            "Convert to vertical",
            P.RESTRICTED,
            P.ALLOWED,
            P.ALLOWED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            "Reject when closing is cleaner.",
        ),
        TimeOfDayPermissionRow(
            "Convert to fly/BWB",
            P.FORBIDDEN,
            P.RESTRICTED,
            P.ALLOWED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            "Wing liquidity decay matters after 14:00.",
        ),
        TimeOfDayPermissionRow(
            "Add risk",
            P.FORBIDDEN,
            P.RESTRICTED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            "No loss repair or behavior-impaired adds.",
        ),
        TimeOfDayPermissionRow(
            "Sell new premium",
            P.FORBIDDEN,
            P.RESTRICTED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            "No theta exception for final-hour short gamma.",
        ),
        TimeOfDayPermissionRow(
            "Recenter fly",
            P.FORBIDDEN,
            P.RESTRICTED,
            P.ALLOWED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            "Only if it reduces risk before wings thin.",
        ),
        TimeOfDayPermissionRow(
            "Remove condor side",
            P.RESTRICTED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.CLOSE_ONLY,
            P.CLOSE_ONLY,
            P.CLOSE_ONLY,
            "Remove tested risk; avoid new thesis.",
        ),
        TimeOfDayPermissionRow(
            "Roll",
            P.FORBIDDEN,
            P.RESTRICTED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            "Rolling losses is presumptively forbidden.",
        ),
        TimeOfDayPermissionRow(
            "Widen",
            P.FORBIDDEN,
            P.RESTRICTED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            "Stress widening is presumptively forbidden.",
        ),
        TimeOfDayPermissionRow(
            "Accept expiry",
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.FORBIDDEN,
            P.RESTRICTED,
            P.RESTRICTED,
            P.RESTRICTED,
            P.PREPLANNED_ONLY,
            P.PREPLANNED_ONLY,
            P.PREPLANNED_ONLY,
            "Only when max outcome is preplanned.",
        ),
        TimeOfDayPermissionRow(
            "Stop trading",
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            P.ALLOWED,
            "Always available after rule breach.",
        ),
    ]
