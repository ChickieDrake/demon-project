#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import os
import random
import pandas as pd
import re

from collections import Counter

from imp_names import IMP_NAMES


# In[3]:


def generate_form_combat_stats(form, rank):
    # Normalize rank to match table keys
    rank = rank.capitalize()

    base_stats = {
        "Arachnine": {
            "ac_mod": +1,
            "movement": {"land": "20'/60'", "fly": "40'/120'", "climb": "20'/60'", "swim": None},
            "attack_routine": "1 (bite)",
            "bme": 1.5,
            "ccf": 0.30,
        },
        "Humanoid": {
            "ac_mod": 0,
            "movement": {"land": "40'/120' or 30'/90'", "fly": "80'/240'", "climb": None, "swim": None},
            "attack_routine": "3 (2 claws, 1 bite)",
            "bme": 2,
            "ccf": 0.033,
        },
        "Monadine": {
            "ac_mod": 0,
            "movement": {"land": "10'/30'", "fly": "20'/60'", "climb": "10'/30'", "swim": "10'/30'"},
            "attack_routine": "1 (envelopment)",
            "bme": 2.08,
            "ccf": None,
        },
        "Scolopendrine": {
            "ac_mod": 0,
            "movement": {"land": "40'/120'", "fly": "60'/180'", "climb": None, "swim": None},
            "attack_routine": "9 (8 tentacles, 1 bite)",
            "bme": 1.5,
            "ccf": 0.20,
        },
        "Wyverine": {
            "ac_mod": +1,
            "movement": {"land": "40'/120' or 30'/90'", "fly": "80'/240'", "climb": None, "swim": None},
            "attack_routine": "2 (talons or bite/sting)",
            "bme": 1.72,
            "ccf": 0.20,
        }
    }

    # Damage by form and rank
    damage_by_form_rank = {
        "Arachnine": {
            "Spawn": ["1d8"],
            "Imp": ["2d8"],
            "Gremlin": ["2d12"],
            "Hellion": ["4d8"],
            "Incubus": ["4d10"],
            "Demon": ["4d12"],
            "Dybbuk": ["6d8"],
            "Devil": ["6d10"],
            "Fiend": ["6d12"],
            "Archfiend": ["7d10+2"]
        },
        "Humanoid": {
            "Spawn": ["1d2", "1d2", "1d3"],
            "Imp": ["1d3", "1d3", "1d6"],
            "Gremlin": ["1d4", "1d4", "1d10"],
            "Hellion": ["1d6", "1d6", "2d6+1"],
            "Incubus": ["1d10", "1d10", "2d10"],
            "Demon": ["1d12", "1d12", "2d12"],
            "Dybbuk": ["2d6", "2d6", "4d6"],
            "Devil": ["2d6+1", "2d6+1", "4d6+1"],
            "Fiend": ["2d8", "2d8", "3d12"],
            "Archfiend": ["2d10", "2d10", "4d10"]
        },
        "Monadine": {
            "Spawn": ["1d8"],
            "Imp": ["2d8"],
            "Gremlin": ["2d12"],
            "Hellion": ["4d8"],
            "Incubus": ["4d10"],
            "Demon": ["4d12"],
            "Dybbuk": ["6d8"],
            "Devil": ["6d10"],
            "Fiend": ["6d12"],
            "Archfiend": ["7d10+2"]
        },
        "Scolopendrine": {
            "Spawn": ["0", "1d6"],
            "Imp": ["1d2", "1d2+4"],
            "Gremlin": ["1d3-1", "2d4+1"],
            "Hellion": ["1d3", "2d6+1"],
            "Incubus": ["1d2", "2d10"],
            "Demon": ["1d2", "2d12"],
            "Dybbuk": ["1d3", "4d6"],
            "Devil": ["1d3", "4d6+1"],
            "Fiend": ["1d4", "3d12"],
            "Archfiend": ["1d4", "4d10"]
        },
        "Wyverine": {
            "Spawn": ["1d4", "1d4"],
            "Imp": ["1d8", "1d8"],
            "Gremlin": ["1d12", "1d12"],
            "Hellion": ["2d8", "2d8"],
            "Incubus": ["2d10", "2d10"],
            "Demon": ["2d12", "2d12"],
            "Dybbuk": ["3d8+1", "3d8+1"],
            "Devil": ["3d10+1", "3d10+1"],
            "Fiend": ["3d12", "3d12"],
            "Archfiend": ["2d20", "2d20"]
        }
    }


    stats = base_stats[form]
    damage = damage_by_form_rank.get(form, {}).get(rank, ["Unknown"])

    return {
        "ac_mod": stats["ac_mod"],
        "movement": stats["movement"],
        "attack_routine": stats["attack_routine"],
        "damage":damage,
        "bme": stats["bme"],
        "ccf": stats["ccf"]
    }


# In[4]:


rank_primary_stats = {
    "Spawn":     {"base_ac": 3, "hd": "2**",  "save": "F2",  "morale": 0},
    "Imp":       {"base_ac": 4, "hd": "4**",  "save": "F4",  "morale": 0},
    "Gremlin":   {"base_ac": 5, "hd": "6**",  "save": "F6",  "morale": 0},
    "Hellion":   {"base_ac": 6, "hd": "8**",  "save": "F8",  "morale": 0},
    "Incubus":   {"base_ac": 7, "hd": "10***","save": "F10", "morale": +1},
    "Demon":     {"base_ac": 8, "hd": "12***","save": "F12", "morale": +1},
    "Dybbuk":    {"base_ac": 9, "hd": "14***","save": "F14", "morale": +1},
    "Devil":     {"base_ac":10, "hd": "16****","save": "F16","morale": +2},
    "Fiend":     {"base_ac":11, "hd": "18*****","save": "F18","morale": +2},
    "Archfiend": {"base_ac":12, "hd": "20*******","save": "F20","morale": +3}
}

