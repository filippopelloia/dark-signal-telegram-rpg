import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from database.db import get_or_create_player, save_player
from database.models import Player
from game.i18n import t, get_lang_options
from game.scene_engine import (get_scene, get_scene_text, get_choice_text, get_locked_reason,
                                check_choice_requirement, apply_scene_effects, apply_choice_effects,
                                process_scene_extras, get_chapter_intro, get_map_ascii)
from config import TYPING_DELAY


async def send_typing(context, chat_id):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(TYPING_DELAY)


# ─── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    if not player.language or player.language not in ["it", "en", "es"]:
        await show_language_selection(update, context)
    else:
        await show_main_menu(update, context, player)


async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🛸 <b>ALIEN: DARK SIGNAL</b>\n\n🌐 Select your language / Seleziona la lingua / Selecciona el idioma:"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang:it")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇪🇸 Español", callback_data="lang:es")],
    ])
    await update.effective_message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def callback_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":")[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    player.language = lang
    player = await save_player(player)
    try:
        await query.message.delete()
    except Exception:
        pass
    await show_main_menu(update, context, player)


# ─── MAIN MENU ────────────────────────────────────────────────────────────────

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player = None):
    if player is None:
        user = update.effective_user
        player = await get_or_create_player(user.id, user.username)
    lang = player.language
    text = f"{t(lang,'welcome_title')}\n{t(lang,'welcome_sub')}\n\n{t(lang,'main_menu')}"
    buttons = []
    if not player.char_created:
        buttons.append([InlineKeyboardButton(t(lang,"btn_new_game"), callback_data="menu:new_game")])
    else:
        buttons.append([InlineKeyboardButton(t(lang,"btn_continue"), callback_data="menu:continue")])
        buttons.append([InlineKeyboardButton(t(lang,"btn_new_game"), callback_data="menu:new_game")])
    buttons.append([
        InlineKeyboardButton(t(lang,"btn_profile"), callback_data="menu:profile"),
        InlineKeyboardButton(t(lang,"btn_inventory"), callback_data="menu:inventory"),
    ])
    buttons.append([
        InlineKeyboardButton(t(lang,"btn_archive"), callback_data="menu:archive"),
        InlineKeyboardButton(t(lang,"btn_achievements"), callback_data="menu:achievements"),
    ])
    buttons.append([
        InlineKeyboardButton(t(lang,"btn_daily"), callback_data="menu:daily"),
        InlineKeyboardButton(t(lang,"btn_settings"), callback_data="menu:settings"),
    ])
    keyboard = InlineKeyboardMarkup(buttons)
    player.state = "idle"
    player.current_scene = "main_menu"
    await save_player(player)
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def callback_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language
    if action == "new_game":
        await start_character_creation(update, context, player)
    elif action == "continue":
        if player.char_created:
            await continue_game(update, context, player)
        else:
            await query.answer(t(lang,"no_save"), show_alert=True)
    elif action == "profile":
        await show_profile(update, context, player)
    elif action == "inventory":
        await show_inventory(update, context, player)
    elif action == "archive":
        await show_archive(update, context, player)
    elif action == "achievements":
        await show_achievements(update, context, player)
    elif action == "daily":
        await show_daily(update, context, player)
    elif action == "settings":
        await show_settings(update, context, player)
    elif action == "main_menu":
        await show_main_menu(update, context, player)


# ─── CHARACTER CREATION ───────────────────────────────────────────────────────

async def start_character_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player):
    lang = player.language
    player.state = "char_creation_name"
    # Reset stats to base
    for stat in ["strength","intelligence","stealth","engineering","endurance","charisma","luck","adaptability"]:
        setattr(player, stat, 3)
    player.char_name = None
    player.callsign = None
    player.background = None
    player.psych_trait = None
    player.starter_item = None
    player.inventory = "[]"
    player.char_created = False
    await save_player(player)
    text = f"{t(lang,'char_creation_title')}\n\n{t(lang,'char_name_prompt')}"
    if update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language
    text_input = update.message.text.strip()

    if player.state == "char_creation_name":
        if not (2 <= len(text_input) <= 30):
            msg = {"en":"⚠️ Name must be 2–30 characters.","it":"⚠️ Nome: 2–30 caratteri.","es":"⚠️ Nombre: 2–30 caracteres."}
            await update.message.reply_text(msg.get(lang, msg["en"]))
            return
        player.char_name = text_input
        player.state = "char_creation_callsign"
        await save_player(player)
        await update.message.reply_text(t(lang,"char_callsign_prompt",name=text_input), parse_mode=ParseMode.HTML)

    elif player.state == "char_creation_callsign":
        if not (2 <= len(text_input) <= 20):
            msg = {"en":"⚠️ Callsign: 2–20 characters.","it":"⚠️ Callsign: 2–20 caratteri.","es":"⚠️ Callsign: 2–20 caracteres."}
            await update.message.reply_text(msg.get(lang, msg["en"]))
            return
        player.callsign = text_input
        player.state = "char_creation_background"
        await save_player(player)
        await _show_background_keyboard(update.message, player)

    else:
        # Ignore unexpected text
        pass


