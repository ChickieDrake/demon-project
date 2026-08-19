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


# --- Signature choice as a probability -------------------------------------

def _forced_poison(sig):
    r = roll_abilities_with_cost_limit(
        2, False, "Man-Sized", "Arachnine", False, "Imp", signature_choice=sig
    )
    return any(a["name"] == "Poison" and a["roll"] == "auto" for a in r["abilities"])


def test_signature_probability_half_forces_about_half():
    forced = sum(_forced_poison(0.5) for _ in range(2000))
    assert 0.4 < forced / 2000 < 0.6  # ~50%, not ~100%


def test_signature_probability_one_always_forces():
    assert all(_forced_poison(1.0) for _ in range(30))


def test_signature_probability_zero_never_forces():
    assert not any(_forced_poison(0.0) for _ in range(30))


# --- Immunity/Resistance resolve into non-overlapping coverage -------------

def test_immunity_and_resistance_never_cover_the_same_thing():
    # Immunity always supersedes resistance, so no generated imp may list a
    # damage type (or effect) as both immune and resisted. (Detailed coverage
    # rules live in test_resistances.py; this guards the wired-up generator.)
    for _ in range(500):
        cov = generate_cacodemon_base("Imp")["coverage"]
        resisted = cov["base_resist"] | cov["additional_resist_damage"]
        assert cov["immune_damage"].isdisjoint(resisted)
        assert cov["immune_effects"].isdisjoint(cov["additional_resist_effects"])


# --- Hug requires a multi-attack form --------------------------------------

def test_hug_is_rerolled_for_single_attack_forms():
    # Arachnine (1 bite) and Monadine (1 envelopment) make a single attack, so
    # "hits with more than half its attacks" is nonsensical -- re-roll Hug.
    from Cacodemon_Generator import should_reroll_ability
    assert should_reroll_ability("Hug", False, "Man-Sized", "Arachnine")
    assert should_reroll_ability("Hug", False, "Man-Sized", "Monadine")


def test_hug_is_allowed_for_multi_attack_forms():
    from Cacodemon_Generator import should_reroll_ability
    for form in ("Humanoid", "Scolopendrine", "Wyverine"):
        assert not should_reroll_ability("Hug", False, "Man-Sized", form)


def test_single_attack_forms_never_generate_hug():
    for form in ("Arachnine", "Monadine"):
        for _ in range(300):
            demon = generate_cacodemon_base("Imp", body_form=form)
            assert "Hug" not in [a["name"] for a in demon["abilities"]["abilities"]]


# --- Abilities folded into the stat block ----------------------------------

from Cacodemon_Generator import effective_stat_block, _scale_speed, _note_stat_folding


def _ability(name, detail0="", structured=None):
    return {"name": name, "roll": "x", "cost": 0, "book_cost": "",
            "description": "", "detail": [detail0, 0, structured]}


def _demon_with(abilities):
    """Minimal demon dict for stat-folding tests (Man-Sized Humanoid, AC 4)."""
    return {
        "primary_stats": {"ac": 4, "morale": 0},
        "combat_stats": {
            "attack_routine": "3 (2 claws, 1 bite)",
            "movement": {"land": "40'/120'", "fly": "80'/240'", "climb": None, "swim": None},
        },
        "attack": "7+",
        "abilities": {"abilities": abilities},
    }


def test_tough_adds_its_rolled_ac_bonus():
    demon = _demon_with([_ability("Tough", "AC Increased by 3", {"ac_bonus": 3})])
    assert effective_stat_block(demon)["ac"] == 7            # 4 + 3


def test_ac_unchanged_without_tough():
    assert effective_stat_block(_demon_with([]))["ac"] == 4


def test_berserk_improves_attack_throw_by_two_and_sets_morale():
    eff = effective_stat_block(_demon_with([_ability("Berserk")]))
    assert eff["attack"] == "5+"                              # 7+ improved by 2
    assert eff["morale"] == 4