def generate_primary_stats(rank, ac_mod=0):
    stats = rank_primary_stats[rank]
    total_ac = stats["base_ac"] + ac_mod
    return {
        "ac": total_ac,
        "hd": stats["hd"],
        "save": stats["save"],
        "morale": stats["morale"]
    }


# In[5]:


spell_lists = {
    1: ["Beguile Humanoid", "Choking Grip", "Fan of Flames", "Frighten Humanoid", "Infuriate Humanoid", "Slumber"],
    2: ["Bewitch Humanoid", "Bloody Flux", "Dark Whisper", "Dominate Humanoid", "Halt Humanoids", "Hypnotic Sigil", 
        "Necromantic Potence", "Physical Protection", "Rain of Vitriol", "Shrouding Fog", "Webbing"],
    3: ["Bewitch Crowd", "Boil Blood", "Cone of Frost", "Dismember", "Fireball", "Flight", "Incite Madness", 
        "Dominate Monster", "Infuriate Crowd", "Invisibility", "Skinchange"],
    4: ["Bewitch Monster", "Cloud of Poison", "Cone of Fear", "Flesh to Ash", "Halt Monsters", "Inferno", 
        "Physical Invulnerability", "Deep Slumber"],
    5: ["Carnage", "Circle of Agony", "Cone of Paralysis", "Deflect Ordinary Weapons", "Fillet and Serve", 
        "Firestorm", "Flay the Slain", "Forgetfulness", "Teleportation"],
    6: ["Anti-Magic Sphere", "Conflagration", "Disfigure Body and Soul", "Disintegration", "Enslave Humanoid", 
        "Madness of Crowds", "Necromantic Invulnerability", "Panic", "Petrification", "Soul Eating", "Transform Other"]
}

spell_slots_by_rank = {
    "Spawn":     {"level": 2,  "slots": [2, 0, 0, 0, 0, 0]},
    "Imp":       {"level": 4,  "slots": [2, 2, 0, 0, 0, 0]},
    "Gremlin":   {"level": 6,  "slots": [2, 2, 2, 0, 0, 0]},
    "Hellion":   {"level": 8,  "slots": [3, 3, 2, 2, 0, 0]},
    "Incubus":   {"level": 10, "slots": [3, 3, 3, 3, 2, 0]},
    "Demon":     {"level": 12, "slots": [4, 4, 4, 3, 3, 2]},
    "Dybbuk":    {"level": 14, "slots": [4, 4, 4, 4, 3, 3]},
    "Devil":     {"level": 16, "slots": [4, 4, 4, 4, 4, 4]},
    "Fiend":     {"level": 18, "slots": [5, 5, 5, 5, 4, 4]},
    "Archfiend": {"level": 20, "slots": [5, 5, 5, 5, 5, 5]}
}

def generate_spellcasting(rank, can_speak):
    if not can_speak:
        return "None"

    rank = rank.capitalize()
    spell_info = spell_slots_by_rank[rank]
    spell_output = {}

    for level, slots in enumerate(spell_info["slots"], start=1):
        available_spells = spell_lists[level]
        if slots > 0:
            spell_output[f"Level {level}"] = random.sample(available_spells, min(slots, len(available_spells)))

    return {
        "caster_level": spell_info["level"],
        "spells": spell_output
    }


def generate_spell_like_abilities(rank):
    sla_output = {}
    total_cost = 0
    number_abilities = random.randint(1, 4)
    
    max_level_ref = {
        "Spawn":     1,
        "Imp":       2,
        "Gremlin":   3,
        "Hellion":   4,
        "Incubus":   5,
        "Demon":     6,
        "Dybbuk":    6,
        "Devil":     6,
        "Fiend":     6,
        "Archfiend": 6
    }

    usage_factors = {
        "At will": 1.0,
        "1/turn": 0.8,
        "1/3 turns": 0.7,
        "1/hour": 0.6,
        "3/day": 0.5,
        "1/day": 0.4,
    }

    max_level = max_level_ref[rank]

    for i in range(number_abilities):
        sla_output[i] = {}

        if random.random() > 0.9:
            act_level = max(int(max_level / 2), 1)
        else:
            act_level = max(int(max_level / 2) - 1, 1)

        sla_output[i]["spell"] = random.choice(spell_lists[act_level])
        usage_choice = random.choice(list(usage_factors.items()))
        sla_output[i]["usage_string"] = usage_choice[0]
        sla_output[i]["cost"] = 2 * act_level * usage_choice[1]
        total_cost += sla_output[i]["cost"] 

    return [sla_output, total_cost]


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[6]:


import pandas as pd
import random

# Load the CSV file with the full special abilities table
df_full = pd.read_csv("Cacodemon_Special_Abilities.csv")

# Helper to parse roll range from the "Roll" column
def parse_roll_range(roll_str):
    if '-' in roll_str:
        start, end = map(int, roll_str.split('-'))
        return range(start, end + 1)
    else:
        val = int(roll_str)
        return range(val, val + 1)

# Build a lookup table for fast access
lookup_table = []
for _, row in df_full.iterrows():
    roll_range = parse_roll_range(str(row["Roll"]))
    lookup_table.append((roll_range, row))

