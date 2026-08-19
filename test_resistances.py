"""Tests for the immunity/resistance coverage engine.

The engine models damage as (type, source) atoms on two independent axes:
  * Nature: Physical vs Energy (a fixed grouping of the 12 types)
  * Source: mundane (default) or extraordinary (a tag any type can carry)

Resistance stacks: an atom resisted by two sources (innate + a roll, or the two
rolls) upgrades to immunity. The Immunity ability's coverage supersedes
resistance outright.
"""

from Cacodemon_Generator import (
    PHYSICAL_TYPES,
    ENERGY_TYPES,
    ALL_DAMAGE_TYPES,
    INNATE_RESISTANCES,
    clause_atoms,
    resolve_coverage,
    describe_coverage,
    describe_ability_rolls,
    _roll_clause,
    _reroll_if_redundant,
    _resolve_demon_coverage,
    IMMUNITY_COST,
    RESISTANCE_COST,
    ability_details,
)
from Cacodemon_Generator import ALL_DAMAGE_TYPES as _ALL


def test_incorporeal_folds_immunity_to_all_mundane_damage():
    incorp = {"name": "Incorporeal", "detail": ["", 1, None]}
    cov = _resolve_demon_coverage([incorp])
    assert cov["immune_damage"] == {(t, "mundane") for t in _ALL}


def both(*types):
    """All (type, source) atoms for the given types, both sources."""
    return {(t, s) for t in types for s in ("mundane", "extraordinary")}


def mundane(*types):
    return {(t, "mundane") for t in types}


def extraordinary(*types):
    return {(t, "extraordinary") for t in types}


INNATE_ATOMS = both(*INNATE_RESISTANCES)


# --- Category membership (the game's non-intuitive split) -------------------

def test_physical_and_energy_partition_the_twelve_types():
    assert set(PHYSICAL_TYPES) == {
        "Acidic", "Arcane", "Bludgeoning", "Piercing", "Poisonous", "Slashing"
    }
    assert set(ENERGY_TYPES) == {
        "Cold", "Electrical", "Fire", "Luminous", "Necrotic", "Seismic"
    }
    # Disjoint and together they are exactly the twelve.
    assert set(PHYSICAL_TYPES).isdisjoint(ENERGY_TYPES)
    assert set(ALL_DAMAGE_TYPES) == set(PHYSICAL_TYPES) | set(ENERGY_TYPES)
    assert len(ALL_DAMAGE_TYPES) == 12


def test_innate_resistances_are_the_six_base_types():
    assert set(INNATE_RESISTANCES) == {
        "Acidic", "Cold", "Electrical", "Fire", "Poisonous", "Seismic"
    }


# --- Clause -> atom expansion ----------------------------------------------

def test_all_mundane_clause_covers_every_type_in_mundane_form_only():
    dmg, eff = clause_atoms({"selector": 1, "picks": None})
    assert dmg == {(t, "mundane") for t in ALL_DAMAGE_TYPES}
    assert eff == set()


def test_all_physical_clause_covers_physical_types_in_both_sources():
    dmg, eff = clause_atoms({"selector": 3, "picks": None})
    assert dmg == {(t, s) for t in PHYSICAL_TYPES for s in ("mundane", "extraordinary")}
    assert eff == set()


def test_mundane_physical_clause_is_physical_types_mundane_only():
    dmg, eff = clause_atoms({"selector": 7, "picks": None})
    assert dmg == {(t, "mundane") for t in PHYSICAL_TYPES}


def test_any_three_mundane_types_uses_the_picked_types_mundane_only():
    dmg, eff = clause_atoms({"selector": 8, "picks": ["Fire", "Bludgeoning", "Luminous"]})
    assert dmg == {("Fire", "mundane"), ("Bludgeoning", "mundane"), ("Luminous", "mundane")}


def test_any_three_types_uses_the_picked_types_in_both_sources():
    dmg, eff = clause_atoms({"selector": 6, "picks": ["Fire", "Cold", "Slashing"]})
    assert dmg == {
        (t, s) for t in ("Fire", "Cold", "Slashing") for s in ("mundane", "extraordinary")
    }


def test_effect_clauses_produce_effect_tokens_not_damage():
    assert clause_atoms({"selector": 9, "picks": None}) == (set(), {"enchantment"})
    assert clause_atoms({"selector": 10, "picks": None}) == (set(), {"death"})
    assert clause_atoms({"selector": 11, "picks": None}) == (set(), {"transmogrification"})


