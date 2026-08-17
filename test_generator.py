"""Tests for the Choice Mode additions to the cacodemon generator.

Choice Mode is two independent options, both surfaced as new keyword arguments:
  * body_form       -- pick the form instead of rolling it randomly
  * signature_choice -- force-include (True) / force-exclude (False) the form's
                        signature ability, or leave it random (None, the default)

A signature ability added by the generator is marked with roll == "auto"; a
randomly-rolled ability carries its numeric roll. Tests use that marker to tell
a *chosen* signature apart from one that merely happened to be rolled.
"""

from Cacodemon_Generator import (
    generate_cacodemon_base,
    roll_abilities_with_cost_limit,
)


def names(result):
    return [a["name"] for a in result["abilities"]]


def has_auto(result, name):
    """True if `name` was added as a signature ability (roll == 'auto')."""
    return any(a["roll"] == "auto" and a["name"] == name for a in result["abilities"])


# --- Feature 1: choosing the body form -------------------------------------

def test_chosen_body_form_is_respected():
    result = generate_cacodemon_base("Imp", body_form="Scolopendrine")
    assert result["body_form"][0] == "Scolopendrine"


def test_random_generation_still_works():
    # Backward compatibility: no Choice Mode args -> random form, valid output.
    result = generate_cacodemon_base("Imp")
    assert result["body_form"][0] in {
        "Arachnine", "Humanoid", "Monadine", "Scolopendrine", "Wyverine"
    }
    assert len(result["abilities"]["abilities"]) > 0


# --- Feature 2: choosing the signature ability -----------------------------

def test_forced_signature_is_included():
    result = roll_abilities_with_cost_limit(
        2, False, "Man-Sized", "Arachnine", False, "Imp", signature_choice=True
    )
    assert has_auto(result, "Poison")


def test_excluded_signature_is_not_auto_added():
    # False must suppress the signature. (A randomly *rolled* Poison would carry
    # a numeric roll, so we assert specifically that none was auto-added.)
    result = roll_abilities_with_cost_limit(
        2, False, "Man-Sized", "Arachnine", False, "Imp", signature_choice=False
    )
    assert not has_auto(result, "Poison")


def test_forced_signature_counts_against_budget():
    # Poison costs 1.0; with a budget of 1 the signature alone fills it, so
    # nothing else is rolled on top. This is the user's core requirement.
    result = roll_abilities_with_cost_limit(
        1, False, "Man-Sized", "Arachnine", False, "Imp", signature_choice=True
    )
    assert names(result) == ["Poison"]


def test_wyverine_winged_signature_is_dive_attack():
    result = roll_abilities_with_cost_limit(
        1, False, "Man-Sized", "Wyverine", True, "Imp", signature_choice=True
    )
    assert has_auto(result, "Dive Attack")
    assert "Berserk" not in names(result)


def test_wyverine_nonwinged_signature_is_berserk():
    result = roll_abilities_with_cost_limit(
        0.25, False, "Man-Sized", "Wyverine", False, "Imp", signature_choice=True
    )
    assert has_auto(result, "Berserk")
    assert "Dive Attack" not in names(result)


def test_monadine_swallow_included_when_huge():
    result = roll_abilities_with_cost_limit(
        1, False, "Huge", "Monadine", False, "Imp", signature_choice=True
    )
    assert has_auto(result, "Swallow Attack")


def test_monadine_swallow_blocked_below_huge_even_when_chosen():
    # Explicit choice does NOT override the size gate: a Man-Sized Monadine
    # cannot swallow, so the signature is silently dropped.
    result = roll_abilities_with_cost_limit(
        2, False, "Man-Sized", "Monadine", False, "Imp", signature_choice=True
    )
    assert "Swallow Attack" not in names(result)


def test_winged_always_gets_flying():
    # Regression guard: the refactor of the built-in block must not drop Flying.
    result = roll_abilities_with_cost_limit(
        1, False, "Man-Sized", "Humanoid", True, "Imp", signature_choice=None
    )
    assert has_auto(result, "Flying")


# --- Both features together, through the top-level entry point --------------

def test_generate_with_chosen_form_and_forced_signature():
    result = generate_cacodemon_base(
        "Imp", body_form="Arachnine", signature_choice=True
    )
    assert result["body_form"][0] == "Arachnine"
    assert has_auto(result["abilities"], "Poison")