# Function to roll a random ability
def roll_special_ability():
    roll = random.randint(1, 100)
    for roll_range, row in lookup_table:
        if roll in roll_range:
            return {
                "roll": roll,
                "name": row["Name"],
                "cost": row["Cost"],
                "description": row["Description"]
            }

# Cost calculator
def compute_ability_cost(cost_str):
    if not isinstance(cost_str, str):
        return 0
    if '*' in cost_str and '#' in cost_str:
        return cost_str.count('*') + cost_str.count('#') * 0.125
    elif '*' in cost_str:
        return cost_str.count('*')
    elif '#' in cost_str:
        return cost_str.count('#') * 0.125
    else:
        return None  # For "varies" or "* or more"


def value_symbols(cost):
    """Render a numeric special-ability cost in the book's */# notation,
    where * = 1 and # = 1/8. E.g. 1.5 -> '*####', 0.5 -> '####'."""
    eighths = round(cost / 0.125)
    return "*" * (eighths // 8) + "#" * (eighths % 8)


# --- Immunity / Resistance coverage model ----------------------------------
#
# Damage sits on two independent axes:
#   * Nature -- Physical vs Energy. This is the game's own (non-intuitive)
#     grouping of the twelve types; Acidic, Arcane and Poisonous are *physical*.
#   * Source -- mundane (the default) or extraordinary (a tag any type can
#     carry). "Extraordinary fire" and "mundane fire" are both possible.
#
# Coverage is tracked as a set of (type, source) "atoms" so that overlapping
# clauses can be intersected exactly -- which is what turns doubled resistance
# into immunity.
PHYSICAL_TYPES = ["Acidic", "Arcane", "Bludgeoning", "Piercing", "Poisonous", "Slashing"]
ENERGY_TYPES = ["Cold", "Electrical", "Fire", "Luminous", "Necrotic", "Seismic"]
ALL_DAMAGE_TYPES = PHYSICAL_TYPES + ENERGY_TYPES
INNATE_RESISTANCES = ["Acidic", "Cold", "Electrical", "Fire", "Poisonous", "Seismic"]
SOURCES = ("mundane", "extraordinary")

# Effect-only clauses (no damage type); the token stored for each.
EFFECT_SELECTORS = {9: "enchantment", 10: "death", 11: "transmogrification"}


def clause_atoms(clause):
    """Expand a rolled Immunity/Resistance clause into the coverage it grants.

    A clause is ``{"selector": 1..11, "picks": [types] | None}`` where the
    selector matches the book's 1d12 table (the "12 -> roll twice" case is
    handled by rolling two clauses, so only 1..11 appear here). Returns
    ``(damage_atoms, effect_tokens)`` -- a set of ``(type, source)`` pairs and a
    set of effect-name strings.
    """
    selector = clause["selector"]
    picks = clause.get("picks")

    if selector == 1:                                   # all mundane damage
        return ({(t, "mundane") for t in ALL_DAMAGE_TYPES}, set())
    if selector == 2:                                   # all extraordinary damage
        return ({(t, "extraordinary") for t in ALL_DAMAGE_TYPES}, set())
    if selector == 3:                                   # all physical damage
        return ({(t, s) for t in PHYSICAL_TYPES for s in SOURCES}, set())
    if selector == 4:                                   # all energy damage
        return ({(t, s) for t in ENERGY_TYPES for s in SOURCES}, set())
    if selector in (5, 6):                              # any N damage types
        return ({(t, s) for t in picks for s in SOURCES}, set())
    if selector == 7:                                   # all mundane physical
        return ({(t, "mundane") for t in PHYSICAL_TYPES}, set())
    if selector == 8:                                   # any 3 mundane types
        return ({(t, "mundane") for t in picks}, set())
    if selector in EFFECT_SELECTORS:                    # enchantment/death/transmog
        return (set(), {EFFECT_SELECTORS[selector]})
    raise ValueError(f"Unknown clause selector: {selector}")


def resolve_coverage(immunity_clauses, resistance_clauses, innate=None):
    """Resolve every Immunity/Resistance clause into the imp's final coverage.

      * The Immunity ability's atoms are immunity outright.
      * Resistance stacks: any atom held by two or more resistance sources --
        the innate base counting as one source -- upgrades to immunity.
      * Immunity always supersedes resistance.

    Returns a dict with ``immune_damage`` / ``immune_effects`` and the surviving
    resistances split into ``base_resist`` (innate-derived) and
    ``additional_resist_damage`` / ``additional_resist_effects`` (from the
    Resistance ability).
    """
    innate = INNATE_RESISTANCES if innate is None else innate
    innate_atoms = {(t, s) for t in innate for s in SOURCES}

    # Immunity-ability coverage.
    imm_dmg, imm_eff = set(), set()
    for clause in immunity_clauses:
        d, e = clause_atoms(clause)
        imm_dmg |= d
        imm_eff |= e

    # Doubling counts only the ROLLED resistance clauses. The innate base is NOT
    # a stacking source: rolling a type you already resist innately is wasted,
    # and only two *rolls* of the same atom upgrade it to immunity.
    rolled_dmg = [clause_atoms(c)[0] for c in resistance_clauses]
    rolled_eff = [clause_atoms(c)[1] for c in resistance_clauses]
    dmg_counts = Counter(atom for src in rolled_dmg for atom in src)
    eff_counts = Counter(tok for src in rolled_eff for tok in src)
    doubled_dmg = {atom for atom, n in dmg_counts.items() if n >= 2}
    doubled_eff = {tok for tok, n in eff_counts.items() if n >= 2}

    immune_damage = imm_dmg | doubled_dmg
    immune_effects = imm_eff | doubled_eff

    rolled_resist_damage = set(dmg_counts) - immune_damage
    rolled_resist_effects = set(eff_counts) - immune_effects

    return {
        "immune_damage": immune_damage,
        "immune_effects": immune_effects,
        # Innate stays resistance unless the immunity ability or a doubled roll
        # covered it. Additional drops anything already innate (that's the
        # wasted "tough luck" roll).
        "base_resist": innate_atoms - immune_damage,
        "additional_resist_damage": rolled_resist_damage - innate_atoms,
        "additional_resist_effects": rolled_resist_effects,
    }


def describe_coverage(damage_atoms, effect_tokens):
    """Render a coverage atom set as readable stat-block text.

    Types covered in both sources print bare ("Fire"); a single source is
    prefixed ("mundane Fire"). Whole categories collapse to their name
    ("all physical damage"), and a scope that is all-but-one-or-two types
    collapses to "all ... damage except X, Y". Returns "None" when empty.
    """
    by_type = {}
    for (t, s) in damage_atoms:
        by_type.setdefault(t, set()).add(s)

    full = {t for t, srcs in by_type.items() if srcs == {"mundane", "extraordinary"}}
    mundane_only = {t for t, srcs in by_type.items() if srcs == {"mundane"}}
    extra_only = {t for t, srcs in by_type.items() if srcs == {"extraordinary"}}

    def order_list(types):
        return ", ".join(sorted(types))     # alphabetical, for stable display

    def phrase(types, source_word):
        prefix = (source_word + " ") if source_word else ""
        allset = set(ALL_DAMAGE_TYPES)
        if types == allset:
            return f"all {prefix}damage"
        missing = allset - types
        if len(missing) <= 2:
            return f"all {prefix}damage except {order_list(missing)}"
        if types == set(PHYSICAL_TYPES):
            return f"all {prefix}physical damage"
        if types == set(ENERGY_TYPES):
            return f"all {prefix}energy damage"
        return f"{prefix}{order_list(types)}"

    parts = []
    if full:
        parts.append(phrase(full, ""))
    if mundane_only:
        parts.append(phrase(mundane_only, "mundane"))
    if extra_only:
        parts.append(phrase(extra_only, "extraordinary"))
    for tok in ("enchantment", "death", "transmogrification"):
        if tok in effect_tokens:
            parts.append(f"all {tok} effects")

    return "; ".join(parts) if parts else "None"


def describe_ability_rolls(structured):
    """Render an Immunity/Resistance ability's raw rolls for the ability block,
    so a reader can see how the stat-block roll-up was reached. Immunity has one
    roll; Resistance's two rolls are labelled "Roll 1"/"Roll 2"."""
    verb = "Immune to" if structured["kind"] == "immunity" else "Resists"
    clauses = structured["clauses"]
    parts = []
    for i, clause in enumerate(clauses, 1):
        prefix = f"Roll {i}: " if len(clauses) > 1 else ""
        parts.append(f"{prefix}{verb} {describe_coverage(*clause_atoms(clause))}")
    return "; ".join(parts)


# Per-selector costs (in special-ability units) for the two abilities. These
# match the book's symbols and the previous inline ladders exactly.
IMMUNITY_COST = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: .5, 7: .5, 8: .25, 9: .5, 10: .5, 11: .5}
RESISTANCE_COST = {1: .5, 2: .5, 3: .5, 4: .5, 5: .5, 6: .25, 7: .25, 8: .125, 9: .25, 10: .25, 11: .25}