# --- Resolver: no abilities -------------------------------------------------

def test_bare_imp_just_has_its_innate_base_resistances():
    r = resolve_coverage(immunity_clauses=[], resistance_clauses=[])
    assert r["immune_damage"] == set()
    assert r["immune_effects"] == set()
    assert r["base_resist"] == INNATE_ATOMS
    assert r["additional_resist_damage"] == set()
    assert r["additional_resist_effects"] == set()


# --- Resolver: doubling upgrades resistance to immunity ---------------------

def test_two_resistance_rolls_overlapping_a_type_make_it_immune():
    # Two "any 3 types" rolls that share Bludgeoning (a non-innate type, to
    # isolate this from innate stacking). The shared type upgrades to immunity;
    # the rest stay resistance.
    r = resolve_coverage(
        immunity_clauses=[],
        resistance_clauses=[
            {"selector": 6, "picks": ["Arcane", "Bludgeoning", "Luminous"]},
            {"selector": 6, "picks": ["Bludgeoning", "Necrotic", "Piercing"]},
        ],
    )
    assert r["immune_damage"] == both("Bludgeoning")
    assert r["additional_resist_damage"] == both("Arcane", "Luminous", "Necrotic", "Piercing")
    # Innate resistances untouched.
    assert r["base_resist"] == INNATE_ATOMS


def test_rolling_an_innately_resisted_type_is_wasted_not_upgraded():
    # Innate is NOT a stacking source. A single roll on Fire (already innate)
    # neither becomes immunity nor a new line -- it's tough luck.
    r = resolve_coverage(
        immunity_clauses=[],
        resistance_clauses=[{"selector": 6, "picks": ["Fire", "Luminous", "Necrotic"]}],
    )
    assert r["immune_damage"] == set()
    assert r["base_resist"] == INNATE_ATOMS                # Fire still just innate
    # Fire is dropped from "additional" (already innate); only the genuinely new
    # non-innate types show up.
    assert r["additional_resist_damage"] == both("Luminous", "Necrotic")


def test_two_rolls_of_an_innate_type_still_stack_to_immunity():
    # The two rolls stack with EACH OTHER (not with innate), so doubling Fire
    # across both rolls does grant immunity -- Fire then leaves the base line.
    r = resolve_coverage(
        immunity_clauses=[],
        resistance_clauses=[
            {"selector": 6, "picks": ["Fire", "Arcane", "Luminous"]},
            {"selector": 6, "picks": ["Fire", "Necrotic", "Piercing"]},
        ],
    )
    assert r["immune_damage"] == both("Fire")
    assert both("Fire").isdisjoint(r["base_resist"])
    assert r["base_resist"] == both("Acidic", "Cold", "Electrical", "Poisonous", "Seismic")
    assert r["additional_resist_damage"] == both("Arcane", "Luminous", "Necrotic", "Piercing")


# --- Resolver: the user's canonical all-mundane + mundane-physical case -----

def test_all_mundane_plus_mundane_physical_immunes_only_the_physical_overlap():
    r = resolve_coverage(
        immunity_clauses=[],
        resistance_clauses=[
            {"selector": 1, "picks": None},   # all mundane
            {"selector": 7, "picks": None},   # all mundane physical
        ],
    )
    # Only the mundane physical types are covered by BOTH rolls -> immune.
    # (Innate no longer stacks, so mundane Cold/Fire/etc. stay resistance.)
    assert r["immune_damage"] == mundane(*PHYSICAL_TYPES)
    # Innate keeps both sources except where it's now immune (mundane Acidic and
    # Poisonous are physical), leaving those two extraordinary-only.
    assert r["base_resist"] == (
        both("Cold", "Electrical", "Fire", "Seismic")
        | extraordinary("Acidic", "Poisonous")
    )
    # The non-innate mundane energy types from "all mundane" are the new ones.
    assert r["additional_resist_damage"] == mundane("Luminous", "Necrotic")


# --- Resolver: the Immunity ability supersedes Resistance ------------------

def test_immunity_ability_supersedes_a_resistance_to_the_same_thing():
    # Immune to all physical, and Resistance also rolled all physical -> the
    # resistance is fully superseded (adds nothing), physical stays immune.
    r = resolve_coverage(
        immunity_clauses=[{"selector": 3, "picks": None}],   # all physical
        resistance_clauses=[{"selector": 3, "picks": None}], # all physical
    )
    assert r["immune_damage"] == both(*PHYSICAL_TYPES)
    assert r["additional_resist_damage"] == set()
    # Only the innate energy types survive as base resistance (innate physical
    # types Acidic/Poisonous were upgraded into the immunity).
    assert r["base_resist"] == both("Cold", "Electrical", "Fire", "Seismic")


