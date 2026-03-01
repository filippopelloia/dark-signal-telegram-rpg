from database.models import Player


NPC_DATA = {
    "ajax": {
        "name_key": "npc_ajax",
        "emoji": "🤖",
        "description": {
            "en": "Android. Corporate assignment. His eyes see everything. His loyalties: uncertain.",
            "it": "Androide. Assegnazione aziendale. I suoi occhi vedono tutto. Le sue lealtà: incerte.",
            "es": "Androide. Asignación corporativa. Sus ojos lo ven todo. Sus lealtades: inciertas."
        },
        "trust_thresholds": {
            "hostile": 0,
            "suspicious": 20,
            "neutral": 40,
            "friendly": 60,
            "loyal": 80
        }
    },
    "chen": {
        "name_key": "npc_chen",
        "emoji": "🪖",
        "description": {
            "en": "Colonial Marine. Practical. Has seen enough to know fear is earned.",
            "it": "Colonial Marine. Pratica. Ha visto abbastanza per sapere che la paura si guadagna.",
            "es": "Marine Colonial. Práctica. Ha visto suficiente para saber que el miedo se gana."
        },
        "trust_thresholds": {
            "hostile": 0,
            "suspicious": 20,
            "neutral": 40,
            "friendly": 60,
            "loyal": 80
        }
    },
    "okafor": {
        "name_key": "npc_okafor",
        "emoji": "🔬",
        "description": {
            "en": "Xenobiologist. Brilliant and complicit. Whereabouts: unknown.",
            "it": "Xenobiologo. Brillante e complice. Dove si trova: sconosciuto.",
            "es": "Xenobiólogo. Brillante y cómplice. Paradero: desconocido."
        },
        "trust_thresholds": {}
    },
    "vance": {
        "name_key": "npc_vance",
        "emoji": "🎖️",
        "description": {
            "en": "Lieutenant. Mission-focused. Doesn't ask questions he doesn't want answered.",
            "it": "Tenente. Focalizzato sulla missione. Non fa domande a cui non vuole risposte.",
            "es": "Teniente. Centrado en la misión. No hace preguntas que no quiere responder."
        },
        "trust_thresholds": {}
    },
    "petra": {
        "name_key": "npc_petra",
        "emoji": "🧬",
        "description": {
            "en": "Survivor. Knows what really happened on Theta. Scared. Angry. Right.",
            "it": "Sopravvissuta. Sa cosa è successo davvero su Theta. Spaventata. Arrabbiata. Ha ragione.",
            "es": "Superviviente. Sabe lo que realmente ocurrió en Theta. Asustada. Enojada. Tiene razón."
        },
        "trust_thresholds": {}
    }
}


def get_npc_trust_label(trust_score: int, lang: str) -> str:
    labels = {
        "en": {0: "Hostile", 20: "Suspicious", 40: "Neutral", 60: "Friendly", 80: "Loyal"},
        "it": {0: "Ostile", 20: "Sospettoso", 40: "Neutrale", 60: "Amichevole", 80: "Leale"},
        "es": {0: "Hostil", 20: "Sospechoso", 40: "Neutral", 60: "Amigable", 80: "Leal"}
    }
    lang_labels = labels.get(lang, labels["en"])
    
    for threshold in sorted(lang_labels.keys(), reverse=True):
        if trust_score >= threshold:
            return lang_labels[threshold]
    return lang_labels[0]


def format_npc_relations(player: Player, lang: str) -> str:
    relations = player.get_npc_relations()
    lines = []
    
    for npc_id, npc_info in NPC_DATA.items():
        trust = relations.get(npc_id, 50)
        label = get_npc_trust_label(trust, lang)
        emoji = npc_info["emoji"]
        
        # Get name (simplified without i18n lookup)
        name_key = npc_info["name_key"]
        name = name_key.replace("npc_", "").upper()
        
        lines.append(f"{emoji} {name}: {trust}/100 — {label}")
    
    return "\n".join(lines)


ACHIEVEMENTS_DATA = {
    "first_blood": {
        "name_key": "achievement_names.first_blood",
        "description": {
            "en": "Defeat your first Xenomorph in combat.",
            "it": "Sconfiggi il tuo primo Xenomorfo in combattimento.",
            "es": "Derrota a tu primer Xenomorfo en combate."
        }
    },
    "theta_survivor": {
        "name_key": "achievement_names.theta_survivor",
        "description": {
            "en": "Complete Chapter 1.",
            "it": "Completa il Capitolo 1.",
            "es": "Completa el Capítulo 1."
        }
    },
    "no_one_hears": {
        "name_key": "achievement_names.no_one_hears",
        "description": {
            "en": "Escape a combat encounter without firing a single shot.",
            "it": "Sfuggi a un incontro di combattimento senza sparare un solo colpo.",
            "es": "Escapa de un encuentro de combate sin disparar un solo tiro."
        }
    },
    "machine_trust": {
        "name_key": "achievement_names.machine_trust",
        "description": {
            "en": "Reach 80 trust with AJAX-7.",
            "it": "Raggiungi 80 di fiducia con AJAX-7.",
            "es": "Alcanza 80 de confianza con AJAX-7."
        }
    },
    "lore_hunter": {
        "name_key": "achievement_names.lore_hunter",
        "description": {
            "en": "Collect 10 lore entries.",
            "it": "Raccogli 10 voci di lore.",
            "es": "Recoge 10 entradas de lore."
        }
    },
    "perfect_run": {
        "name_key": "achievement_names.perfect_run",
        "description": {
            "en": "Complete a chapter with all NPCs alive.",
            "it": "Completa un capitolo con tutti gli NPC vivi.",
            "es": "Completa un capítulo con todos los NPC vivos."
        }
    },
    "nostromo_clear": {
        "name_key": "achievement_names.nostromo_clear",
        "description": {
            "en": "Complete the game in Nostromo Mode.",
            "it": "Completa il gioco in Modalità Nostromo.",
            "es": "Completa el juego en Modo Nostromo."
        }
    }
}