# How many damage types each picking selector samples.
_PICK_COUNT = {5: 6, 6: 3, 8: 3}


def _roll_clause():
    """Roll one Immunity/Resistance clause: a 1d11 selector plus, for the
    type-picking selectors, the sampled types. Picks are drawn from all twelve
    types -- the old innate-type exclusion is gone, because a roll landing on an
    innate type now stacks to immunity rather than being wasted."""
    selector = random.randint(1, 11)
    count = _PICK_COUNT.get(selector)
    picks = random.sample(ALL_DAMAGE_TYPES, count) if count else None
    return {"selector": selector, "picks": picks}


def _reroll_if_redundant(clause, immune_atoms, immune_effects, attempts=50):
    """The book's "re-roll if already immune": if a resistance clause is wholly
    covered by the Immunity ability it grants nothing, so replace it with
    another clause of the SAME cost tier that adds something. Cost is preserved
    so the ability's budgeted total does not shift. Gives up (keeps the clause)
    if no better same-cost clause turns up."""
    def redundant(c):
        d, e = clause_atoms(c)
        return d <= immune_atoms and e <= immune_effects

    if not redundant(clause):
        return clause
    tier = RESISTANCE_COST[clause["selector"]]
    for _ in range(attempts):
        candidate = _roll_clause()
        if RESISTANCE_COST[candidate["selector"]] == tier and not redundant(candidate):
            return candidate
    return clause


def _resolve_demon_coverage(abilities):
    """Resolve the Immunity/Resistance abilities in a selected-abilities list
    into the imp's net coverage. Applies the immunity re-roll guard first (only
    meaningful when the imp has both abilities), then folds everything -- innate
    base included -- through resolve_coverage."""
    imm = next((a for a in abilities if a["name"] == "Immunity"), None)
    res = next((a for a in abilities if a["name"] == "Resistance"), None)

    immunity_clauses = imm["detail"][2]["clauses"] if imm else []
    resistance_clauses = res["detail"][2]["clauses"] if res else []

    if imm and res:
        immune_atoms, immune_effects = set(), set()
        for c in immunity_clauses:
            d, e = clause_atoms(c)
            immune_atoms |= d
            immune_effects |= e
        resistance_clauses = [
            _reroll_if_redundant(c, immune_atoms, immune_effects)
            for c in resistance_clauses
        ]
        res["detail"][2]["clauses"] = resistance_clauses
        # Keep the raw ability text in sync with the (possibly re-rolled) clauses.
        res["detail"][0] = describe_ability_rolls(res["detail"][2])

    return resolve_coverage(immunity_clauses, resistance_clauses)


