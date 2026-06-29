# 🎵 Music Watermark Bot

A personal Telegram bot that takes an audio file (MP3/M4A) you send it and applies your jingle/voice-tag — at the **start and end**, at **regular intervals**, or **both** — then sends the watermarked file back. Powered by Pyrogram + FFmpeg, with MongoDB-backed settings persistence.

```
your_audio.mp3  →  [jingle] + your_audio + [jingle]   (start_end mode)
your_audio.mp3  →  audio…[jingle]…audio…[jingle]…     (interval mode)
your_audio.mp3  →  [jingle] + audio…[jingle]…[jingle] (both mode)
```

---

## ✨ Features

### 🔊 Watermark Modes
| Mode | Description |
|---|---|
| `both` | Jingle at start + end, **plus** at regular intervals inside |
| `start_end` | Jingle only at the very start and end |
| `interval` | Jingle repeated every N seconds throughout the audio |
| `none` | No jingle — only metadata tagging |

### 🎚 Interval Controls
- **Interval duration** — how often the jingle plays (e.g. every 120 s)
  - Quick presets: 30 s, 60 s, 90 s, 120 s, 180 s, 300 s
  - Fine-tune with ±10 s buttons
  - Or set an exact value with `/setinterval <seconds>`
- **Music during jingle** — two modes:
  - 🔊 **Mix** — jingle overlays on top of music (both play simultaneously)
  - 🔇 **Full Stop** — music completely pauses while the jingle plays, then resumes
- **Volume** _(mix mode only)_ — jingle loudness relative to source (0.0–1.0, default 0.7)
- **Fade** — smooth fade-in / fade-out on the jingle to avoid harsh cuts (0–2000 ms, default 300 ms)

### 🏷 Metadata Tagging
- Automatically tags output audio with artist and title suffix
- Preserves original cover art and all existing tags
- Configurable via `/default` → **Tagging** settings

### 🛠 Admin Commands
| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/default` | Open the interactive settings panel |
| `/setinterval <s>` | Set exact interval in seconds (e.g. `/setinterval 75`) |
| `/setjingle` | Reply to an audio file to set it as the custom jingle |

### 🌐 Deployment-Ready
- Built-in keep-alive web server for **Render free tier** + UptimeRobot
- **MongoDB persistence** for settings (with automatic `settings.json` fallback)
- Docker support with `Dockerfile` + `.dockerignore`
- Graceful shutdown — closes DB connection cleanly on `SIGINT` / `SIGTERM`

---

## 📁 Project Structure

```text
watermark_bot/
├── config.py              # Configuration (reads from env vars + .env)
├── main.py                # Entrypoint: starts bot + web server
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container build
├── .dockerignore
├── .env.example           # Template for local env vars
├── jingle.mp3             # ⚠️ YOUR watermark clip (add this manually)
├── settings.json          # Auto-generated fallback settings store
│
├── bot/
│   ├── __init__.py        # Initializes Pyrogram Client with plugins
│   └── handlers/
│       ├── __init__.py
│       ├── start.py       # /start command
│       ├── audio.py       # Audio file handler (main watermark pipeline)
│       └── settings.py    # /default settings panel + all callbacks
│
├── server/
│   └── web_server.py      # Keep-alive HTTP server (port 8080)
│
└── utils/
    ├── ffmpeg.py          # FFmpeg watermarking (mix + full-stop modes)
    ├── metadata.py        # Duration, tags, cover art helpers
    ├── settings_manager.py# MongoDB + JSON settings CRUD
    └── progress.py        # Upload/download progress callbacks