def test_bonus_attack_appends_to_the_attacks_line():
    one = _demon_with([_ability("Bonus Attack", "", {"bonus_attacks": 1, "damage": "primary"})])
    assert effective_stat_block(one)["attacks_suffix"] == " +1 bonus attack (primary dmg)"
    two = _demon_with([_ability("Bonus Attack", "", {"bonus_attacks": 2, "damage": "half"})])
    assert effective_stat_block(two)["attacks_suffix"] == " +2 bonus attacks (half dmg)"


def test_swift_scales_speeds_by_25_percent_rounded_to_nearest_five():
    assert _scale_speed("40'/120'") == "50'/150'"
    assert _scale_speed("10'/30'") == "15'/40'"
    assert _scale_speed("40'/120' or 30'/90'") == "50'/150' or 40'/115'"
    assert _scale_speed(None) is None


def test_swift_present_scales_the_movement():
    demon = _demon_with([_ability("Swift")])
    assert effective_stat_block(demon)["movement"]["land"] == "50'/150'"


def test_stat_fold_note_is_appended_only_to_folded_abilities():
    abils = [
        _ability("Tough", "AC Increased by 2", {"ac_bonus": 2}),
        _ability("Berserk"),
        _ability("Poison", "onset time: instant; effect: death"),   # not folded
    ]
    _note_stat_folding(abils)
    tough = next(a for a in abils if a["name"] == "Tough")
    berserk = next(a for a in abils if a["name"] == "Berserk")
    poison = next(a for a in abils if a["name"] == "Poison")
    assert tough["detail"][0].startswith("AC Increased by 2")
    assert tough["detail"][0].endswith("reflected in the stat block")
    assert "reflected in the stat block" in berserk["detail"][0]
    assert "reflected in the stat block" not in poison["detail"][0]


def test_stat_fold_note_covers_the_other_folded_abilities():
    abils = [
        _ability("Flying"),
        _ability("Special Senses", "Acute Olfaction", {"sense": "Acute Olfaction"}),
        _ability("Immunity", "Immune to all physical damage", {"kind": "immunity"}),
        _ability("Resistance", "Roll 1: Resists all death effects", {"kind": "resistance"}),
        _ability("Aura", "Fire"),   # not folded into the stat block
    ]
    _note_stat_folding(abils)
    for nm in ("Flying", "Special Senses", "Immunity", "Resistance"):
        detail = next(a for a in abils if a["name"] == nm)["detail"][0]
        assert "reflected in the stat block" in detail.lower()
    aura = next(a for a in abils if a["name"] == "Aura")["detail"][0]
    assert "reflected in the stat block" not in aura.lower()


def test_special_senses_line_is_not_polluted_by_the_note():
    # The Other Senses line must show the sense only; the note lives in the
    # ability's detail, read separately from structured data.
    from Cacodemon_Generator import format_stats_block
    for _ in range(3000):
        demon = generate_cacodemon_base("Imp")
        by = {a["name"]: a for a in demon["abilities"]["abilities"]}
        if "Special Senses" not in by:
            continue
        other = next(l for l in format_stats_block(demon).splitlines()
                     if l.startswith("Other Senses:"))
        assert "reflected in the stat block" not in other
        assert "reflected in the stat block" in by["Special Senses"]["detail"][0]
        return
    raise AssertionError("no Special Senses rolled in sample")


def test_stat_block_ac_and_morale_match_effective_values():
    # Wiring guard: the rendered stat block uses the folded values.
    demon = generate_cacodemon_base("Imp")
    eff = effective_stat_block(demon)
    from Cacodemon_Generator import format_stats_block
    lines = format_stats_block(demon).splitlines()
    ac_line = next(l for l in lines if l.startswith("Armor Class:"))
    morale_line = next(l for l in lines if l.startswith("Morale:"))
    assert ac_line.split()[-1] == str(eff["ac"])
    assert morale_line.split()[-1] == str(eff["morale"])


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
