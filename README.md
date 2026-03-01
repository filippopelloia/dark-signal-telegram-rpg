# 🛸 ALIEN: DARK SIGNAL — Telegram RPG Bot

Un RPG testuale completo ambientato nell'universo di Alien, progettato per Telegram.

---

## 🚀 SETUP RAPIDO

### 1. Clona / scarica il progetto
```bash
cd alien_dark_signal
```

### 2. Installa le dipendenze
```bash
pip install -r requirements.txt
```

### 3. Configura il bot
```bash
cp .env.example .env
```
Modifica `.env` e inserisci il tuo **BOT_TOKEN** da [@BotFather](https://t.me/BotFather).

### 4. Avvia
```bash
python bot.py
```

---

## 📁 STRUTTURA DEL PROGETTO

```
alien_dark_signal/
├── bot.py                        ← Entry point principale
├── config.py                     ← Configurazioni globali
├── requirements.txt
├── .env.example
│
├── database/
│   ├── models.py                 ← Modello Player (SQLAlchemy)
│   └── db.py                     ← Gestione sessioni async
│
├── game/
│   ├── i18n.py                   ← Localizzazione (IT/EN/ES)
│   ├── scene_engine.py           ← Engine delle scene
│   ├── combat.py                 ← Sistema di combattimento
│   ├── npcs.py                   ← NPC, achievement, missioni daily
│   └── scenes/
│       └── chapter1.json         ← Capitolo 1 completo (+ lore)
│
├── handlers/
│   └── main_handlers.py          ← Tutti i callback e comandi
│
└── localization/
    ├── it.json
    ├── en.json
    └── es.json
```

---

## 🎮 MECCANICHE DI GIOCO

### Statistiche personaggio (1–10)
| Stat | Uso |
|------|-----|
| Forza | Combattimento, azioni fisiche |
| Intelligenza | Puzzle, hacking, lore nascosta |
| Furtività | Evitare xenomorfi, infiltrazione |
| Ingegneria | Riparare, costruire trappole |
| Resistenza | HP, sopravvivenza ambienti ostili |
| Carisma | Convincere NPC, leadership |
| Fortuna | Modificatore casuale |
| Adattabilità | Bonus in situazioni nuove |

### Background disponibili
- 🪖 **Colonial Marine** — Forza/Resistenza
- 🔬 **Scienziato W-Y** — Intelligenza/Stealth
- 🔧 **Tecnico** — Ingegneria/Resistenza  
- 🧠 **Sopravvissuto** — Adattabilità/Fortuna
- 🤖 **Sintetico** — Intelligenza, no panico

### Tratti psicologici
- 🧊 Freddo e Razionale
- ⚡ Istintivo e Coraggioso
- 👁️ Paranoico
- 💗 Empatico

### Sistema XP & Level Up
- XP da scene, scelte coraggiose, lore trovata, combattimento
- Ogni livello (100 XP × livello): +2 punti stat da distribuire
- Livello massimo: 20

### Missione Giornaliera
- Disponibile ogni 24h
- Streak bonus per 7 giorni consecutivi
- XP + oggetti rari

### Permadeath (Nostromo Mode)
- Morte permanente, nessun checkpoint
- Storie esclusive e finale segreto
- Titolo speciale: ☠️ Il Vero Sopravvissuto

---

## 📖 STORIA — ALIEN: DARK SIGNAL

**Anno 2197.** La Weyland-Yutani ha dichiarato estinta la minaccia xenomorfa. Bugia.

La **Prometheus Station Theta** — classificata Omega — è silenziosa da 72 ore. Il giocatore guida una squadra di risposta rapida verso la verità su **Progetto Architetto**: xenomorfi ibridi con DNA di Engineer, capaci di pianificare, apprendere, adattarsi.

### Capitoli
1. **Silenzio di Theta** — Arrivo, primo contatto, scoperta del segreto
2. **Gli Architetti** — Discesa nei livelli, tradimento interno
3. **Codice Nero** — Database segreti, rivelazione AJAX-7
4. **La Regina degli Architetti** — Boss finale multi-fase
5. **Segnale verso Casa** — Fuga, 4 finali alternativi

### NPC Principali
- 🤖 **AJAX-7** — Sintetico ambiguo, lealtà dipende dalle scelte
- 🪖 **Cpl. Sarah Chen** — Colonial Marine, protettiva
- 🔬 **Dr. Marcus Okafor** — Xenobiologo, complice?
- 🎖️ **Lt. Ray Vance** — Comandante, mission-focused
- 🧬 **Dr. Petra Morel** — Sopravvissuta, conosce la verità

---

## 🔧 AGGIUNGERE CAPITOLI

Crea `game/scenes/chapter2.json` con la stessa struttura di `chapter1.json`:

```json
{
  "chapter": 2,
  "title": {"en": "THE ARCHITECTS", ...},
  "intro": {"en": "...", ...},
  "scenes": {
    "c2_scene1": {
      "id": "c2_scene1",
      "text": {"en": "...", "it": "...", "es": "..."},
      "choices": [...]
    }
  },
  "lore_entries": {...}
}
```

La scene engine carica **automaticamente** tutti i JSON nella cartella `scenes/`.

---

## 🌐 COMANDI TELEGRAM

| Comando | Funzione |
|---------|----------|
| `/start` | Menu principale |
| `/profilo` | Scheda personaggio |
| `/inventario` | Oggetti posseduti |
| `/archivio` | Lore raccolta |
| `/mappa` | Mappa ASCII stazione |
| `/obiettivi` | Achievement |
| `/salva` | Salva manuale |

---

## ☁️ DEPLOY SU SERVER

Per girare 24/7 su un VPS (es. Ubuntu):

```bash
# Con systemd
sudo nano /etc/systemd/system/alien-bot.service
```

```ini
[Unit]
Description=Alien Dark Signal Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/alien_dark_signal
ExecStart=/usr/bin/python3 /home/ubuntu/alien_dark_signal/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable alien-bot
sudo systemctl start alien-bot
```

---

## 📊 DATABASE

SQLite per default (file locale `alien_dark_signal.db`).  
Per PostgreSQL su produzione, cambia nel `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/aliendb
```
E aggiungi `asyncpg` ai requirements.

---

*Weyland-Yutani Corp — "Building Better Worlds"*  
*⚠️ Classificazione: Omega. Accesso non autorizzato è perseguibile.*
