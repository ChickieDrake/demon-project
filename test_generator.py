"""Tests for the Choice Mode additions to the cacodemon generator.

Choice Mode is two independent options, both surfaced as new keyword arguments:
  * body_form       -- pick the form instead of rolling it randomly
  * signature_choice -- force-include (True) / force-exclude (False) the form's
                        signature ability, or leave it random (None, the default)

A signature ability added by the generator is marked with roll == "auto"; a
randomly-rolled ability carries its numeric roll. Tests use that marker to tell
a *chosen* signature apart from one that merely happened to be rolled.
"""

import inspect

from Cacodemon_Generator import (
    generate_cacodemon_base,
    roll_abilities_with_cost_limit,
)
from imp_names import IMP_NAMES


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


# --- Speech / spellcasting -------------------------------------------------

def test_uses_speech_defaults_to_false():
    assert inspect.signature(generate_cacodemon_base).parameters["uses_speech"].default is False


def test_speech_off_disables_spellcasting():
    result = generate_cacodemon_base("Imp", uses_speech=False)
    assert result["spells"] == "None"
    assert "Spellcasting" not in [a["name"] for a in result["abilities"]["abilities"]]


def test_uses_speech_true_enables_spellcasting():
    result = generate_cacodemon_base("Imp", uses_speech=True)
    assert result["spells"] != "None"


# --- Stats block extraction ------------------------------------------------

def test_format_stats_block_has_stats_only():
    from Cacodemon_Generator import format_stats_block
    demon = generate_cacodemon_base("Imp", body_form="Arachnine")
    block = format_stats_block(demon)
    assert "Size:" in block
    assert "Other Senses:" in block
    # It is ONLY the stats -- no abilities or spellcasting sections.
    assert "Special Abilities" not in block
    assert "Spellcasting" not in block


def test_imp_hit_points_is_4d8():
    hp = generate_cacodemon_base("Imp")["hit_points"]
    assert isinstance(hp, int)
    assert 4 <= hp <= 32  # 4d8


# --- Naming -----------------------------------------------------------------

def test_generated_imp_has_a_name():
    from Cacodemon_Generator import reset_used_names
    reset_used_names()
    demon = generate_cacodemon_base("Imp")
    assert demon["name"] in IMP_NAMES


def test_names_are_unique_until_pool_exhausted():
    from Cacodemon_Generator import assign_imp_name, reset_used_names
    reset_used_names()
    names = [assign_imp_name() for _ in range(len(IMP_NAMES))]
    assert len(set(names)) == len(IMP_NAMES)  # every name used exactly once


def test_pool_resets_after_exhaustion():
    from Cacodemon_Generator import assign_imp_name, reset_used_names
    reset_used_names()
    for _ in range(len(IMP_NAMES)):
        assign_imp_name()
    # Pool is now exhausted; the next call must still return a valid name.
    extra = assign_imp_name()
    assert extra in IMP_NAMES


def test_used_names_persist_to_disk():
    # A used name must be crossed off on disk, not just in memory: reading the
    # store back from disk must show it.
    from Cacodemon_Generator import assign_imp_name, reset_used_names, _load_used_names
    reset_used_names()
    name = assign_imp_name()
    assert name in _load_used_names()


# --- Ability book-cost symbols and clean Flying text ------------------------

def test_all_abilities_carry_book_cost():
    result = roll_abilities_with_cost_limit(
        2, False, "Man-Sized", "Arachnine", True, "Imp", signature_choice=True
    )
    assert all("book_cost" in a for a in result["abilities"])


def test_signature_and_flying_book_cost_symbols():
    poison = roll_abilities_with_cost_limit(
        1, False, "Man-Sized", "Arachnine", False, "Imp", signature_choice=True
    )
    assert next(a for a in poison["abilities"] if a["name"] == "Poison")["book_cost"] == "*"

    winged = roll_abilities_with_cost_limit(
        1, False, "Man-Sized", "Humanoid", True, "Imp", signature_choice=None
    )
    assert next(a for a in winged["abilities"] if a["name"] == "Flying")["book_cost"] == "####"


def test_flying_description_has_no_dive_text():
    result = roll_abilities_with_cost_limit(
        1, False, "Man-Sized", "Scolopendrine", True, "Imp", signature_choice=True
    )
    flying = next(a for a in result["abilities"] if a["name"] == "Flying")
    assert "dive" not in flying["description"].lower()


def test_flying_cost_is_half_even_with_custom_description():
    result = roll_abilities_with_cost_limit(
        1, False, "Man-Sized", "Humanoid", True, "Imp", signature_choice=None
    )
    flying = next(a for a in result["abilities"] if a["name"] == "Flying")
    assert flying["cost"] == 0.5  # #### = 4 * 0.125


def test_dive_attack_worth_four_hash():
    result = roll_abilities_with_cost_limit(
        1, False, "Man-Sized", "Wyverine", True, "Imp", signature_choice=True
    )
    dive = next(a for a in result["abilities"] if a["name"] == "Dive Attack")
    assert dive["book_cost"] == "####"
    assert dive["cost"] == 0.5


# --- Resolved */# symbols and summing to the allotment ---------------------

def test_value_symbols_resolves_to_book_notation():
    from Cacodemon_Generator import value_symbols
    assert value_symbols(1.0) == "*"
    assert value_symbols(2.0) == "**"
    assert value_symbols(0.5) == "####"
    assert value_symbols(0.25) == "##"
    assert value_symbols(0.125) == "#"
    assert value_symbols(1.5) == "*####"
    assert value_symbols(0) == ""


def test_special_ability_total_never_exceeds_allotment():
    # Every generated Imp's abilities must sum to at most ** (2.0); they must
    # not overshoot the allotment.
    for _ in range(200):
        r = roll_abilities_with_cost_limit(
            2, False, "Man-Sized", "Arachnine", False, "Imp", signature_choice=None
        )
        assert r["total_cost"] <= 2.0 + 1e-9, r["total_cost"]


def test_stats_block_has_hit_points_resistances_and_languages():
    from Cacodemon_Generator import format_stats_block
    demon = generate_cacodemon_base("Imp", body_form="Arachnine")
    block = format_stats_block(demon)
    assert "Base Resistances:" in block
    lines = block.splitlines()
    assert any(l.startswith("Languages:") and l.endswith("None (but uses Telepathy)") for l in lines)
    # Hit Points appears directly under Hit Dice.
    hd_idx = next(i for i, line in enumerate(lines) if line.startswith("Hit Dice:"))
    assert lines[hd_idx + 1].startswith("Hit Points:")