def coverage_stat_lines(resolved):
    """The three ordered (label, text) coverage lines for the stat block."""
    return [
        ("Immunities",
         describe_coverage(resolved["immune_damage"], resolved["immune_effects"])),
        ("Base Resistances",
         describe_coverage(resolved["base_resist"], set())),
        ("Additional Resistances",
         describe_coverage(resolved["additional_resist_damage"],
                           resolved["additional_resist_effects"])),
    ]


# Additional info:
def ability_details(name, rank):
    info = ""
    cost = -1
    structured = None       # Immunity/Resistance stash their rolled clauses here

    aura_damage_types = [
        "Arcane",
        "Acidic",
        "Cold",
        "Electrical",
        "Fire",
        "Necrotic",
        "Poisonous",
        "Seismic"
    ]
    
    class_powers = [
        "Acrobatics",
        "Ambushing",
        "Combat Ferocity",
        "Combat Reflexes",
        "Kin-Slaying",
        "Skirmishing",
        "Swashbuckling",
        "Weapon Focus",
        "Aura of Protection (JJ309)",
        "Dark Blessing (JJ314)",
        "Martial Talent (JJ321)",
        "Scaly Hide (JJ324)",
        "Inexorable (JJ325)"
    ]
    
    if name == 'Aura':
        info = random.choice(aura_damage_types)
        cost = 1
        
    elif name == 'Bonus Attack':
        if random.random() > .5:
            info = "One extra attack, damage equal to its primary attack"
        else:
            info = "Two extra attacks, damage half its primary attack"
        cost = .25
            
    elif name == 'Breath Weapon':
        info = random.choice(aura_damage_types)
        cost = 1
        
    elif name == 'Class Powers/Proficiencies':
        totalPowers = random.randint(1, 4)
        selected = []
        seen_powers = set()

        while len(selected) < totalPowers:
            power = random.choice(class_powers)
            if power in seen_powers:
                continue  # Skip "varies"/non-numeric costs or duplicates

            selected.append(power)
            seen_powers.add(name)
        info = str(selected)
        cost = .125 * totalPowers
        
    elif name == 'Grab/Restrain':
        selector = random.randint(1, 20)
        if selector <= 14:
            info = "Constriction attack that deals damage equal to its primary attack and restrains any creature struck that is smaller than the cacodemon"
        elif selector in (15, 16, 17):
            info =  "If it hits a creature smaller than itself with at least two of its secondary attacks, the creature struck must make a successful size-adjusted Paralysis save or be grabbed"
        elif selector in (18, 19, 20):
            info = "if it hits a creature smaller than itself with its primary attack, the creature struck must make a successful size-adjusted Paralysis save or be grabbed."
        cost = 1
        
    elif name == "Immunity":
        # Roll one clause. The raw roll is shown in the ability block (info); the
        # resolved net coverage is rolled up into the stat block separately.
        clause = _roll_clause()
        cost = IMMUNITY_COST[clause["selector"]]
        structured = {"kind": "immunity", "clauses": [clause]}
        info = describe_ability_rolls(structured)


    elif name == "Paralysis":
        selector = random.randint(1, 6)
        if selector <= 2:
            info = "Paralysis lasts 1d10 rounds"
        else:
            info = "Paralysis lasts 2d4 turns"
        cost = 1
            
    elif name == "Petrification":
        selector = random.randint(1, 6)
        if selector <= 3:
            info = "Cacodemon petrifies those that behold its gaze, as Medusa"
        else:
            info = "Cacodemon petrifies those that are struck by its attacks"
        cost = 2
            
    elif name == "Poison":
        selector = random.randint(1, 20)
        if selector <= 12:
            onset = "instant"
        elif selector <= 14:
            onset = "1 turn"
        elif selector <= 15:
            onset = "1d4 turns"
        elif selector <= 19:
            onset = "1d4+2 turns"
        elif selector == 20:
            onset = "1d10 turns"
        else:
            onset = "error"
            
        selector = random.randint(1, 20)
        if selector <= 16:
            effect = "death"
        elif selector <= 19:
            effect = "paralysis"
        elif selector == 20:
            effect = "incapacitation"
        else:
            effect = "error"
        
        info = "onset time: " + onset + "; effect: " + effect
        cost = 1
        
    elif name == "Resistance":
        # Roll twice. Overlaps between the two rolls stack up to immunity during
        # resolution (innate does not stack). The raw rolls show in the ability
        # block; the resolved net lands in the stat block's rolled-up lines.
        clauses = [_roll_clause(), _roll_clause()]
        cost = sum(RESISTANCE_COST[c["selector"]] for c in clauses)
        structured = {"kind": "resistance", "clauses": clauses}
        info = describe_ability_rolls(structured)


    elif name == 'Special Senses':
        sense_options = [
            ["Acute Hearing", .125],
            ["Acute Olfaction", .125],
            ["Acute Vision", .125],
            ["Night Vision", .125],
            ["Echolocation", .25],
            ["Mechanoreception", .25]
        ]
        sense = random.choice(sense_options)
        info = sense[0]
        cost = sense[1]
    
    elif name == "Tough":
        increase = random.randint(1, 4)
        info = "AC Increased by " + str(increase)
        cost = 0.25
        
    elif name == "Spell-like Abilities":
        sla_detail = generate_spell_like_abilities(rank)
        info = sla_detail[0]
        cost = sla_detail[1]

    return [info, cost, structured]