async def _show_background_keyboard(message: Message, player: Player):
    lang = player.language
    text = t(lang,"char_background_prompt")
    bgs = [
        ("marine", t(lang,"bg_marine"), t(lang,"bg_marine_desc")),
        ("scientist", t(lang,"bg_scientist"), t(lang,"bg_scientist_desc")),
        ("tech", t(lang,"bg_tech"), t(lang,"bg_tech_desc")),
        ("survivor", t(lang,"bg_survivor"), t(lang,"bg_survivor_desc")),
        ("synthetic", t(lang,"bg_synthetic"), t(lang,"bg_synthetic_desc")),
    ]
    buttons = [[InlineKeyboardButton(f"{n}\n{d}", callback_data=f"bg:{bid}")] for bid, n, d in bgs]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)


async def callback_background(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    bg = query.data.split(":")[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    player.background = bg
    bg_stats = {
        "marine":    {"strength":2,"endurance":2,"charisma":-1},
        "scientist": {"intelligence":3,"stealth":1},
        "tech":      {"engineering":3,"stealth":1,"endurance":1},
        "survivor":  {"adaptability":2,"luck":2},
        "synthetic": {"intelligence":3,"endurance":2},
    }
    for stat, delta in bg_stats.get(bg, {}).items():
        setattr(player, stat, max(1, min(10, getattr(player, stat, 3) + delta)))
    player.state = "char_creation_psych"
    await save_player(player)
    await _show_psych_keyboard(query.message, player)


async def _show_psych_keyboard(message: Message, player: Player):
    lang = player.language
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang,"psych_cold"), callback_data="psych:cold")],
        [InlineKeyboardButton(t(lang,"psych_brave"), callback_data="psych:brave")],
        [InlineKeyboardButton(t(lang,"psych_paranoid"), callback_data="psych:paranoid")],
        [InlineKeyboardButton(t(lang,"psych_empathic"), callback_data="psych:empathic")],
    ])
    await message.reply_text(t(lang,"psych_prompt"), reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def callback_psych(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    psych = query.data.split(":")[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    player.psych_trait = psych
    psych_bonuses = {
        "cold":     {"intelligence":1},
        "brave":    {"strength":1,"endurance":1},
        "paranoid": {"stealth":2,"charisma":-1},
        "empathic": {"charisma":2},
    }
    for stat, delta in psych_bonuses.get(psych, {}).items():
        setattr(player, stat, max(1, min(10, getattr(player, stat, 3) + delta)))
    player.state = "char_creation_item"
    await save_player(player)
    await _show_item_keyboard(query.message, player)


async def _show_item_keyboard(message: Message, player: Player):
    lang = player.language
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang,"item_pulse_rifle"), callback_data="item:pulse_rifle")],
        [InlineKeyboardButton(t(lang,"item_motion_tracker"), callback_data="item:motion_tracker")],
        [InlineKeyboardButton(t(lang,"item_medkit"), callback_data="item:medkit_starter")],
        [InlineKeyboardButton(t(lang,"item_terminal"), callback_data="item:terminal_access")],
        [InlineKeyboardButton(t(lang,"item_blade"), callback_data="item:blade")],
    ])
    await message.reply_text(t(lang,"starter_item_prompt"), reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def callback_starter_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item = query.data.split(":")[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language
    player.starter_item = item
    player.add_item(item)
    # Everyone gets a basic pulse rifle
    if "pulse_rifle" not in player.get_inventory():
        player.add_item("pulse_rifle")
    player.state = "char_creation_confirm"
    await save_player(player)

    item_names = {
        "en":{"pulse_rifle":"Modified M41A Pulse Rifle","motion_tracker":"Advanced Motion Tracker",
              "medkit_starter":"Weyland Premium Med-Kit","terminal_access":"Corporate Terminal Access (Lvl 3)","blade":"Monomolecular Silent Blade"},
        "it":{"pulse_rifle":"Pulse Rifle M41A Modificato","motion_tracker":"Motion Tracker Avanzato",
              "medkit_starter":"Kit Medico Weyland Premium","terminal_access":"Accesso Terminale (Lvl 3)","blade":"Lama Monomolecolare Silenziosa"},
        "es":{"pulse_rifle":"Pulse Rifle M41A Modificado","motion_tracker":"Motion Tracker Avanzado",
              "medkit_starter":"Kit Médico Weyland Premium","terminal_access":"Acceso Terminal (Niv 3)","blade":"Hoja Monomolecular Silenciosa"},
    }
    bg_labels = {
        "en":{"marine":"Colonial Marine","scientist":"W-Y Scientist","tech":"Ship Tech","survivor":"Civilian Survivor","synthetic":"Synthetic"},
        "it":{"marine":"Colonial Marine","scientist":"Scienziato W-Y","tech":"Tecnico di Bordo","survivor":"Sopravvissuto Civile","synthetic":"Sintetico"},
        "es":{"marine":"Marine Colonial","scientist":"Científico W-Y","tech":"Técnico de Nave","survivor":"Superviviente Civil","synthetic":"Sintético"},
    }
    psych_labels = {
        "en":{"cold":"Cold & Rational","brave":"Instinctive & Brave","paranoid":"Paranoid","empathic":"Empathic"},
        "it":{"cold":"Freddo e Razionale","brave":"Istintivo e Coraggioso","paranoid":"Paranoico","empathic":"Empatico"},
        "es":{"cold":"Frío y Racional","brave":"Instintivo y Valiente","paranoid":"Paranoico","empathic":"Empático"},
    }
    text = t(lang,"char_confirm",
             name=player.char_name, callsign=player.callsign,
             background=bg_labels.get(lang, bg_labels["en"]).get(player.background, "?"),
             psych=psych_labels.get(lang, psych_labels["en"]).get(player.psych_trait, "?"),
             item=item_names.get(lang, item_names["en"]).get(item, item))
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang,"btn_confirm"), callback_data="char:confirm")],
        [InlineKeyboardButton(t(lang,"btn_restart_creation"), callback_data="char:restart")],
    ])
    await query.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def callback_char(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language

    if action == "restart":
        await start_character_creation(update, context, player)
        return

    # Confirm → permadeath choice
    player.state = "char_creation_permadeath"
    await save_player(player)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang,"btn_nostromo"), callback_data="permadeath:yes")],
        [InlineKeyboardButton(t(lang,"btn_standard"), callback_data="permadeath:no")],
    ])
    await query.message.reply_text(t(lang,"permadeath_prompt"), reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def callback_permadeath(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":")[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language

    player.permadeath_mode = (choice == "yes")
    player.char_created = True
    player.current_chapter = 1
    player.current_scene = "c1_shuttle"
    player.state = "in_scene"
    import json
    player.npc_relations = json.dumps({"ajax":50,"chen":50,"okafor":50,"vance":50,"petra":50})
    player.medkits = 2
    player.ammo = 30
    player.battery = 100
    player.hp = player.max_hp = 100
    player.stress = 0
    await save_player(player)

    intro = get_chapter_intro(1, lang)
    await query.message.reply_text(intro, parse_mode=ParseMode.HTML)
    await asyncio.sleep(2.0)
    await show_scene(query.message, context, player, "c1_shuttle")


# ─── SCENE ENGINE ─────────────────────────────────────────────────────────────

async def show_scene(message: Message, context: ContextTypes.DEFAULT_TYPE, player: Player, scene_id: str):
    lang = player.language
    scene = get_scene(scene_id, player.current_chapter)
    if not scene:
        await message.reply_text(f"❌ Scene not found: {scene_id}")
        return

    events = apply_scene_effects(scene, player)
    extras = process_scene_extras(scene, player)
    events.extend(extras)
    player.current_scene = scene_id
    player.state = "in_scene"
    player = await save_player(player)

    text = get_scene_text(scene, lang)

    if scene.get("combat_trigger"):
        await message.reply_text(text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(1.5)
        await show_combat(message, context, player, scene["combat_trigger"], scene.get("post_combat_scene","main_menu"))
        return

    # Build choices
    choices = scene.get("choices", [])
    buttons = []
    for choice in choices:
        can_use, _ = check_choice_requirement(choice, player)
        choice_text = get_choice_text(choice, lang)
        if can_use:
            buttons.append([InlineKeyboardButton(choice_text, callback_data=f"choice:{choice['id']}")])
        else:
            reason = get_locked_reason(choice, lang)
            locked_label = t(lang,"locked_choice",reason=reason) if reason else f"🔒 {choice_text}"
            buttons.append([InlineKeyboardButton(locked_label, callback_data="locked")])

    keyboard = InlineKeyboardMarkup(buttons) if buttons else None

    # Send events
    for event in events:
        if event.startswith("level_up:"):
            parts = event.split(":")
            await message.reply_text(t(lang,"level_up",level=parts[1],points=parts[2]), parse_mode=ParseMode.HTML)
        elif event.startswith("lore:"):
            lore_id = event.split(":",1)[1]
            from game.scene_engine import get_lore_entry
            entry = get_lore_entry(lore_id)
            if entry:
                title = entry.get("title",{}).get(lang, entry.get("title",{}).get("en",""))
                msg = {"en":f"📂 <b>LORE UNLOCKED:</b> {title}","it":f"📂 <b>LORE SBLOCCATO:</b> {title}","es":f"📂 <b>LORE DESBLOQUEADO:</b> {title}"}
                await message.reply_text(msg.get(lang,msg["en"]), parse_mode=ParseMode.HTML)
        elif event.startswith("achievement:"):
            ach_id = event.split(":",1)[1]
            ach_name = t(lang,f"achievement_names.{ach_id}")
            msg = {"en":f"🏆 <b>ACHIEVEMENT:</b> {ach_name}","it":f"🏆 <b>OBIETTIVO:</b> {ach_name}","es":f"🏆 <b>LOGRO:</b> {ach_name}"}
            await message.reply_text(msg.get(lang,msg["en"]), parse_mode=ParseMode.HTML)

    await context.bot.send_chat_action(message.chat_id, ChatAction.TYPING)
    await asyncio.sleep(TYPING_DELAY)
    await message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def callback_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "locked":
        await query.answer("🔒", show_alert=False)
        return
    await query.answer()
    choice_id = query.data.split(":",1)[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language

    scene = get_scene(player.current_scene, player.current_chapter)
    if not scene:
        return

    choice = next((c for c in scene.get("choices",[]) if c["id"] == choice_id), None)
    if not choice:
        return

    events = apply_choice_effects(choice, player)
    player = await save_player(player)

    for event in events:
        if event.startswith("lore:"):
            lore_id = event.split(":",1)[1]
            from game.scene_engine import get_lore_entry
            entry = get_lore_entry(lore_id)
            if entry:
                title = entry.get("title",{}).get(lang, entry.get("title",{}).get("en",""))
                msg = {"en":f"📂 <b>LORE UNLOCKED:</b> {title}","it":f"📂 <b>LORE SBLOCCATO:</b> {title}","es":f"📂 <b>LORE DESBLOQUEADO:</b> {title}"}
                await query.message.reply_text(msg.get(lang,msg["en"]), parse_mode=ParseMode.HTML)

    next_scene = choice.get("next","main_menu")
    if next_scene == "main_menu":
        await show_main_menu(update, context, player)
    else:
        await show_scene(query.message, context, player, next_scene)


# ─── COMBAT ───────────────────────────────────────────────────────────────────

async def show_combat(message: Message, context: ContextTypes.DEFAULT_TYPE, player: Player, enemy_id: str, post_scene: str):
    from game.combat import get_enemy
    lang = player.language
    enemy = get_enemy(enemy_id)
    if not enemy:
        await show_scene(message, context, player, post_scene)
        return
    pending = {"enemy_id":enemy_id,"enemy_hp":enemy.hp,"post_scene":post_scene}
    player.set_pending(pending)
    player.state = "in_combat"
    player = await save_player(player)
    enemy_name = t(lang,f"xeno_types.{enemy_id}")
    text = (f"{t(lang,'combat_title')}\n\n"
            f"{t(lang,'combat_vs',enemy=enemy_name)}\n"
            f"{t(lang,'combat_hp',hp=player.hp,enemy_hp=enemy.hp)}")
    buttons = _combat_buttons(player, lang)
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)


def _combat_buttons(player: Player, lang: str) -> list:
    buttons = [
        [InlineKeyboardButton(t(lang,"btn_attack"), callback_data="combat:attack")],
        [InlineKeyboardButton(t(lang,"btn_dodge"), callback_data="combat:dodge")],
    ]
    if player.medkits > 0:
        buttons.append([InlineKeyboardButton(f"{t(lang,'btn_use_item')} 💊 ({player.medkits})", callback_data="combat:medkit")])
    if player.adrenaline > 0:
        buttons.append([InlineKeyboardButton(t(lang,"btn_use_adrenaline"), callback_data="combat:adrenaline")])
    buttons.append([InlineKeyboardButton(t(lang,"btn_flee"), callback_data="combat:flee")])
    return buttons


async def callback_combat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language
    if player.state != "in_combat":
        return

    from game.combat import get_enemy, player_attack, player_dodge, player_flee, player_use_item
    pending = player.get_pending()
    enemy_id = pending.get("enemy_id","drone")
    enemy_hp = pending.get("enemy_hp",30)
    post_scene = pending.get("post_scene","main_menu")
    enemy = get_enemy(enemy_id)
    enemy.hp = enemy_hp

    fled = False
    result_lines = []

    if action == "attack":
        r = player_attack(player, enemy)
        result_lines.append(t(lang,"attack_hit",dmg=r.player_dmg,hp=max(0,enemy.hp)) if r.player_hit else t(lang,"attack_miss"))
        if r.enemy_hit:
            result_lines.append(t(lang,"enemy_attack",dmg=r.enemy_dmg))
    elif action == "dodge":
        r = player_dodge(player, enemy)
        result_lines.append(t(lang,"dodge_success") if r.player_dodged else t(lang,"dodge_fail",dmg=r.enemy_dmg))
    elif action == "medkit":
        r = player_use_item(player, enemy, "medkit")
        result_lines.append(f"💊 +{r.heal_amount} HP")
        if r.enemy_hit:
            result_lines.append(t(lang,"enemy_attack",dmg=r.enemy_dmg))
    elif action == "adrenaline":
        r = player_attack(player, enemy, use_adrenaline=True)
        result_lines.append("💉 Adrenaline!")
        result_lines.append(t(lang,"attack_hit",dmg=r.player_dmg,hp=max(0,enemy.hp)) if r.player_hit else t(lang,"attack_miss"))
        if r.enemy_hit:
            result_lines.append(t(lang,"enemy_attack",dmg=r.enemy_dmg))
    elif action == "flee":
        r = player_flee(player, enemy)
        if r.fled:
            result_lines.append(t(lang,"flee_success"))
            fled = True
        else:
            result_lines.append(t(lang,"flee_fail"))
            if r.enemy_hit:
                result_lines.append(t(lang,"enemy_attack",dmg=r.enemy_dmg))

    await query.message.reply_text("\n".join(result_lines), parse_mode=ParseMode.HTML)
    await asyncio.sleep(0.8)

    if fled:
        player.state = "in_scene"
        player.set_pending({})
        player.add_achievement("no_one_hears")
        player = await save_player(player)
        await show_scene(query.message, context, player, post_scene)
        return

    if player.hp <= 0:
        player.state = "idle"
        player.set_pending({})
        player = await save_player(player)
        if player.permadeath_mode:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(lang,"btn_restart"), callback_data="death:restart")]])
            await query.message.reply_text(t(lang,"game_over_permadeath"), reply_markup=kb, parse_mode=ParseMode.HTML)
        else:
            player.hp = player.max_hp // 2
            player.stress = min(100, player.stress + 20)
            player = await save_player(player)
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(lang,"btn_continue"), callback_data=f"death:continue:{post_scene}")]])
            await query.message.reply_text(t(lang,"combat_dead"), reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    if enemy.hp <= 0:
        from game.combat import ENEMIES
        xp = ENEMIES.get(enemy_id, type("", (), {"xp_reward":30})()).xp_reward
        player.add_achievement("first_blood")
        if len(player.get_archive()) >= 10:
            player.add_achievement("lore_hunter")
        player.state = "in_scene"
        player.set_pending({})
        player = await save_player(player)
        await query.message.reply_text(t(lang,"combat_win",xp=xp), parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.8)
        await show_scene(query.message, context, player, post_scene)
        return

    pending["enemy_hp"] = enemy.hp
    player.set_pending(pending)
    player = await save_player(player)
    enemy_name = t(lang,f"xeno_types.{enemy_id}")
    status = f"{t(lang,'combat_vs',enemy=enemy_name)}\n{t(lang,'combat_hp',hp=player.hp,enemy_hp=enemy.hp)}"
    await query.message.reply_text(status, reply_markup=InlineKeyboardMarkup(_combat_buttons(player,lang)), parse_mode=ParseMode.HTML)


async def callback_death(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    action = parts[1]
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language
    if action == "restart":
        for stat in ["strength","intelligence","stealth","engineering","endurance","charisma","luck","adaptability"]:
            setattr(player, stat, 3)
        player.hp = player.max_hp = 100
        player.stress = 0
        player.current_chapter = 1
        player.current_scene = "c1_shuttle"
        player.chapter_flags = "{}"
        player.state = "in_scene"
        import json
        player.npc_relations = json.dumps({"ajax":50,"chen":50,"okafor":50,"vance":50,"petra":50})
        player = await save_player(player)
        intro = get_chapter_intro(1, lang)
        await query.message.reply_text(intro, parse_mode=ParseMode.HTML)
        await asyncio.sleep(2.0)
        await show_scene(query.message, context, player, "c1_shuttle")
    elif action == "continue":
        scene_id = parts[2] if len(parts) > 2 else player.current_scene
        player.state = "in_scene"
        player = await save_player(player)
        await show_scene(query.message, context, player, scene_id)


# ─── PROFILE / STATS ─────────────────────────────────────────────────────────

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player = None):
    if player is None:
        user = update.effective_user
        player = await get_or_create_player(user.id, user.username)
    lang = player.language
    from config import XP_PER_LEVEL
    if not player.char_created:
        msg = {"en":"No character yet! Start a new game.","it":"Nessun personaggio! Inizia una nuova partita.","es":"¡Sin personaje! Inicia una nueva partida."}
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️", callback_data="menu:main_menu")]])
        if update.callback_query:
            await update.callback_query.message.edit_text(msg.get(lang,msg["en"]), reply_markup=kb)
        else:
            await update.effective_message.reply_text(msg.get(lang,msg["en"]), reply_markup=kb)
        return
    bg_labels = {
        "en":{"marine":"Colonial Marine","scientist":"W-Y Scientist","tech":"Ship Tech","survivor":"Civilian Survivor","synthetic":"Synthetic"},
        "it":{"marine":"Colonial Marine","scientist":"Scienziato W-Y","tech":"Tecnico","survivor":"Sopravvissuto","synthetic":"Sintetico"},
        "es":{"marine":"Marine Colonial","scientist":"Científico W-Y","tech":"Técnico","survivor":"Superviviente","synthetic":"Sintético"},
    }
    chapter_names = {
        "en":{0:"Not started",1:"Ch.1 — Silence of Theta",2:"Ch.2 — The Architects",3:"Ch.3 — Black Code",4:"Ch.4 — Queen",5:"Ch.5 — Dark Signal"},
        "it":{0:"Non iniziato",1:"Cap.1 — Silenzio di Theta",2:"Cap.2 — Gli Architetti",3:"Cap.3 — Codice Nero",4:"Cap.4 — La Regina",5:"Cap.5 — Segnale Oscuro"},
        "es":{0:"No iniciado",1:"Cap.1 — Silencio de Theta",2:"Cap.2 — Los Arquitectos",3:"Cap.3 — Código Negro",4:"Cap.4 — La Reina",5:"Cap.5 — Señal Oscura"},
    }
    text = (
        f"{t(lang,'profile_title',name=player.char_name or '?',callsign=player.callsign or '?')}\n"
        f"{t(lang,'profile_bg',bg=bg_labels.get(lang,bg_labels['en']).get(player.background or '','?'))}\n\n"
        f"{t(lang,'profile_level',level=player.level,xp=player.xp,max_xp=player.level*XP_PER_LEVEL)}\n\n"
        f"{t(lang,'profile_vitals',hp=player.hp,max_hp=player.max_hp,stress=player.stress,battery=player.battery,medkits=player.medkits,ammo=player.ammo)}\n\n"
        f"{t(lang,'profile_stats',strength=player.strength,intelligence=player.intelligence,stealth=player.stealth,engineering=player.engineering,endurance=player.endurance,charisma=player.charisma,luck=player.luck,adaptability=player.adaptability)}\n\n"
        f"{t(lang,'profile_chapter',chapter=chapter_names.get(lang,chapter_names['en']).get(player.current_chapter,str(player.current_chapter)))}\n"
        f"{t(lang,'profile_streak',streak=player.daily_streak)}"
    )
    if player.stat_points > 0:
        text += f"\n\n{t(lang,'profile_stat_points',points=player.stat_points)}"
    buttons = []
    if player.stat_points > 0:
        buttons.append([InlineKeyboardButton(t(lang,"btn_upgrade_stat"), callback_data="stat:upgrade")])
    buttons.append([InlineKeyboardButton("◀️ Menu", callback_data="menu:main_menu")])
    keyboard = InlineKeyboardMarkup(buttons)
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def callback_stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    player = await get_or_create_player(user.id, user.username)
    lang = player.language
    data = query.data

    if data == "stat:upgrade":
        stat_names = {
            "en":{"strength":"💪 Strength","intelligence":"🧠 Intelligence","stealth":"👣 Stealth","engineering":"🔧 Engineering","endurance":"🛡️ Endurance","charisma":"🗣️ Charisma","luck":"🍀 Luck","adaptability":"🔄 Adaptability"},
            "it":{"strength":"💪 Forza","intelligence":"🧠 Intelligenza","stealth":"👣 Furtività","engineering":"🔧 Ingegneria","endurance":"🛡️ Resistenza","charisma":"🗣️ Carisma","luck":"🍀 Fortuna","adaptability":"🔄 Adattabilità"},
            "es":{"strength":"💪 Fuerza","intelligence":"🧠 Inteligencia","stealth":"👣 Sigilo","engineering":"🔧 Ingeniería","endurance":"🛡️ Resistencia","charisma":"🗣️ Carisma","luck":"🍀 Suerte","adaptability":"🔄 Adaptabilidad"},
        }
        names = stat_names.get(lang, stat_names["en"])
        all_stats = ["strength","intelligence","stealth","engineering","endurance","charisma","luck","adaptability"]
        text = t(lang,"upgrade_stat_prompt",points=player.stat_points)
        buttons = []
        for stat in all_stats:
            val = getattr(player, stat)
            if val < 10:
                buttons.append([InlineKeyboardButton(f"{names[stat]}: {val} → {val+1}", callback_data=f"stat:set:{stat}")])
        buttons.append([InlineKeyboardButton("◀️", callback_data="menu:profile")])
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

    elif data.startswith("stat:set:"):
        stat_name = data.split(":")[2]
        success = player.upgrade_stat(stat_name)
        if success:
            val = getattr(player, stat_name)
            await save_player(player)
            await query.answer(t(lang,"stat_upgraded",stat=stat_name.capitalize(),value=val), show_alert=True)
            await show_profile(update, context, player)
        else:
            await query.answer(t(lang,"no_stat_points"), show_alert=True)


# ─── INVENTORY / ARCHIVE / ACHIEVEMENTS ──────────────────────────────────────

async def show_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player = None):
    if player is None:
        user = update.effective_user
        player = await get_or_create_player(user.id, user.username)
    lang = player.language
    inv = player.get_inventory()
    item_display = {
        "en":{"pulse_rifle":"🔫 M41A Pulse Rifle","motion_tracker":"📡 Advanced Motion Tracker","medkit":"💊 Med-Kit","medkit_starter":"💊 Weyland Med-Kit","terminal_access":"💻 Corporate Terminal Access","blade":"🗡️ Monomolecular Blade","datapad_b4":"📱 Datapad B-4","petra_data_chip":"💾 Petra's Data Chip"},
        "it":{"pulse_rifle":"🔫 Pulse Rifle M41A","motion_tracker":"📡 Motion Tracker Avanzato","medkit":"💊 Medikit","medkit_starter":"💊 Kit Medico Weyland","terminal_access":"💻 Accesso Terminale","blade":"🗡️ Lama Monomolecolare","datapad_b4":"📱 Datapad B-4","petra_data_chip":"💾 Chip Dati di Petra"},
        "es":{"pulse_rifle":"🔫 Pulse Rifle M41A","motion_tracker":"📡 Motion Tracker Avanzado","medkit":"💊 Botiquín","medkit_starter":"💊 Kit Médico Weyland","terminal_access":"💻 Acceso Terminal","blade":"🗡️ Hoja Monomolecular","datapad_b4":"📱 Datapad B-4","petra_data_chip":"💾 Chip de Petra"},
    }
    display = item_display.get(lang, item_display["en"])
    text = t(lang,"inventory_title")
    text += "\n\n" + ("\n".join(f"• {display.get(i,i)}" for i in inv) if inv else t(lang,"inventory_empty"))
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Menu", callback_data="menu:main_menu")]])
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def show_archive(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player = None):
    if player is None:
        user = update.effective_user
        player = await get_or_create_player(user.id, user.username)
    lang = player.language
    archive = player.get_archive()
    text = t(lang,"archive_title",count=len(archive))
    if not archive:
        text += f"\n\n{t(lang,'archive_empty')}"
    else:
        from game.scene_engine import get_lore_entry
        lines = []
        for lore_id in archive:
            entry = get_lore_entry(lore_id)
            if entry:
                title = entry.get("title",{}).get(lang, entry.get("title",{}).get("en",lore_id))
                lore_text = entry.get("text",{}).get(lang, entry.get("text",{}).get("en",""))
                lines.append(f"\n📄 <b>{title}</b>\n<i>{lore_text[:200]}...</i>")
        text += "\n" + "\n".join(lines)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Menu", callback_data="menu:main_menu")]])
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player = None):
    if player is None:
        user = update.effective_user
        player = await get_or_create_player(user.id, user.username)
    lang = player.language
    earned = player.get_achievements()
    from game.npcs import ACHIEVEMENTS_DATA
    text = t(lang,"achievements_title")
    if not earned:
        text += f"\n\n{t(lang,'no_achievements')}"
    else:
        lines = [f"\n✅ <b>{t(lang,f'achievement_names.{a}')}</b>\n<i>{ACHIEVEMENTS_DATA.get(a,{}).get('description',{}).get(lang,ACHIEVEMENTS_DATA.get(a,{}).get('description',{}).get('en',''))}</i>" for a in earned]
        text += "\n" + "\n".join(lines)
    locked = [a for a in ACHIEVEMENTS_DATA if a not in earned]
    if locked:
        text += "\n\n" + "\n".join(f"🔒 {t(lang,f'achievement_names.{a}')}" for a in locked)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Menu", callback_data="menu:main_menu")]])
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ─── DAILY MISSION ────────────────────────────────────────────────────────────

