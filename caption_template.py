"""
caption_template.py — Three caption styles for Telegram.
"""

from config import Config


def _stars(rating: str) -> str:
    try:
        r = float(str(rating).split("/")[0])
        f = round(r / 2)
        return "⭐" * f + "☆" * (5 - f)
    except Exception:
        return ""


def generate_caption(info: dict, filename: str = None, template: str = None) -> str:
    t = template or Config.DEFAULT_TEMPLATE
    if t == "minimal":
        cap = _minimal(info, filename)
    elif t == "full":
        cap = _full(info, filename)
    else:
        cap = _default(info, filename)
    return cap[:Config.MAX_CAPTION_LEN]


# ──────────── Default ────────────

def _default(info: dict, filename: str = None) -> str:
    title = info.get("title", "Unknown")
    year  = info.get("year", "")
    lines = [f"🎬 **{title}**" + (f" ({year})" if year else "")]

    if info.get("imdb_rating"):
        lines.append(f"⭐ **IMDB:** {info['imdb_rating']}/10  {_stars(info['imdb_rating'])}")
    if info.get("genre"):
        lines.append(f"🎭 **Genre:** {info['genre']}")
    if info.get("runtime"):
        lines.append(f"⏱️ **Runtime:** {info['runtime']}")
    if info.get("director"):
        lines.append(f"🎥 **Director:** {info['director']}")
    if info.get("actors"):
        top3 = ", ".join(info["actors"].split(", ")[:3])
        lines.append(f"👥 **Cast:** {top3}")
    if info.get("language"):
        lines.append(f"🌐 **Language:** {info['language']}")
    if info.get("released"):
        lines.append(f"📅 **Released:** {info['released']}")
    if info.get("rated"):
        lines.append(f"🔞 **Rated:** {info['rated']}")

    if info.get("plot"):
        plot = info["plot"][:300] + ("…" if len(info["plot"]) > 300 else "")
        lines.append(f"\n📝 **Plot:**\n{plot}")

    if info.get("imdb_id"):
        lines.append(f"\n🔗 [View on IMDB](https://www.imdb.com/title/{info['imdb_id']}/)")
    if filename:
        lines.append(f"📁 `{filename}`")

    return "\n".join(lines)


# ──────────── Minimal ────────────

def _minimal(info: dict, filename: str = None) -> str:
    title  = info.get("title", "Unknown")
    year   = info.get("year", "")
    rating = info.get("imdb_rating", "N/A")
    genre  = info.get("genre", "")
    lines  = [
        f"🎬 **{title}**" + (f" ({year})" if year else ""),
        f"⭐ {rating}/10 | 🎭 {genre}",
    ]
    if info.get("imdb_id"):
        lines.append(f"[IMDB ↗](https://www.imdb.com/title/{info['imdb_id']}/)")
    if filename:
        lines.append(f"`{filename}`")
    return "\n".join(lines)


# ──────────── Full ────────────

def _full(info: dict, filename: str = None) -> str:
    title = info.get("title", "Unknown")
    year  = info.get("year", "")
    div   = "━━━━━━━━━━━━━━━━━━━━━━"
    lines = [div, f"🎬 **{title}**" + (f" ({year})" if year else ""), div]

    if info.get("imdb_rating"):
        lines.append(f"⭐ **IMDB:** {info['imdb_rating']}/10  {_stars(info['imdb_rating'])}")

    rt = info.get("ratings", {}).get("rt")
    mc = info.get("ratings", {}).get("mc")
    if rt: lines.append(f"🍅 **Rotten Tomatoes:** {rt}")
    if mc: lines.append(f"🎯 **Metacritic:** {mc}")

    for emoji, key, label in [
        ("🎭", "genre",    "Genre"),
        ("⏱️", "runtime",  "Runtime"),
        ("🎥", "director", "Director"),
        ("✍️", "writer",   "Writer"),
        ("👥", "actors",   "Cast"),
        ("🌐", "language", "Language"),
        ("🌍", "country",  "Country"),
        ("📅", "released", "Released"),
        ("🔞", "rated",    "Rated"),
        ("💰", "box_office","Box Office"),
        ("🏆", "awards",   "Awards"),
        ("📺", "total_seasons","Seasons"),
    ]:
        if info.get(key):
            lines.append(f"{emoji} **{label}:** {info[key]}")

    if info.get("plot"):
        plot = info["plot"][:400] + ("…" if len(info["plot"]) > 400 else "")
        lines.append(f"\n📝 **Plot:**\n{plot}")

    if info.get("imdb_id"):
        lines.append(f"\n🔗 [View on IMDB](https://www.imdb.com/title/{info['imdb_id']}/)")
    if filename:
        lines.append(f"📁 `{filename}`")

    lines.append(div)
    return "\n".join(lines)