def should_reroll_ability(name, can_speak, size_category):
    # Add game-specific logic here
    if name == "Spellcasting" and not can_speak:
        return True
    if name in {"Swallow Attack", "Topple and Fling"} and size_category not in {"Huge", "Gigantic", "Colossal"}:
        return True
    if name in {"Trample", "Vicious Attack"} and size_category not in {"Large", "Huge", "Gigantic", "Colossal"}:
        return True
    return False


def roll_abilities_with_cost_limit(target_cost, can_speak, size_category, body_form, has_wings, rank, signature_choice=None):
    """
    Selects built-in form/wings abilities first, then rolls others until total cost meets or exceeds target.

    signature_choice controls the form's signature ability:
        None  -> random (90% chance), the default / off-mode behavior
        True  -> force-include it
        False -> force-exclude it
    In every case its cost is counted against target_cost, because it is added
    before the roll loop below.
    """
    selected = []
    seen = set()
    total = 0.0

    def add_builtin(name, book_cost=None, description_override=None):
        """Add a form/wings ability. book_cost and description default to the
        table row; pass them explicitly for abilities not in the table
        (e.g. Dive Attack). The cost always comes from the book_cost symbols."""
        row = df_full.loc[df_full["Name"] == name]
        if book_cost is None:
            book_cost = row["Cost"].iloc[0]
        if description_override is not None:
            desc = description_override
        elif not row.empty:
            desc = row["Description"].iloc[0]
        else:
            desc = ""
        cost_val = compute_ability_cost(book_cost) or 1
        detail = ability_details(name, None)

        selected.append({"roll": "auto", "name": name, "cost": cost_val,
                         "book_cost": book_cost, "description": desc, "detail": detail})
        seen.add(name)
        return cost_val

    # Built-in logic based on wings and body form. Flying is always granted to
    # winged forms; the signature ability depends on signature_choice.
    if has_wings and "Flying" not in seen:
        total += add_builtin(
            "Flying",
            description_override="The Cacodemon can fly at the speed noted for its body form."
        )

    if signature_choice is None:
        include_signature = random.random() < 0.9
    elif isinstance(signature_choice, bool):
        include_signature = signature_choice          # True -> always, False -> never
    else:
        include_signature = random.random() < signature_choice   # probability in [0, 1]

    if include_signature:
        if body_form == "Arachnine" and "Poison" not in seen:
            total += add_builtin("Poison")
        elif body_form == "Monadine" and "Swallow Attack" not in seen \
                and size_category in {"Huge", "Gigantic", "Colossal"}:
            total += add_builtin("Swallow Attack")
        elif body_form == "Scolopendrine" and "Paralysis" not in seen:
            total += add_builtin("Paralysis")
        elif body_form == "Wyverine":
            if has_wings and "Dive Attack" not in seen:
                total += add_builtin(
                    "Dive Attack",
                    book_cost="####",
                    description_override=(
                        "The Cacodemon can make dive attacks that deal double damage. "
                        "If a dive hits a victim smaller than itself, it grabs and carries him off, "
                        "unless the victim makes a successful size-adjusted Paralysis save."
                    ),
                )
            elif not has_wings and "Berserk" not in seen:
                total += add_builtin("Berserk")

    # Roll additional abilities to fill the allotment WITHOUT going over it, so
    # the values add up to (at most) target_cost. Abilities that would overshoot
    # are skipped. The attempt cap prevents an unfillable remainder (possible
    # only with an odd, non-1/8 cost) from looping forever.
    attempts = 0
    while total < target_cost - 1e-9 and attempts < 200:
        attempts += 1
        abil = roll_special_ability()
        name, cost_str = abil["name"], abil["cost"]
        if name in seen or should_reroll_ability(name, can_speak, size_category):
            continue  # Skip duplicates or invalid ones

        cost_val = compute_ability_cost(cost_str) or 1
        abil["detail"] = ability_details(name, rank)
        if abil["detail"][1] > 0:
            cost_val = abil["detail"][1]
        if total + cost_val > target_cost + 1e-9:
            continue  # would exceed the allotment -> leave it out

        abil["book_cost"] = cost_str   # raw book symbols (*, #, varies)
        abil["cost"] = cost_val        # numeric value for internal budget use
        selected.append(abil)
        seen.add(name)
        total += cost_val

    return {"total_cost": round(total, 3), "abilities": selected}


# # Example usage
# if __name__ == "__main__":
#     result = roll_abilities_with_cost_limit(3, True, "Small", "Wyverine", False, "Hellion")
# #     print(result["abilities"])
#     for ab in result["abilities"]:
# #         print(f"- {ab['name']} ({ab['cost']}): {ab['description']}\n")
#         print(f"- {ab['name']} ({ab['cost']}): {ab['description']} {ab['detail']}\n")
#     print("Total Cost:", result["total_cost"])


# In[ ]:





# In[7]:


def size_calc(hd, bme):
    weight = (10*hd) ** bme
    if weight <= 35:
        return {"category": "Small", "length": "Less than 7' long/tall"}
    elif weight <= 400:
        return {"category": "Man-Sized", "length": "Less than 8' long/tall"}
    elif weight <= 2000:
        return {"category": "Large", "length": "8' to 12' long/tall"}
    elif weight <= 8000:
        return {"category": "Huge", "length": "12' to 20' long/tall"}
    elif weight <= 32000:
        return {"category": "Gigantic", "length": "20' to 32' long/tall"}
    else:
        return {"category": "Colossal", "length": "32' or more long/tall"}


# In[ ]:





# In[13]:


# Used names are crossed off a persistent list on disk, next to this module, so
# they are not reused across runs. (On an ephemeral host such as Streamlit Cloud
# the file is reset whenever the container is rebuilt by a reboot or redeploy.)
_USED_NAMES_FILE = os.path.join(os.path.dirname(__file__), "used_names.json")


def _load_used_names():
    try:
        with open(_USED_NAMES_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, ValueError):
        return set()


def _save_used_names(used):
    with open(_USED_NAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(used), f)


def reset_used_names():
    """Clear the persistent record of used names."""
    _save_used_names(set())


def assign_imp_name():
    """Return a name not yet crossed off the list and cross it off on disk.
    When every name has been used, the list starts over."""
    used = _load_used_names()
    available = [n for n in IMP_NAMES if n not in used]
    if not available:
        used = set()
        available = list(IMP_NAMES)
    name = random.choice(available)
    used.add(name)
    _save_used_names(used)
    return name


def generate_cacodemon_base(rank, body_form_roll = None, body_form = None, signature_choice = None, uses_speech = False):
    # Define rank traits
    rank_traits = {
        "Spawn": {"special_abilities": 2, "speak_chance": 0.01},
        "Imp": {"special_abilities": 2, "speak_chance": 0.02},
        "Gremlin": {"special_abilities": 2, "speak_chance": 0.05},
        "Hellion": {"special_abilities": 2, "speak_chance": 0.10},
        "Incubus": {"special_abilities": 3, "speak_chance": 0.20},
        "Demon": {"special_abilities": 3, "speak_chance": 0.35},
        "Dybbuk": {"special_abilities": 3, "speak_chance": 0.50},
        "Devil": {"special_abilities": 4, "speak_chance": 0.76},
        "Fiend": {"special_abilities": 6, "speak_chance": 1.00},
        "Archfiend": {"special_abilities": 7, "speak_chance": 1.00}
    }

    # Validate rank
    if rank not in rank_traits:
        raise ValueError(f"Unknown rank: {rank}")

    traits = rank_traits[rank]
    # Speech is off by default. With no speech there is no spellcasting: the
    # Spellcasting special ability is rerolled (see should_reroll_ability) and
    # generate_spellcasting short-circuits to "None".
    can_speak = uses_speech

    # Determine body form
    if body_form is not None:
        # Choice Mode: the form was picked by the caller; wings are still
        # rolled randomly (50/50, matching the odds of the random path).
        has_wings = random.random() < 0.5
    else:
        if body_form_roll is None:
            body_form_roll = random.randint(1, 10)
        if body_form_roll <= 2:
            body_form = "Arachnine"
        elif body_form_roll <= 4:
            body_form = "Humanoid"
        elif body_form_roll <= 6:
            body_form = "Monadine"
        elif body_form_roll <= 8:
            body_form = "Scolopendrine"
        else:
            body_form = "Wyverine"
        has_wings = body_form_roll % 2 == 1


        
    combat_stats = generate_form_combat_stats(body_form, rank)
    primary_stats = generate_primary_stats(rank, combat_stats["ac_mod"])
    
    hd_num = int(re.sub(r'\D', '', primary_stats["hd"]))
    attack_throw = str(max(-9, 11-hd_num)) + "+"
    size = size_calc(hd_num, combat_stats["bme"])
    hit_points = sum(random.randint(1, 8) for _ in range(hd_num))  # hd_num d8 (4d8 for an Imp)
    
    abilities = roll_abilities_with_cost_limit(traits["special_abilities"], can_speak, size["category"], body_form, has_wings, rank, signature_choice)

    for ab in abilities["abilities"]:
        if ab['name'] == "Spellcasting":
            can_speak = True

    spellcasting = generate_spellcasting(rank, can_speak)

    # Fold the Immunity/Resistance abilities (and the innate base) into the net
    # coverage shown on the stat block.
    coverage = _resolve_demon_coverage(abilities["abilities"])

    return {
        "name": assign_imp_name(),
        "rank": rank,
        "num_special_abilities": traits["special_abilities"],
        "can_speak": can_speak,
        "body_form": [body_form, has_wings],
        "primary_stats": primary_stats,
        "combat_stats": combat_stats,
        "attack": attack_throw,
        "hit_points": hit_points,
        "spells": spellcasting,
        "abilities": abilities,
        "coverage": coverage,
        "size: ": size
    }


# In[ ]:





# In[9]:


def print_cacodemon_statblock(cacodemon):
    print(f"{cacodemon['rank']} Cacodemon")
    if cacodemon['body_form'][1]:
        wing_status = "Winged"
    else:
        wing_status = "Non-Winged"
    
    print(f"{'Form:':15} {cacodemon['body_form'][0]}, {wing_status}")
    
    print("-" * 50)

    size_data = cacodemon.get('size: ', {})
    combat = cacodemon.get('combat_stats', {})
    movement = combat.get('movement', {})
    primary = cacodemon.get('primary_stats', {})
    
    myAC = primary.get('ac', 0)
    flySpeed = 'None'
    has_flying = False
    landSpeed = movement.get('land', '-')

    sense = 'None'
    
    for ab in cacodemon['abilities']['abilities']:
        if ab['name'] == "Flying":
            has_flying = True
            flySpeed = movement.get('fly', '-')
        if ab['name'] == "Special Senses":
            sense = ab['detail'][0]
    
    if 'or' in landSpeed:
        options = landSpeed.split('or')
        # Choose based on flying
        landSpeed = options[1].strip() if has_flying else options[0].strip()

    



    print(f"{'Size:':15} {size_data.get('category', 'Unknown')}")
    print(f"{'Speed (land):':15} {landSpeed}")
    print(f"{'Speed (fly):':15} {flySpeed}")
    print(f"{'Speed (climb):':15} {movement.get('climb', '-')}")
    print(f"{'Speed (swim):':15} {movement.get('swim', '-')}")
    print(f"{'Armor Class:':15} {myAC}")
    print(f"{'Hit Dice:':15} {primary.get('hd', '-')}")
    print(f"{'Attacks:':15} {combat.get('attack_routine', '-')}, {cacodemon['attack']}")
    print(f"{'Damage:':15} {', '.join(combat.get('damage', []))}")
    print(f"{'Save:':15} {primary.get('save', '-')}")
    print(f"{'Morale:':15} {primary.get('morale', '-')}")
    vision = "Lightless Vision (90')"
    print(f"{'Vision:':15} {vision}")
    print(f"{'Other Senses:':15} {sense}")  # You can replace this with a real value if defined

    print("\nSpecial Abilities:")
    print("-" * 50)
    
    
    resolved = cacodemon.get("coverage") or _resolve_demon_coverage(
        cacodemon['abilities']['abilities']
    )
    print("\nResistances & Immunities:")
    print(f"{'-' * 25}")
    for label, text in coverage_stat_lines(resolved):
        print(f"{label}: {text}")

    print("\nTelepathy")
    print(f"{'-' * 9}")
    print("Can communicate telepathically with any creatures they encounter")
    
    
    for ab in cacodemon['abilities']['abilities']:
        name = ab['name']
        desc = ab['description']
        print(f"\n{name}")
        print(f"{'-' * len(name)}")
        print(desc)
        if ab['detail'][0] != '' and ab['detail'][0] != "(":
            print("Detail:")
            if isinstance(ab['detail'][0], dict):
                for spell_info in ab['detail'][0].values():
                    print(f"  {spell_info['spell']}: {spell_info['usage_string']}")
            else:
                print(f"  {ab['detail'][0]}")

    print("\nSpellcasting:")
    print("-" * 50)

    spells_data = cacodemon.get("spells", "None")
    if spells_data == "None":
        print("None")
    elif isinstance(spells_data, dict) and "spells" in spells_data:
        print(f"Caster Level: {spells_data.get('caster_level', '?')}")
        for level, spell_list in spells_data["spells"].items():
            if isinstance(spell_list, list):
                print(f"{level}: {', '.join(spell_list)}")
            elif isinstance(spell_list, str):
                print(f"{level}: {spell_list}")
            else:
                print(f"{level}: [Unrecognized spell format]")
    else:
        print("Unrecognized spell format.")


def format_stats_block(cacodemon):
    """Return just the Size -> Other Senses stat lines as text.

    Land speed depends on whether the demon can fly, and Other Senses come from
    the Special Senses ability if present.
    """
    lines = []

    size_data = cacodemon.get('size: ', {})
    combat = cacodemon.get('combat_stats', {})
    movement = combat.get('movement', {})
    primary = cacodemon.get('primary_stats', {})

    myAC = primary.get('ac', 0)
    flySpeed = 'None'
    has_flying = False
    landSpeed = movement.get('land', '-')
    sense = 'None'

    for ab in cacodemon['abilities']['abilities']:
        if ab['name'] == "Flying":
            has_flying = True
            flySpeed = movement.get('fly', '-')
        if ab['name'] == "Special Senses":
            sense = ab['detail'][0]

    if 'or' in landSpeed:
        options = landSpeed.split('or')
        landSpeed = options[1].strip() if has_flying else options[0].strip()

    hp = cacodemon.get('hit_points', '-')
    resolved = cacodemon.get("coverage") or _resolve_demon_coverage(
        cacodemon['abilities']['abilities']
    )

    lines.append(f"{'Size:':15} {size_data.get('category', 'Unknown')}")
    lines.append(f"{'Speed (land):':15} {landSpeed}")
    lines.append(f"{'Speed (fly):':15} {flySpeed}")
    lines.append(f"{'Speed (climb):':15} {movement.get('climb', '-')}")
    lines.append(f"{'Speed (swim):':15} {movement.get('swim', '-')}")
    lines.append(f"{'Armor Class:':15} {myAC}")
    lines.append(f"{'Hit Dice:':15} {primary.get('hd', '-')}")
    lines.append(f"{'Hit Points:':15} {hp}")
    lines.append(f"{'Attacks:':15} {combat.get('attack_routine', '-')}, {cacodemon['attack']}")
    lines.append(f"{'Damage:':15} {', '.join(combat.get('damage', []))}")
    lines.append(f"{'Save:':15} {primary.get('save', '-')}")
    lines.append(f"{'Morale:':15} {primary.get('morale', '-')}")
    lines.append(f"{'Vision:':15} Lightless Vision (90')")
    lines.append(f"{'Other Senses:':15} {sense}")
    for label, text in coverage_stat_lines(resolved):
        lines.append(f"{label + ':':24} {text}")
    lines.append(f"{'Languages:':24} None (but uses Telepathy)")

    return "\n".join(lines)




