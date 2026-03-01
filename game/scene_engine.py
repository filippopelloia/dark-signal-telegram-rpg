import json
import os
import random
from typing import Optional
from database.models import Player


# Load all chapter data
_chapters: dict[int, dict] = {}

def load_chapters():
    scenes_dir = os.path.join(os.path.dirname(__file__), "scenes")
    for fname in os.listdir(scenes_dir):
        if fname.endswith(".json"):
            path = os.path.join(scenes_dir, fname)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            ch_num = data.get("chapter", 0)
            _chapters[ch_num] = data

load_chapters()


def get_scene(scene_id: str, chapter: int = None) -> Optional[dict]:
    """Get a scene dict by its ID"""
    if chapter:
        ch = _chapters.get(chapter)
        if ch:
            return ch["scenes"].get(scene_id)
    # Search all chapters
    for ch_data in _chapters.values():
        scene = ch_data["scenes"].get(scene_id)
        if scene:
            return scene
    return None


def get_lore_entry(lore_id: str) -> Optional[dict]:
    for ch_data in _chapters.values():
        entry = ch_data.get("lore_entries", {}).get(lore_id)
        if entry:
            return entry
    return None


def get_chapter_intro(chapter: int, lang: str) -> str:
    ch = _chapters.get(chapter)
    if ch:
        return ch.get("intro", {}).get(lang, ch.get("intro", {}).get("en", ""))
    return ""


def get_scene_text(scene: dict, lang: str) -> str:
    text = scene.get("text", {})
    return text.get(lang, text.get("en", ""))


def get_choice_text(choice: dict, lang: str) -> str:
    text = choice.get("text", {})
    return text.get(lang, text.get("en", ""))


def get_locked_reason(choice: dict, lang: str) -> str:
    reason = choice.get("locked_reason", {})
    if isinstance(reason, dict):
        return reason.get(lang, reason.get("en", "Locked"))
    return str(reason)


def check_choice_requirement(choice: dict, player: Player) -> tuple[bool, str]:
    """Returns (can_use, reason_if_locked)"""
    req = choice.get("requires")
    if not req:
        return True, ""
    
    # Stat requirement
    if "stat" in req:
        stat_name = req["stat"]
        required_val = req["value"]
        player_val = getattr(player, stat_name, 0)
        if player_val < required_val:
            return False, ""  # caller handles reason
    
    # Item requirement
    if "item" in req:
        item_map = {
            "motion_tracker": "motion_tracker",
            "terminal_access": "terminal_access",
            "pulse_rifle": "pulse_rifle",
            "blade": "blade",
            "medkit": "medkit"
        }
        item_key = item_map.get(req["item"], req["item"])
        if not player.has_item(item_key):
            return False, ""
    
    # Flag requirement
    if "flag" in req:
        flag_key = req["flag"]
        flag_val = req.get("flag_value", True)
        if player.get_flag(flag_key) != flag_val:
            return False, ""
    
    return True, ""


def apply_scene_effects(scene: dict, player: Player) -> list[str]:
    """Apply scene effects and return list of event strings for display"""
    effects = scene.get("effects", {})
    events = []
    
    if "xp" in effects:
        leveled = player.add_xp(effects["xp"])
        if leveled:
            events.append(f"level_up:{player.level}:{player.stat_points}")
    
    if "stress" in effects:
        delta = effects["stress"]
        if delta > 0:
            player.add_stress(delta)
        else:
            player.reduce_stress(abs(delta))
    
    if "hp" in effects:
        delta = effects["hp"]
        if delta > 0:
            player.heal(delta)
        else:
            player.take_damage(abs(delta))
    
    if "battery" in effects:
        player.battery = max(0, min(100, player.battery + effects["battery"]))
    
    # NPC relation changes
    for key, val in effects.items():
        if key.startswith("npc_") and key.endswith("_trust"):
            npc_id = key[4:-6]  # strip "npc_" and "_trust"
            player.change_npc_trust(npc_id, val)
    
    return events


def apply_choice_effects(choice: dict, player: Player) -> list[str]:
    events = []
    
    # Set flags
    flags_set = choice.get("flags_set", {})
    for k, v in flags_set.items():
        player.set_flag(k, v)
    
    # Apply effects
    effects = choice.get("effects", {})
    if effects:
        for key, val in effects.items():
            if key.startswith("npc_") and key.endswith("_trust"):
                npc_id = key[4:-6]
                player.change_npc_trust(npc_id, val)
            elif key == "stress":
                if val > 0:
                    player.add_stress(val)
                else:
                    player.reduce_stress(abs(val))
            elif key == "xp":
                leveled = player.add_xp(val)
                if leveled:
                    events.append(f"level_up:{player.level}:{player.stat_points}")
    
    # Add item
    item_add = choice.get("item_add")
    if item_add:
        item_key_map = {
            "datapad_b4": "datapad_b4",
            "petra_data_chip": "petra_data_chip"
        }
        player.add_item(item_key_map.get(item_add, item_add))
    
    # Unlock lore
    lore_unlock = choice.get("lore_unlock")
    if lore_unlock:
        player.add_lore(lore_unlock)
        events.append(f"lore:{lore_unlock}")
    
    return events


def process_scene_extras(scene: dict, player: Player) -> list[str]:
    """Process lore unlocks and achievements for a scene"""
    events = []
    
    lore_unlock = scene.get("lore_unlock")
    if lore_unlock:
        player.add_lore(lore_unlock)
        events.append(f"lore:{lore_unlock}")
    
    ach_unlock = scene.get("achievement_unlock")
    if ach_unlock:
        newly_unlocked = player.add_achievement(ach_unlock)
        if newly_unlocked:
            events.append(f"achievement:{ach_unlock}")
    
    chapter_complete = scene.get("chapter_complete")
    if chapter_complete:
        player.current_chapter = chapter_complete
        events.append(f"chapter_complete:{chapter_complete}")
    
    return events


def get_map_ascii(player: Player) -> str:
    maps = {
        "c1_shuttle": "🚀 USS CORTEZ — En Route",
        "c1_airlock": "🚪 THETA — Airlock Deck A",
        "c1_corridor_stealth": "🏃 THETA — Corridor Deck A",
        "c1_research_lab": "🔬 THETA — Research Lab Deck 3",
        "c1_find_survivor": "🆘 THETA — Deck 9",
        "c1_cliffhanger": "🏃 THETA — Emergency Stairwell",
    }
    scene = player.current_scene
    location = maps.get(scene, "📍 Location unknown")
    
    map_art = f"""
{location}

╔══════════════════╗
║  DECK A  [ENTRY] ║
║    Airlock ■■    ║
╠══════════════════╣
║  DECK 3  [LAB]   ║
║   Research ■■    ║
╠══════════════════╣
║  DECK 5  [CORE]  ║
║   Reactor ░░░    ║
╠══════════════════╣
║  DECK 7  [NESTS] ║
║   ??? ░░░░░░░    ║
╠══════════════════╣
║  DECK 9  [SURV]  ║
║   Survivor ■     ║
╚══════════════════╝
■ = Explored  ░ = Unknown
"""
    return map_art