```

---

## ⚙️ Configuration

All config is read from **environment variables** (with `.env` fallback for local dev).

| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `MONGO_URI` | optional | MongoDB connection string for settings persistence |
| `JINGLE_PATH` | optional | Path to jingle file (default: `jingle.mp3`) |
| `MAX_FILE_SIZE_MB` | optional | Max accepted file size in MB (default: `300`) |
| `PORT` | auto (Render) | Port for the keep-alive web server (default: `8080`) |

> If `MONGO_URI` is not set, settings are saved to `settings.json` automatically.

---

## 🔧 Settings Reference

All settings are stored in MongoDB (or `settings.json`) and controlled via `/default`.

| Setting | Default | Description |
|---|---|---|
| `mode` | `both` | Watermark mode: `both`, `start_end`, `interval`, `none` |
| `interval_seconds` | `120` | Seconds between interval jingles |
| `interval_mute_music` | `False` | `True` = Full Stop; `False` = Mix/Overlay |
| `interval_volume` | `0.7` | Jingle volume in Mix mode (0.0–1.0) |
| `interval_fade_ms` | `300` | Fade-in/out duration in ms (0–2000) |
| `tagging_enabled` | `True` | Auto-tag title/artist on output |
| `tag_artist` | `@PFMXBOT` | Artist tag written to output file |
| `tag_title_suffix` | ` @PFMXBOT` | Appended to the original title |

---

## 🖥️ Option 1: Run Locally

```bash
# 1. Install ffmpeg
sudo apt install ffmpeg          # Linux / WSL
brew install ffmpeg              # macOS

# 2. Install Python deps
pip install -r requirements.txt

# 3. Copy env template and fill in values
cp .env.example .env
nano .env

# 4. Add your jingle
cp /path/to/your/jingle.mp3 .

# 5. Run
PYTHONPATH=. python main.py
```

`config.py` loads `.env` via `python-dotenv` automatically — no manual `export` needed.

---

## 🐳 Option 2: Run with Docker

```bash
# 1. Fill in .env (see Option 1, step 3)

# 2. Build
docker build -t watermark-bot .

# 3. Run
docker run -d \
  --env-file .env \
  -p 8080:8080 \
  --name watermark-bot \
  watermark-bot
```

> `jingle.mp3` is baked in via `COPY . .`. To use a file outside the repo:
> `-v $(pwd)/jingle.mp3:/app/jingle.mp3`

---

## ☁️ Option 3: Deploy on Render (Free Tier)

Render's free tier requires a **Web Service** (not Background Worker) — the bot starts a keep-alive HTTP server on port 8080 to satisfy this.

1. Push repo to GitHub (include `jingle.mp3` or mount it separately)
2. On Render: **New → Web Service** → connect repo → choose **Docker**
3. Add environment variables: `API_ID`, `API_HASH`, `BOT_TOKEN`, and optionally `MONGO_URI`
4. Deploy

### Keep it always-on with UptimeRobot

Render free tier sleeps after 15 min of inactivity. Prevent this:

1. Sign up at [uptimerobot.com](https://uptimerobot.com) (free)
2. **New Monitor → HTTP(s)**
3. URL: `https://your-app.onrender.com`
4. Interval: **5 minutes**

> ⚠️ Free tier = ~750 instance-hours/month. One always-on bot uses ~720–750 h — fine for a single service.

---

## 🛠️ How It Works

### Audio Pipeline

```
User sends MP3/M4A
      │
      ▼
Bot downloads → applies FFmpeg filter_complex
      │
      ├── [start_end] : asplit → concat(jingle + main + jingle)
      │
      ├── [interval / mix] : asplit jingle N times → adelay each
      │                      → amix all with volume + afade
      │
      ├── [interval / full stop] : atrim main into segments
      │                           → concat(seg0 + jingle + seg1 + ...)
      │
      └── [both] : combines start_end concat around interval logic
      │
      ▼
Metadata tags + cover art preserved
      │
      ▼
Bot sends watermarked file back → temp files deleted
```

### Full Stop Mode (interval)

When `interval_mute_music = True`, FFmpeg splits the main audio into segments at each jingle timestamp using `atrim`, then reassembles them with the jingle inserted between segments using `concat`:

```
Main audio:  [====Seg1====]        [====Seg2====]        [===Seg3===]
Jingles:                  [Jingle]              [Jingle]
Output:      [====Seg1====][Jingle][====Seg2====][Jingle][===Seg3===]
```

---

## 🔒 Note on `jingle.mp3` and Git

Since `jingle.mp3` is your personal voice-tag, you may not want it in a public repo:

- Keep the repo **private**, or
- Add `jingle.mp3` to `.gitignore` and upload it separately, or
- Use Render's **Disk** feature to persist it across deploys
- Or send any audio to the bot with `/setjingle` (reply to the file) to set a custom jingle without redeploying