# --- Resolver: effects double and supersede the same way -------------------

def test_two_resistance_rolls_of_the_same_effect_become_immunity():
    r = resolve_coverage(
        immunity_clauses=[],
        resistance_clauses=[
            {"selector": 9, "picks": None},   # enchantment
            {"selector": 9, "picks": None},   # enchantment
        ],
    )
    assert r["immune_effects"] == {"enchantment"}
    assert r["additional_resist_effects"] == set()


def test_a_single_effect_roll_is_just_a_resistance():
    r = resolve_coverage(
        immunity_clauses=[],
        resistance_clauses=[{"selector": 10, "picks": None}],   # death
    )
    assert r["immune_effects"] == set()
    assert r["additional_resist_effects"] == {"death"}


# --- Rendering atoms to readable text --------------------------------------

def test_empty_coverage_reads_none():
    assert describe_coverage(set(), set()) == "None"


def test_whole_categories_collapse_to_their_name():
    assert describe_coverage(both(*ALL_DAMAGE_TYPES), set()) == "all damage"
    assert describe_coverage(both(*PHYSICAL_TYPES), set()) == "all physical damage"
    assert describe_coverage(both(*ENERGY_TYPES), set()) == "all energy damage"


def test_mundane_and_extraordinary_scopes_are_labelled():
    assert describe_coverage(mundane(*ALL_DAMAGE_TYPES), set()) == "all mundane damage"
    assert describe_coverage(mundane(*PHYSICAL_TYPES), set()) == "all mundane physical damage"
    assert describe_coverage(extraordinary(*ENERGY_TYPES), set()) == "all extraordinary energy damage"


def test_types_are_listed_alphabetically():
    assert describe_coverage(both("Fire"), set()) == "Fire"
    # Alphabetical -- distinct from type-index order, which would give
    # "Acidic, Slashing, Fire" (physical types before energy types).
    assert describe_coverage(both("Slashing", "Acidic", "Fire"), set()) == "Acidic, Fire, Slashing"


def test_single_source_types_get_a_source_prefix():
    assert describe_coverage(mundane("Luminous", "Necrotic"), set()) == "mundane Luminous, Necrotic"
    assert describe_coverage(extraordinary("Fire"), set()) == "extraordinary Fire"


def test_almost_complete_scope_collapses_with_except():
    # The canonical innate-stacking immune set: all mundane but Luminous/Necrotic.
    atoms = mundane(
        "Acidic", "Arcane", "Bludgeoning", "Piercing", "Poisonous", "Slashing",
        "Cold", "Electrical", "Fire", "Seismic",
    )
    assert describe_coverage(atoms, set()) == "all mundane damage except Luminous, Necrotic"


def test_mixed_scopes_and_effects_join_with_semicolons():
    text = describe_coverage(both("Fire") | extraordinary("Cold"), {"death"})
    assert text == "Fire; extraordinary Cold; all death effects"


# --- Rolling clauses --------------------------------------------------------

def test_roll_clause_always_produces_a_valid_selector_and_picks():
    for _ in range(500):
        c = _roll_clause()
        assert 1 <= c["selector"] <= 11
        if c["selector"] == 5:
            assert len(c["picks"]) == 6
        elif c["selector"] in (6, 8):
            assert len(c["picks"]) == 3
        else:
            assert c["picks"] is None
        if c["picks"]:
            assert all(t in ALL_DAMAGE_TYPES for t in c["picks"])
            assert len(set(c["picks"])) == len(c["picks"])   # no dup picks


def test_roll_clause_can_pick_innate_types_now():
    # Innate exclusion was dropped: a roll may land on an innate type (it then
    # stacks to immunity). Over many rolls at least one innate type appears.
    seen = set()
    for _ in range(2000):
        c = _roll_clause()
        if c["picks"]:
            seen.update(c["picks"])
    assert seen & set(INNATE_RESISTANCES)


# --- ability_details now returns structured, resolvable clauses -------------

