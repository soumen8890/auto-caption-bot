"""
imdb_helper.py — OMDB + TMDB API client with MongoDB caching.
"""

import logging
import aiohttp
from config import Config
from database import get_cached, set_cache

logger = logging.getLogger(__name__)

OMDB_BASE = "http://www.omdbapi.com/"
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG  = "https://image.tmdb.org/t/p/w500"


class IMDBHelper:

    # ─────────────── Search OMDB ───────────────

    async def search(self, title: str, year: str = None) -> list[dict]:
        results = []
        for media_type in ("movie", "series"):
            params = {"apikey": Config.OMDB_KEY, "s": title, "type": media_type}
            if year:
                params["y"] = year
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.get(OMDB_BASE, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                        data = await r.json()
                        if data.get("Response") == "True":
                            for item in data.get("Search", []):
                                results.append({
                                    "title":   item.get("Title"),
                                    "year":    item.get("Year"),
                                    "imdb_id": item.get("imdbID"),
                                    "type":    item.get("Type"),
                                    "poster":  item.get("Poster") if item.get("Poster") != "N/A" else None,
                                    "rating":  "N/A",
                                })
            except Exception as e:
                logger.warning("OMDB search error (%s): %s", media_type, e)
            if results:
                break
        return results

    # ─────────────── Full Details (with cache) ───────────────

    async def get_by_id(self, imdb_id: str) -> dict | None:
        # Check MongoDB cache first
        cached = await get_cached(imdb_id)
        if cached:
            logger.info("Cache hit: %s", imdb_id)
            return cached

        params = {"apikey": Config.OMDB_KEY, "i": imdb_id, "plot": "full"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(OMDB_BASE, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    data = await r.json()
                    if data.get("Response") != "True":
                        return None
                    info = self._parse_omdb(data)

                    # Upgrade poster via TMDB if key set
                    if Config.TMDB_KEY:
                        hq = await self._tmdb_poster(imdb_id)
                        if hq:
                            info["poster"] = hq

                    # Store in MongoDB cache
                    await set_cache(imdb_id, info)
                    return info
        except Exception as e:
            logger.warning("OMDB get_by_id error: %s", e)
        return None

    # ─────────────── Parsers ───────────────

    def _parse_omdb(self, d: dict) -> dict:
        def c(v):
            return v if v and v != "N/A" else None

        ratings = {}
        for r in d.get("Ratings", []):
            src = r.get("Source", "")
            if "Internet Movie" in src:
                ratings["imdb"] = r.get("Value")
            elif "Rotten" in src:
                ratings["rt"]   = r.get("Value")
            elif "Metacritic" in src:
                ratings["mc"]   = r.get("Value")

        return {
            "title":          c(d.get("Title")),
            "year":           c(d.get("Year")),
            "released":       c(d.get("Released")),
            "runtime":        c(d.get("Runtime")),
            "genre":          c(d.get("Genre")),
            "director":       c(d.get("Director")),
            "writer":         c(d.get("Writer")),
            "actors":         c(d.get("Actors")),
            "plot":           c(d.get("Plot")),
            "language":       c(d.get("Language")),
            "country":        c(d.get("Country")),
            "awards":         c(d.get("Awards")),
            "poster":         c(d.get("Poster")),
            "imdb_rating":    c(d.get("imdbRating")),
            "imdb_votes":     c(d.get("imdbVotes")),
            "imdb_id":        c(d.get("imdbID")),
            "type":           c(d.get("Type")),
            "box_office":     c(d.get("BoxOffice")),
            "rated":          c(d.get("Rated")),
            "ratings":        ratings,
            "total_seasons":  c(d.get("totalSeasons")),
        }

    async def _tmdb_poster(self, imdb_id: str) -> str | None:
        try:
            url = f"{TMDB_BASE}/find/{imdb_id}"
            params = {"api_key": Config.TMDB_KEY, "external_source": "imdb_id"}
            async with aiohttp.ClientSession() as s:
                async with s.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    data = await r.json()
                    for key in ("movie_results", "tv_results"):
                        results = data.get(key, [])
                        if results and results[0].get("poster_path"):
                            return TMDB_IMG + results[0]["poster_path"]
        except Exception as e:
            logger.warning("TMDB poster error: %s", e)
        return None