DAILY_MISSIONS = [
    {
        "id": "daily_scan",
        "text": {
            "en": "📡 <b>DAILY SIGNAL</b>\n\nA partial data packet arrives from Theta's outer sensors. You isolate and decode it — fragmented corporate communications, movement logs, a half-corrupted research entry.\n\nNot much. But enough to keep you oriented.\n\n<i>+25 XP, torch battery restored +10%</i>",
            "it": "📡 <b>SEGNALE GIORNALIERO</b>\n\nUn pacchetto di dati parziale arriva dai sensori esterni di Theta. Lo isoli e lo decodifichi — comunicazioni aziendali frammentate, log di movimento, una voce di ricerca semi-corrotta.\n\nNon molto. Ma abbastanza per tenerti orientato.\n\n<i>+25 XP, batteria torcia ripristinata +10%</i>",
            "es": "📡 <b>SEÑAL DIARIA</b>\n\nUn paquete de datos parcial llega de los sensores exteriores de Theta. Lo aislas y decodificas — comunicaciones corporativas fragmentadas, registros de movimiento, una entrada de investigación medio corrupta.\n\nNo mucho. Pero suficiente para mantenerte orientado.\n\n<i>+25 XP, batería de linterna restaurada +10%</i>"
        },
        "effects": {"xp": 25, "battery": 10}
    },
    {
        "id": "daily_maintenance",
        "text": {
            "en": "🔧 <b>EQUIPMENT MAINTENANCE</b>\n\nYou spend twenty minutes checking your kit. The pulse rifle's thermal coupling was slightly misaligned — you correct it. The motion tracker's sensitivity dial gets a recalibration.\n\nSmall things. The kind of small things that save lives.\n\n<i>+20 XP, +5 ammo, +1 medkit</i>",
            "it": "🔧 <b>MANUTENZIONE EQUIPAGGIAMENTO</b>\n\nPassi venti minuti a controllare il tuo kit. Il raccordo termico del pulse rifle era leggermente disallineato — lo correggi. Il quadrante di sensibilità del motion tracker ottiene una ricalibrazione.\n\nCose piccole. Il tipo di cose piccole che salvano vite.\n\n<i>+20 XP, +5 munizioni, +1 medikit</i>",
            "es": "🔧 <b>MANTENIMIENTO DE EQUIPO</b>\n\nPasas veinte minutos revisando tu equipo. El acoplamiento térmico del pulse rifle estaba ligeramente desalineado — lo corriges. El dial de sensibilidad del detector de movimiento recibe una recalibración.\n\nCosas pequeñas. El tipo de cosas pequeñas que salvan vidas.\n\n<i>+20 XP, +5 munición, +1 botiquín</i>"
        },
        "effects": {"xp": 20, "ammo": 5, "medkits": 1}
    },
    {
        "id": "daily_intel",
        "text": {
            "en": "📋 <b>CORPORATE INTERCEPT</b>\n\nA Weyland-Yutani encrypted channel opens briefly — someone on the outside is trying to reach Theta. You catch fragments before the signal dies.\n\n<i>«...Omega Harvest timeline accelerated... do not engage... specimen recovery priority...»</i>\n\nThey're not coming to rescue you.\n\n<i>+30 XP, +5 Stress</i>",
            "it": "📋 <b>INTERCETTAZIONE AZIENDALE</b>\n\nUn canale criptato Weyland-Yutani si apre brevemente — qualcuno dall'esterno sta cercando di raggiungere Theta. Cogli frammenti prima che il segnale muoia.\n\n<i>«...tempistica Omega Harvest accelerata... non ingaggiare... priorità recupero campione...»</i>\n\nNon vengono a salvarti.\n\n<i>+30 XP, +5 Stress</i>",
            "es": "📋 <b>INTERCEPTACIÓN CORPORATIVA</b>\n\nUn canal cifrado Weyland-Yutani se abre brevemente — alguien desde fuera intenta contactar con Theta. Captas fragmentos antes de que la señal muera.\n\n<i>«...línea de tiempo Omega Cosecha acelerada... no intente contacto... prioridad recuperación espécimen...»</i>\n\nNo vienen a rescatarte.\n\n<i>+30 XP, +5 Estrés</i>"
        },
        "effects": {"xp": 30, "stress": 5}
    }
]
