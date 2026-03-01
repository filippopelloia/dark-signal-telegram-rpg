import random
from dataclasses import dataclass
from typing import Optional
from database.models import Player


@dataclass
class Enemy:
    id: str
    hp: int
    max_hp: int
    damage_min: int
    damage_max: int
    dodge_chance: float  # 0.0–1.0
    flee_difficulty: int  # stat check value
    xp_reward: int
    is_architect: bool = False


ENEMIES = {
    "facehugger": Enemy("facehugger", 15, 15, 5, 12, 0.4, 3, 20),
    "drone": Enemy("drone", 30, 30, 8, 18, 0.3, 4, 40),
    "warrior": Enemy("warrior", 55, 55, 14, 26, 0.2, 6, 70),
    "architect": Enemy("architect", 80, 80, 16, 30, 0.35, 7, 120, is_architect=True),
    "praetorian": Enemy("praetorian", 130, 130, 22, 38, 0.15, 9, 200),
}


def roll(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)


def dice(notation: str) -> int:
    """Parse NdM notation like 2d8"""
    parts = notation.lower().split("d")
    n, m = int(parts[0]), int(parts[1])
    return sum(random.randint(1, m) for _ in range(n))


class CombatResult:
    def __init__(self):
        self.player_dmg = 0
        self.enemy_dmg = 0
        self.player_hit = False
        self.enemy_hit = False
        self.player_dodged = False
        self.enemy_dodged = False
        self.fled = False
        self.flee_failed = False
        self.player_dead = False
        self.enemy_dead = False
        self.used_item: Optional[str] = None
        self.heal_amount = 0
        self.xp_gained = 0


def player_attack(player: Player, enemy: Enemy, use_adrenaline: bool = False) -> CombatResult:
    result = CombatResult()
    
    # Base damage from weapon
    has_rifle = player.has_item("pulse_rifle")
    has_blade = player.has_item("blade")
    
    if has_rifle and player.ammo > 0:
        base_dmg = dice("2d8") + player.strength
        player.ammo -= 1
    elif has_blade:
        base_dmg = dice("1d10") + player.strength + player.stealth
    else:
        base_dmg = dice("1d6") + player.strength
    
    if use_adrenaline and player.adrenaline > 0:
        base_dmg = int(base_dmg * 1.5)
        player.adrenaline -= 1
    
    # Hit chance: strength + luck vs enemy dodge
    hit_chance = 0.6 + (player.strength + player.luck) * 0.02
    hit_chance = min(0.95, hit_chance)
    
    if enemy.is_architect:
        hit_chance -= 0.15  # Architects are smarter
    
    # Enemy dodge
    enemy_dodged = random.random() < enemy.dodge_chance
    
    if random.random() < hit_chance and not enemy_dodged:
        result.player_hit = True
        result.player_dmg = max(1, base_dmg)
        enemy.hp -= result.player_dmg
    else:
        result.player_hit = False
        result.enemy_dodged = enemy_dodged
    
    # Enemy counter-attack
    if enemy.hp > 0:
        enemy_dmg = roll(enemy.damage_min, enemy.damage_max)
        player_dead = player.take_damage(enemy_dmg)
        result.enemy_dmg = enemy_dmg
        result.enemy_hit = True
        result.player_dead = player_dead
    
    if enemy.hp <= 0:
        result.enemy_dead = True
        result.xp_gained = enemy.xp_reward
        player.add_xp(result.xp_gained)
    
    return result


def player_dodge(player: Player, enemy: Enemy) -> CombatResult:
    result = CombatResult()
    
    # Dodge check: stealth + adaptability
    dodge_score = (player.stealth + player.adaptability) / 20.0
    dodge_chance = 0.3 + dodge_score
    
    if random.random() < dodge_chance:
        result.player_dodged = True
        # Partial hit still possible from Architects
        if enemy.is_architect and random.random() < 0.3:
            dmg = roll(enemy.damage_min // 2, enemy.damage_max // 2)
            player.take_damage(dmg)
            result.enemy_dmg = dmg
            result.enemy_hit = True
    else:
        result.player_dodged = False
        dmg = roll(enemy.damage_min, enemy.damage_max)
        dead = player.take_damage(dmg)
        result.enemy_dmg = dmg
        result.enemy_hit = True
        result.player_dead = dead
    
    return result


def player_flee(player: Player, enemy: Enemy) -> CombatResult:
    result = CombatResult()
    
    # Flee check: endurance + luck vs enemy flee difficulty
    flee_score = player.endurance + (player.luck // 2)
    
    if flee_score >= enemy.flee_difficulty:
        result.fled = True
        player.add_stress(10)
    else:
        result.fled = False
        result.flee_failed = True
        # Opportunity attack from enemy
        dmg = roll(enemy.damage_min, enemy.damage_max)
        dead = player.take_damage(dmg)
        result.enemy_dmg = dmg
        result.enemy_hit = True
        result.player_dead = dead
    
    return result


def player_use_item(player: Player, enemy: Enemy, item: str) -> CombatResult:
    result = CombatResult()
    result.used_item = item
    
    if item == "medkit" and player.medkits > 0:
        heal = roll(20, 40)
        player.heal(heal)
        player.medkits -= 1
        result.heal_amount = heal
    elif item == "adrenaline" and player.adrenaline > 0:
        player.adrenaline -= 1
        result.heal_amount = 0  # Handled in next turn
    
    # Enemy still attacks
    if enemy.hp > 0:
        dmg = roll(enemy.damage_min, enemy.damage_max)
        dead = player.take_damage(dmg)
        result.enemy_dmg = dmg
        result.enemy_hit = True
        result.player_dead = dead
    
    return result


def get_enemy(enemy_id: str) -> Optional[Enemy]:
    if enemy_id in ENEMIES:
        e = ENEMIES[enemy_id]
        # Return a fresh copy
        return Enemy(
            id=e.id,
            hp=e.hp,
            max_hp=e.max_hp,
            damage_min=e.damage_min,
            damage_max=e.damage_max,
            dodge_chance=e.dodge_chance,
            flee_difficulty=e.flee_difficulty,
            xp_reward=e.xp_reward,
            is_architect=e.is_architect
        )
    return None