def test_resistance_ability_details_returns_two_clauses_and_summed_cost():
    info, cost, structured = ability_details("Resistance", "Imp")
    assert structured["kind"] == "resistance"
    assert len(structured["clauses"]) == 2
    assert cost == sum(RESISTANCE_COST[c["selector"]] for c in structured["clauses"])


def test_immunity_ability_details_returns_one_clause_and_its_cost():
    info, cost, structured = ability_details("Immunity", "Imp")
    assert structured["kind"] == "immunity"
    assert len(structured["clauses"]) == 1
    assert cost == IMMUNITY_COST[structured["clauses"][0]["selector"]]


# --- Re-roll guard: never pay for a resistance you're already immune to -----

def test_reroll_replaces_a_fully_immune_resistance_clause():
    immune_atoms = clause_atoms({"selector": 3, "picks": None})[0]   # all physical
    redundant = {"selector": 3, "picks": None}                       # all physical
    out = _reroll_if_redundant(redundant, immune_atoms, set())
    d, e = clause_atoms(out)
    assert not (d <= immune_atoms and e <= set())          # now adds something
    assert RESISTANCE_COST[out["selector"]] == RESISTANCE_COST[3]   # same cost tier


def test_reroll_leaves_a_useful_clause_untouched():
    immune_atoms = clause_atoms({"selector": 3, "picks": None})[0]   # all physical
    useful = {"selector": 4, "picks": None}                          # all energy
    assert _reroll_if_redundant(useful, immune_atoms, set()) is useful


# --- End-to-end integration into the demon and its stat block --------------

from Cacodemon_Generator import generate_cacodemon_base, format_stats_block


def test_generated_demon_carries_resolved_coverage():
    demon = generate_cacodemon_base("Imp", body_form="Arachnine")
    cov = demon["coverage"]
    for key in ("immune_damage", "immune_effects", "base_resist",
                "additional_resist_damage", "additional_resist_effects"):
        assert key in cov


def test_stat_block_shows_the_three_coverage_lines_in_order():
    demon = generate_cacodemon_base("Imp", body_form="Arachnine")
    labels = [l.split(":")[0] for l in format_stats_block(demon).splitlines()]
    i = labels.index("Immunities")
    assert labels[i:i + 3] == ["Immunities", "Base Resistances", "Additional Resistances"]


def test_nothing_is_ever_both_immune_and_resisted():
    # The core promise: immunity always supersedes, so a type can never appear
    # as both immune and resisted on the same imp.
    for _ in range(300):
        demon = generate_cacodemon_base("Imp")
        cov = demon["coverage"]
        resisted = cov["base_resist"] | cov["additional_resist_damage"]
        assert cov["immune_damage"].isdisjoint(resisted)
        assert cov["immune_effects"].isdisjoint(cov["additional_resist_effects"])


# --- Raw per-ability roll detail (so the roll-up is traceable) -------------

def test_immunity_detail_describes_its_single_roll():
    info = describe_ability_rolls(
        {"kind": "immunity", "clauses": [{"selector": 3, "picks": None}]}
    )
    assert info == "Immune to all physical damage"


def test_resistance_detail_shows_both_rolls_labelled():
    info = describe_ability_rolls({"kind": "resistance", "clauses": [
        {"selector": 1, "picks": None},
        {"selector": 6, "picks": ["Fire", "Cold", "Slashing"]},
    ]})
    assert info == "Roll 1: Resists all mundane damage; Roll 2: Resists Cold, Fire, Slashing"


def test_ability_details_carry_the_raw_roll_text():
    for name in ("Immunity", "Resistance"):
        info, cost, structured = ability_details(name, "Imp")
        assert info == describe_ability_rolls(structured)
        assert info  # non-empty: the expander shows how the roll-up was reached


def test_resistance_detail_matches_its_final_clauses_after_reroll():
    # Immunity makes the first Resistance clause redundant; after resolution the
    # detail text must describe the FINAL (re-rolled) clauses, not the stale one.
    imm = {"name": "Immunity",
           "detail": ["", 1, {"kind": "immunity", "clauses": [{"selector": 3, "picks": None}]}]}
    res = {"name": "Resistance",
           "detail": ["", 0.75, {"kind": "resistance", "clauses": [
               {"selector": 3, "picks": None},                       # all physical -> redundant
               {"selector": 6, "picks": ["Luminous", "Necrotic", "Arcane"]},
           ]}]}
    _resolve_demon_coverage([imm, res])
    assert res["detail"][0]
    assert res["detail"][0] == describe_ability_rolls(res["detail"][2])
