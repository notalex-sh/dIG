#!/usr/bin/env python3

import re
import json
import random
import time
import urllib.parse
from typing import Any, Optional, List, Dict, Set, Tuple
from rich.text import Text

from utils.constants import LYNX_HOSTS, SOCIAL_HOSTS

URL_RE = re.compile(r"(https?://[^\s\)\]]+)", flags=re.IGNORECASE)

def add_request_jitter(min_delay: float = 0.5, max_delay: float = 2.0):
    # add random delay between requests to appear more human
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def not_found(msg: str = "Not found/returned") -> Text:
    return Text(msg, style="bold red")

def ok_text(s: str) -> Text:
    return Text(s, style="bold green")

def fmt_bool_found(b: Optional[bool]) -> Text:
    if b is True:
        return Text("Yes", style="bold green")
    if b is False:
        return Text("No", style="bold red")
    return not_found()

def shorten_url_for_display(u: Optional[str], max_len: int = 70) -> Optional[Text]:
    if not u:
        return None
    try:
        sp = urllib.parse.urlsplit(u)
        host = sp.netloc
        path = sp.path or "/"
        parts = [p for p in path.split("/") if p]
        tail = "/".join(parts[-2:]) if parts else ""
        q = urllib.parse.parse_qsl(sp.query, keep_blank_values=True)
        q_label = f"?{q[0][0]}=…" if q else ""
        label = f"{host}/{tail}{q_label}" if tail else f"{host}{q_label}"
        if len(label) > max_len:
            label = label[: max_len - 1] + "…"
        return Text(label, style=f"underline link {u}")
    except Exception:
        return Text(u, style=f"underline link {u}")

def norm_handle(s: str) -> str:
    return s.strip().lstrip("@").lower()

def try_parse_json_text(text: str) -> Any:
    t = text.strip()
    if t.startswith("for (;;);"):
        t = t[len("for (;;);"):]
    return json.loads(t)

def clean_cdn_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    return url.split('?', 1)[0]

def unwrap_lynx(u: str) -> str:
    try:
        parsed = urllib.parse.urlparse(u)
        host = parsed.netloc.lower()
        if host in LYNX_HOSTS:
            qs = urllib.parse.parse_qs(parsed.query)
            if "u" in qs and qs["u"]:
                return urllib.parse.unquote(qs["u"][0])
    except Exception:
        pass
    return u

def extract_bio_entities(user: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    mentions: Set[str] = set()
    hashtags: Set[str] = set()
    ents = (user.get("biography_with_entities") or {}).get("entities") or []
    for ent in ents:
        u = (ent.get("user") or {}).get("username")
        if u:
            mentions.add(u)
        h = (ent.get("hashtag") or {}).get("name") if isinstance(ent.get("hashtag"), dict) else None
        if h:
            hashtags.add(h.lstrip("#"))
    return sorted(mentions), sorted(hashtags)

def extract_links_from_user_obj(user: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, str]], Optional[str]]:
    urls = set()
    ext = user.get("external_url")
    if ext:
        urls.add(ext)
    for link in (user.get("bio_links") or []):
        url = link.get("url") or link.get("lynx_url") or link.get("url_wrapper")
        if url:
            urls.add(url)
    entities = (user.get("biography_with_entities") or {}).get("entities") or []
    for ent in entities:
        url = ent.get("url") or ent.get("link") or ent.get("href")
        if url:
            urls.add(url)
    bio = user.get("biography") or ""
    for m in URL_RE.findall(bio):
        urls.add(m.strip(").,]"))
    unwrapped = {unwrap_lynx(u) for u in urls}
    websites = sorted([u for u in unwrapped if u])
    socials: List[Dict[str, str]] = []
    for u in websites:
        host = re.sub(r"^https?://", "", u, flags=re.I).split("/")[0].lower()
        for known_host, svc in SOCIAL_HOSTS.items():
            if host.endswith(known_host):
                socials.append({"service": svc, "url": u})
                break
    fb_biolink_url = None
    fb_biolink = user.get("fb_profile_biolink")
    if isinstance(fb_biolink, dict) and fb_biolink.get("url"):
        fb_biolink_url = fb_biolink.get("url")
    return websites, socials, fb_biolink_url

def pick_hd_profile_pic(user_like: Dict[str, Any]) -> Optional[str]:
    if not isinstance(user_like, dict):
        return None
    return (
        user_like.get("profile_pic_url_hd")
        or (user_like.get("hd_profile_pic_url_info") or {}).get("url")
        or user_like.get("profile_pic_url")
    )

def search_url(engine: str, query: str) -> str:
    engines = {
        "google": f"https://www.google.com/search?q={urllib.parse.quote(query)}",
        "bing": f"https://www.bing.com/search?q={urllib.parse.quote(query)}",
        "duckduckgo": f"https://duckduckgo.com/?q={urllib.parse.quote(query)}",
        "yandex": f"https://yandex.com/search/?text={urllib.parse.quote(query)}",
        "baidu": f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}",
    }
    return engines.get(engine, "")

def advice_from_error(status: Optional[int], body: Optional[str]) -> List[str]:
    tips = []
    if status in (403, 429) or (body and ("Please wait a few minutes" in body or "rate limit" in body.lower())):
        tips += [
            "🔄 Rotate IP or try a different network (residential > datacenter)",
            "⏱️ Slow down requests; add jitter/backoff between calls",
            "🕐 Try again later; temporary rate limiting is common",
            "🔀 Avoid reusing the exact same headers too frequently",
            "🌐 Consider using rotating proxies for better success",
            "🎭 Use more diverse User-Agent strings",
        ]
    elif status and 500 <= status < 600:
        tips += ["⚠️ Server-side hiccup; retry later"]
    elif status == 401:
        tips += ["🔑 Authentication may be required for this endpoint"]
    elif status == 404:
        tips += ["❓ User may not exist or account may be deleted/suspended"]
    return tips

def owner_edges(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return user["edge_owner_to_timeline_media"]["edges"]
    except Exception:
        return []

def coauthors_from_node(node: Dict[str, Any]) -> List[str]:
    coauthors: Set[str] = set()
    for key in ("coauthor_producers", "coauthor_producer", "collaborator_users", "collaborators"):
        obj = node.get(key) or {}
        if isinstance(obj, dict) and isinstance(obj.get("edges"), list):
            for e in obj["edges"]:
                u = ((e.get("node") or {}).get("username")) or ((e.get("user") or {}).get("username"))
                if u:
                    coauthors.add(u)
        elif isinstance(obj, list):
            for maybe_user in obj:
                if isinstance(maybe_user, dict):
                    u = maybe_user.get("username") or ((maybe_user.get("user") or {}).get("username"))
                    if u:
                        coauthors.add(u)
    return sorted([u for u in coauthors if u])

def row_text_list(urls: List[str]) -> Text:
    pieces: List[Text] = []
    for i, u in enumerate(urls):
        if i > 0:
            pieces.append(Text(" • "))
        pieces.append(shorten_url_for_display(u) or Text(u, style=f"underline link {u}"))
    return Text().join(pieces) if pieces else not_found()