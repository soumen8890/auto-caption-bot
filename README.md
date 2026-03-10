# 🎬 IMDB Auto Caption & Thumbnail Changer Bot

A production-ready Telegram bot that automatically detects movie/show titles from filenames,
fetches IMDB data, replaces the media thumbnail with the official poster, and adds a rich
formatted caption — with full **MongoDB Atlas** persistence and one-click deploy to
**Render** and **Koyeb**.

---

## ✨ Features

| Feature | Detail |
|---|---|
| 🔍 Auto title detection | Strips quality tags, extracts year, handles all naming conventions |
| 🎬 IMDB data via OMDB | Rating, genre, runtime, director, cast, plot, awards, RT/Metacritic |
| 🖼️ Thumbnail replacement | Downloads official IMDB/TMDB poster, resizes to 320×320, sets as thumb |
| 🗄️ MongoDB Atlas | Per-user settings, per-chat config, IMDB cache (7-day TTL), global stats |
| ✏️ 3 caption templates | `default` · `minimal` · `full` — switchable per user via `/settings` |
| 📢 Channel/Group auto-caption | Whitelist channels; bot auto-processes every new upload |
| 📊 Stats & Admin | `/stats`, `/broadcast`, MongoDB-backed counters |
| 🌐 Health-check server | Built-in aiohttp server for Render/Koyeb uptime checks |
| 🚀 CI/CD | GitHub Actions → Docker Hub → auto-deploy Render + Koyeb |

---

## 📁 Project Structure

```
imdb_bot/
├── main.py                  # Entry point + health-check server
├── config.py                # All env-var configuration
├── database.py              # MongoDB Atlas (motor async)
├── imdb_helper.py           # OMDB + TMDB API client with cache
├── caption_template.py      # Caption builders (3 templates)
├── plugins/
│   ├── start.py             # /start /help /stats
│   ├── settings.py          # /settings inline keyboard
│   ├── search.py            # /search command
│   ├── media_handler.py     # Core: receive → IMDB → re-upload
│   └── admin.py             # /broadcast /adminstat
├── utils/
│   └── helpers.py           # filename parser, image downloader
├── requirements.txt
├── Dockerfile
├── render.yaml              # Render IaC config
├── koyeb.yaml               # Koyeb service definition
├── .env.example
└── .github/
    └── workflows/
        └── deploy.yml       # CI/CD pipeline
```

---

## 🚀 Quick Start (Local)

### 1. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/imdb-caption-bot
cd imdb-caption-bot
cp .env.example .env
# Edit .env with your keys
```

### 2. Get Required API Keys

| Key | Where to get |
|---|---|
| `API_ID` + `API_HASH` | https://my.telegram.org → App API |
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `OMDB_API_KEY` | https://www.omdbapi.com/apikey.aspx (free, 1000 req/day) |
| `MONGO_URI` | MongoDB Atlas (see below) |
| `TMDB_API_KEY` | https://www.themoviedb.org/settings/api (optional) |

### 3. Run

```bash
pip install -r requirements.txt
python main.py
```

---

## 🗄️ MongoDB Atlas Setup

1. Go to https://cloud.mongodb.com → **Create free cluster** (M0 — free forever)
2. **Database Access** → Add user (username + password)
3. **Network Access** → Add IP `0.0.0.0/0` (allow all — required for cloud hosts)
4. **Connect** → **Connect your application** → copy the URI
5. Replace `<password>` and set as `MONGO_URI` in your `.env` / host dashboard

```
mongodb+srv://myuser:mypassword@cluster0.abc123.mongodb.net/imdb_bot
```

---

## 🌐 Deploy to Render

### One-click (recommended)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Manual

1. Push your code to GitHub
2. Go to https://dashboard.render.com → **New → Web Service**
3. Connect your GitHub repo
4. Set **Runtime: Docker**, **Branch: main**
5. Add all environment variables from `.env.example`
6. Click **Create Web Service**
7. Copy the **Deploy Hook URL** (Settings → Deploy Hook) → add as `RENDER_DEPLOY_HOOK` GitHub Secret

---

## ☁️ Deploy to Koyeb

### Via Dashboard

1. https://app.koyeb.com → **Create Service → Web Service**
2. Connect GitHub repo → select branch `main`
3. Set **Build: Dockerfile**, **Port: 8080**, **Health path: /health**
4. Add all env vars from `.env.example`
5. Deploy

### Via CLI

```bash
# Install CLI
curl -fsSL https://raw.githubusercontent.com/koyeb/koyeb-cli/master/install.sh | bash

# Login
koyeb login

# Deploy
koyeb service create --file koyeb.yaml
```

### GitHub Secrets for auto-deploy

| Secret | Where to get |
|---|---|
| `KOYEB_TOKEN` | Koyeb dashboard → Account → API Credentials |
| `RENDER_DEPLOY_HOOK` | Render → Service → Settings → Deploy Hook |
| `DOCKER_USERNAME` | Your Docker Hub username |
| `DOCKER_PASSWORD` | Your Docker Hub password or access token |

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome & quick guide |
| `/help` | Full usage guide |
| `/search <title>` | Search IMDB inline with buttons |
| `/settings` | Switch caption template, toggle auto-caption |
| `/stats` | Public bot statistics |
| `/caption <title>` | Reply to a file to override detected title |
| `/broadcast` | *(Admin)* Broadcast message to all users |
| `/adminstat` | *(Admin)* Detailed statistics |

---

## 🎨 Caption Templates

**`default`** (recommended):
```
🎬 Oppenheimer (2023)
⭐ IMDB: 8.9/10  ⭐⭐⭐⭐⭐
🎭 Genre: Biography, Drama, History
⏱️ Runtime: 180 min
🎥 Director: Christopher Nolan
👥 Cast: Cillian Murphy, Emily Blunt, Matt Damon
🌐 Language: English
📅 Released: 21 Jul 2023

📝 Plot:
The story of J. Robert Oppenheimer…

🔗 View on IMDB
📁 Oppenheimer.2023.1080p.mkv
```

**`minimal`**: One-liner — title, rating, genre, IMDB link

**`full`**: Everything — RT, Metacritic, Box Office, Awards, Countries, all cast

---

## ⚠️ Notes

- OMDB free tier: **1,000 requests/day**. Results are cached in MongoDB for 7 days.
- The bot **re-uploads** the file — large files take time based on server speed.
- Render free tier **spins down** after 15 min of inactivity. Use Koyeb or Render paid for always-on.
- For channel auto-caption: add bot as admin with **Post Messages** permission, add channel ID to `AUTO_CAPTION_CHANNELS`.
