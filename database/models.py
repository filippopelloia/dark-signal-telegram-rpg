from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime
import json


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    language = Column(String(5), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Character
    char_name = Column(String(60), nullable=True)
    callsign = Column(String(40), nullable=True)
    background = Column(String(40), nullable=True)  # marine, scientist, tech, survivor, synthetic
    psych_trait = Column(String(40), nullable=True)  # cold, brave, paranoid, empathic
    starter_item = Column(String(60), nullable=True)
    char_created = Column(Boolean, default=False)

    # Stats
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    stat_points = Column(Integer, default=0)

    strength = Column(Integer, default=3)
    intelligence = Column(Integer, default=3)
    stealth = Column(Integer, default=3)
    engineering = Column(Integer, default=3)
    endurance = Column(Integer, default=3)
    charisma = Column(Integer, default=3)
    luck = Column(Integer, default=3)
    adaptability = Column(Integer, default=3)

    # Vitals
    hp = Column(Integer, default=100)
    max_hp = Column(Integer, default=100)
    stress = Column(Integer, default=0)  # 0-100
    trauma_points = Column(Integer, default=0)
    ammo = Column(Integer, default=30)
    medkits = Column(Integer, default=2)
    battery = Column(Integer, default=100)   # torch battery %
    adrenaline = Column(Integer, default=0)

    # Progression
    current_chapter = Column(Integer, default=0)
    current_scene = Column(String(60), default="main_menu")
    chapter_flags = Column(Text, default="{}")   # JSON flags dict
    npc_relations = Column(Text, default="{}")   # JSON {npc_id: trust_score}
    inventory = Column(Text, default="[]")       # JSON list
    lore_archive = Column(Text, default="[]")    # JSON collected lore
    achievements = Column(Text, default="[]")    # JSON list

    # Daily / streak
    daily_streak = Column(Integer, default=0)
    last_daily = Column(DateTime, nullable=True)
    permadeath_mode = Column(Boolean, default=False)

    # Mental states
    is_paranoid = Column(Boolean, default=False)
    is_ptsd = Column(Boolean, default=False)
    is_dissociated = Column(Boolean, default=False)

    # State machine
    state = Column(String(60), default="idle")   # idle, in_scene, in_combat, char_creation, etc.
    pending_data = Column(Text, default="{}")    # temp data for multi-step flows

    def get_flags(self) -> dict:
        return json.loads(self.chapter_flags or "{}")

    def set_flag(self, key: str, value):
        flags = self.get_flags()
        flags[key] = value
        self.chapter_flags = json.dumps(flags)

    def get_flag(self, key: str, default=None):
        return self.get_flags().get(key, default)

    def get_npc_relations(self) -> dict:
        return json.loads(self.npc_relations or "{}")

    def change_npc_trust(self, npc_id: str, delta: int):
        relations = self.get_npc_relations()
        current = relations.get(npc_id, 50)
        relations[npc_id] = max(0, min(100, current + delta))
        self.npc_relations = json.dumps(relations)

    def get_inventory(self) -> list:
        return json.loads(self.inventory or "[]")

    def add_item(self, item: str):
        inv = self.get_inventory()
        inv.append(item)
        self.inventory = json.dumps(inv)

    def remove_item(self, item: str) -> bool:
        inv = self.get_inventory()
        if item in inv:
            inv.remove(item)
            self.inventory = json.dumps(inv)
            return True
        return False

    def has_item(self, item: str) -> bool:
        return item in self.get_inventory()

    def get_archive(self) -> list:
        return json.loads(self.lore_archive or "[]")

    def add_lore(self, lore_id: str):
        archive = self.get_archive()
        if lore_id not in archive:
            archive.append(lore_id)
            self.lore_archive = json.dumps(archive)

    def get_achievements(self) -> list:
        return json.loads(self.achievements or "[]")

    def add_achievement(self, ach_id: str):
        achs = self.get_achievements()
        if ach_id not in achs:
            achs.append(ach_id)
            self.achievements = json.dumps(achs)
            return True
        return False

    def get_pending(self) -> dict:
        return json.loads(self.pending_data or "{}")

    def set_pending(self, data: dict):
        self.pending_data = json.dumps(data)

    def add_xp(self, amount: int) -> bool:
        """Returns True if leveled up"""
        from config import XP_PER_LEVEL, MAX_LEVEL, STAT_POINTS_PER_LEVEL
        self.xp += amount
        if self.level < MAX_LEVEL and self.xp >= self.level * XP_PER_LEVEL:
            self.xp -= self.level * XP_PER_LEVEL
            self.level += 1
            self.stat_points += STAT_POINTS_PER_LEVEL
            return True
        return False

    def get_stat(self, stat_name: str) -> int:
        return getattr(self, stat_name, 0)

    def upgrade_stat(self, stat_name: str) -> bool:
        valid = ["strength","intelligence","stealth","engineering","endurance","charisma","luck","adaptability"]
        if stat_name in valid and self.stat_points > 0:
            current = getattr(self, stat_name)
            if current < 10:
                setattr(self, stat_name, current + 1)
                self.stat_points -= 1
                return True
        return False

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def take_damage(self, amount: int) -> bool:
        """Returns True if dead"""
        self.hp = max(0, self.hp - amount)
        self.stress = min(100, self.stress + amount // 3)
        return self.hp <= 0

    def add_stress(self, amount: int):
        self.stress = min(100, self.stress + amount)
        if self.stress >= 80 and not self.is_paranoid:
            self.is_paranoid = True

    def reduce_stress(self, amount: int):
        self.stress = max(0, self.stress - amount)
        if self.stress < 40:
            self.is_paranoid = False