async def show_daily(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player = None):
    if player is None:
        user = update.effective_user
        player = await get_or_create_player(user.id, user.username)
    lang = player.language
    from datetime import datetime, timedelta
    from game.npcs import DAILY_MISSIONS
    import random
    now = datetime.utcnow()
    if player.last_daily and (now - player.last_daily).total_seconds() < 86400:
        remaining = timedelta(seconds=86400) - (now - player.last_daily)
        hours = int(remaining.total_seconds() // 3600)
        mins = int((remaining.total_seconds() % 3600) // 60)
        text = t(lang,"daily_done",hours=hours,mins=mins)
    else:
        mission = random.choice(DAILY_MISSIONS)
        mission_text = mission["text"].get(lang, mission["text"]["en"])
        effects = mission.get("effects",{})
        leveled = False
        if "xp" in effects: leveled = player.add_xp(effects["xp"])
        if "stress" in effects: player.add_stress(effects["stress"])
        if "battery" in effects: player.battery = min(100, player.battery + effects["battery"])
        if "ammo" in effects: player.ammo += effects["ammo"]
        if "medkits" in effects: player.medkits += effects["medkits"]
        player.last_daily = now
        player.daily_streak += 1
        player = await save_player(player)
        text = f"{t(lang,'daily_available')}\n\n{mission_text}"
        if leveled:
            text += f"\n\n{t(lang,'level_up',level=player.level,points=player.stat_points)}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Menu", callback_data="menu:main_menu")]])
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ─── SETTINGS ─────────────────────────────────────────────────────────────────

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player = None):
    if player is None:
        user = update.effective_user
        player = await get_or_create_player(user.id, user.username)
    lang = player.language
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang,"btn_change_language"), callback_data="settings:language")],
        [InlineKeyboardButton("◀️ Menu", callback_data="menu:main_menu")],
    ])
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(t(lang,"settings_title"), reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.reply_text(t(lang,"settings_title"), reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(t(lang,"settings_title"), reply_markup=kb, parse_mode=ParseMode.HTML)


async def callback_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    if action == "language":
        text = "🌐 Select / Seleziona / Selecciona:"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang:it")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
            [InlineKeyboardButton("🇪🇸 Español", callback_data="lang:es")],
        ])
        await query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ─── COMMANDS ─────────────────────────────────────────────────────────────────

async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = await get_or_create_player(update.effective_user.id, update.effective_user.username)
    await show_profile(update, context, player)

async def cmd_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = await get_or_create_player(update.effective_user.id, update.effective_user.username)
    await show_inventory(update, context, player)

async def cmd_archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = await get_or_create_player(update.effective_user.id, update.effective_user.username)
    await show_archive(update, context, player)

async def cmd_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = await get_or_create_player(update.effective_user.id, update.effective_user.username)
    await update.message.reply_text(f"<pre>{get_map_ascii(player)}</pre>", parse_mode=ParseMode.HTML)

async def cmd_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = await get_or_create_player(update.effective_user.id, update.effective_user.username)
    await save_player(player)
    await update.message.reply_text(t(player.language,"game_saved"))

async def cmd_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = await get_or_create_player(update.effective_user.id, update.effective_user.username)
    await show_achievements(update, context, player)

async def continue_game(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player):
    scene_id = player.current_scene
    if not scene_id or scene_id == "main_menu":
        scene_id = "c1_shuttle"
        player.current_scene = scene_id
        await save_player(player)
    if update.callback_query:
        await show_scene(update.callback_query.message, context, player, scene_id)
    else:
        await show_scene(update.effective_message, context, player, scene_id)
