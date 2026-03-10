"""
utils/helpers.py — Shared utility functions.
"""

import os
import re
import logging
from io import BytesIO
import aiohttp
from PIL import Image

logger = logging.getLogger(__name__)

VIDEO_EXTS = re.compile(r"\.(mkv|mp4|avi|mov|ts|m4v|wmv|flv|webm)$", re.IGNORECASE)
QUALITY_TAGS = re.compile(
    r"\b(480p|720p|1080p|2160p|4K|UHD|HDR|HDRip|BluRay|BDRip|WEB[-.]?DL|WEBRip|"
    r"HEVC|x264|x265|H\.264|H\.265|AAC|DD5\.1|DTS|10bit|YIFY|RARBG|YTS|"
    r"NF|AMZN|DSNP|HULU|HBO|REPACK|PROPER|EXTENDED|THEATRICAL)\b",
    re.IGNORECASE,
)


def parse_filename(name: str) -> tuple[str, str | None]:
    """Return (clean_title, year_or_None) extracted from a media filename."""
    name = VIDEO_EXTS.sub("", name)
    name = re.sub(r"[\.\-\_]", " ", name)
    name = QUALITY_TAGS.sub("", name)
    name = re.sub(r"\s{2,}", " ", name).strip()

    year_match = re.search(r"(19|20)\d{2}", name)
    year = year_match.group() if year_match else None
    if year_match:
        name = name[:year_match.start()].strip()

    # Remove trailing parentheses/brackets noise
    name = re.sub(r"[\[\(].*?[\]\)]", "", name).strip()
    return name, year


def is_media_file(filename: str) -> bool:
    return bool(VIDEO_EXTS.search(filename or ""))


async def download_image(url: str) -> BytesIO | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    return BytesIO(await r.read())
    except Exception as e:
        logger.warning("Image download failed: %s", e)
    return None


def save_thumbnail(img_bytes: BytesIO, path: str = "/tmp/thumb.jpg") -> str:
    img = Image.open(img_bytes).convert("RGB")
    img.thumbnail((320, 320))
    img.save(path, "JPEG", quality=85)
    return path


def human_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
