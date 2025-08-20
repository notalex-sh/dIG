#!/usr/bin/env python3

# just some console renderering stuff

import json
import random
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

from .banners import BANNERS
from .constants import LABEL_STYLE, FIELD_WIDTH, VALUE_OVERFLOW, SOCIAL_HOSTS
from .helpers import (
    not_found, ok_text, fmt_bool_found, 
    shorten_url_for_display, row_text_list,
    search_url, advice_from_error
)

console = Console()

def make_kv_table() -> Table:
    t = Table(
        box=box.MINIMAL,
        expand=True,
        show_header=False,
        pad_edge=False,
    )
    t.add_column(
        "Field",
        style=LABEL_STYLE,
        justify="left",
        no_wrap=True,
        overflow="crop",
        width=FIELD_WIDTH,
        min_width=FIELD_WIDTH,
        max_width=FIELD_WIDTH,
    )
    t.add_column(
        "Value",
        justify="left",
        no_wrap=False,
        overflow=VALUE_OVERFLOW,
        ratio=1,
    )
    return t

def render_header(username: str):
    banner = random.choice(BANNERS)
    banner_text = Text(banner, style="bold magenta", justify="center")
    console.print(banner_text)
    console.print(Text("Instagram Email Intelligence", justify="center", style="cyan"))
    console.print(Text(f"Target: @{username}", justify="center", style="dim"))
    console.rule(style="magenta")

def render_profile_block(fields: Dict[str, Any]):
    console.rule("📱 Profile", style="cyan")
    t = make_kv_table()
    t.add_row("Username", ok_text(fields.get("username") or ""))
    t.add_row("Name", ok_text(fields.get("name")) if fields.get("name") else not_found())
    t.add_row("Account", ok_text(fields.get("account_status")) if fields.get("account_status") else not_found())
    t.add_row("Verified", fmt_bool_found(fields.get("is_verified")))
    t.add_row("Business", fmt_bool_found(fields.get("is_business")))
    t.add_row("Category", ok_text(fields.get("category_name")) if fields.get("category_name") else not_found())
    t.add_row("Followers", ok_text(str(fields.get("followers"))) if fields.get("followers") is not None else not_found())
    t.add_row("Following", ok_text(str(fields.get("following"))) if fields.get("following") is not None else not_found())
    t.add_row("Posts", ok_text(str(fields.get("posts"))) if fields.get("posts") is not None else not_found())
    t.add_row("Instagram ID", ok_text(str(fields.get("instagram_id"))) if fields.get("instagram_id") else not_found())
    
    pfp_full = fields.get("hd_profile_pic_url_original") or fields.get("hd_profile_pic_url")
    if pfp_full:
        val = shorten_url_for_display(pfp_full) or Text(pfp_full, style=f"underline link {pfp_full}")
        val = Text.assemble(val)
        val.stylize("bold green", 0, len(val))
        val.append(Text("  (link may expire; use --download-pfp)", style="dim"))
        t.add_row("HD PFP", val)
    else:
        t.add_row("HD PFP", not_found())
    
    console.print(t)
    console.print()

def render_bio(fields: Dict[str, Any]):
    console.rule("📝 Bio & Entities", style="cyan")
    t = make_kv_table()
    bio = fields.get("bio")
    t.add_row("Bio", ok_text(bio) if bio else not_found())
    mentions = fields.get("bio_mentions") or []
    hashtags = fields.get("bio_hashtags") or []
    t.add_row("Mentions", ok_text(", ".join(f"@{m}" for m in mentions)) if mentions else not_found("none"))
    t.add_row("Hashtags", ok_text(", ".join(f"#{h}" for h in hashtags)) if hashtags else not_found("none"))
    console.print(t)
    console.print()

def render_contacts_and_recovery(fields: Dict[str, Any], lookup: Dict[str, Any]):
    console.rule("🔐 Obfuscated Contact & Recovery", style="cyan")
    c = make_kv_table()
    oe = fields.get("obfuscated_email")
    op = fields.get("obfuscated_phone")
    c.add_row("Obfuscated Email", ok_text(oe) if oe else not_found("not present"))
    c.add_row("Obfuscated Phone", ok_text(op) if op else not_found("not present"))
    console.print(c)
    console.print()
    
    rec_fields = {
        "has_valid_phone": lookup.get("has_valid_phone"),
        "can_email_reset": lookup.get("can_email_reset"),
        "can_sms_reset": lookup.get("can_sms_reset"),
        "can_wa_reset": lookup.get("can_wa_reset"),
    }
    rec = make_kv_table()
    if not any(v is not None for v in rec_fields.values()):
        rec.add_row("—", not_found("No recovery flags returned"))
    else:
        for k, v in rec_fields.items():
            rec.add_row(k, fmt_bool_found(v))
    console.print(rec)
    console.print()

def render_business_block(fields: Dict[str, Any]):
    console.rule("💼 Business & Public Contact", style="cyan")
    keys = [
        "business_contact_method", "business_email", "business_phone_number",
        "business_address_json", "category_name",
        "public_email", "public_phone",
    ]
    t = make_kv_table()
    any_present = any(fields.get(k) not in (None, "", []) for k in keys)
    if not any_present:
        t.add_row("—", not_found("No business/contact fields returned"))
    else:
        for k in keys:
            v = fields.get(k)
            if v in (None, "", []) or (isinstance(v, (list, dict)) and not v):
                t.add_row(k, not_found())
            else:
                t.add_row(k, ok_text(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)))
    console.print(t)
    console.print()

def render_socials_block(fields: Dict[str, Any]):
    console.rule("🌐 Socials & Websites", style="cyan")
    t = make_kv_table()
    
    from collections import defaultdict
    grouped: Dict[str, List[str]] = defaultdict(list)
    non_social_websites = []

    social_urls = set()
    for s in (fields.get("linked_socials") or []):
        if s.get("url"):
            social_urls.add(s.get("url"))
            svc = s.get("service")
            url = s.get("url")
            if svc and url:
                grouped[svc].append(url)

    for url in (fields.get("websites") or []):
        if url not in social_urls:
            non_social_websites.append(url)

    if non_social_websites:
        t.add_row("📌 Websites", row_text_list(non_social_websites))

    fbp = fields.get("fb_profile_biolink_url")
    if fbp:
        t.add_row("📘 FB Profile", shorten_url_for_display(fbp))
    
    if fields.get("has_threads") and fields.get("username"):
        threads_urls = grouped.get("threads") or []
        if threads_urls:
            t.add_row("🧵 Threads", row_text_list(threads_urls))
        else:
            t.add_row("🧵 Threads", ok_text(f"Exists (probable: https://www.threads.net/@{fields['username']})"))
    elif grouped.get("threads"):
        t.add_row("🧵 Threads", row_text_list(grouped["threads"]))

    instagram_urls = grouped.get("instagram") or []
    current_username = fields.get("username", "").lower()
    other_instagrams = []
    
    for url in instagram_urls:
        import re
        match = re.search(r'instagram\.com/([^/?]+)', url)
        if match:
            found_username = match.group(1).lower()
            if found_username != current_username:
                other_instagrams.append(url)
    
    if other_instagrams:
        t.add_row("📸 Instagram (alt)", row_text_list(other_instagrams))
    
    social_icons = {
        "twitter": "🐦",
        "facebook": "📘",
        "linkedin": "💼",
        "github": "🐙",
        "youtube": "📺",
        "tiktok": "🎵",
        "discord": "💬",
        "telegram": "✈️",
        "reddit": "🤖",
        "pinterest": "📌",
        "snapchat": "👻",
        "spotify": "🎧",
        "twitch": "🎮",
        "linktree": "🌳",
        "beacons": "🔗",
        "carrd": "🔗",
        "onlyfans": "🔞",
        "patreon": "🎨",
        "substack": "📝",
        "vsco": "📷",
        "behance": "🎨",
        "soundcloud": "☁️",
        "bandcamp": "🎸",
        "mastodon": "🐘",
        "bluesky": "🦋",
        "deviantart": "🎨",
        "tumblr": "📝",
    }
    
    for svc in sorted(grouped.keys()):
        if svc in ["threads", "instagram"]:  
            continue
        urls = grouped[svc]
        if urls:
            icon = social_icons.get(svc, "🔗")
            service_name = svc.title()
            t.add_row(f"{icon} {service_name}", row_text_list(urls))

    if not non_social_websites and not grouped and not fbp and not fields.get("has_threads"):
        t.add_row("—", not_found("No linked socials or websites found"))
    
    console.print(t)
    console.print()

def render_collabs(collabs: List[Dict[str, Any]]):
    console.rule("🤝 Collaborations", style="cyan")
    if not collabs:
        console.print(not_found("No collaborated posts found (first page)"))
        console.print()
        return

    seen_urls = set()
    unique_collabs = []
    for c in collabs:
        url = c.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_collabs.append(c)
    
    for idx, c in enumerate(unique_collabs, 1):
        url = c.get("url", "")
        short = shorten_url_for_display(url) or Text(url, style=f"underline link {url}")
        co = ", ".join(c.get("coauthors", [])) if c.get("coauthors") else ""
        line = Text(f"{idx}. ").append(short)
        if co:
            line.append(Text(" — Co-authors: "))
            line.append(ok_text(co))
        console.print(line)
    console.print()

def render_osint_tools(username: str, fields: Dict[str, Any]):

    console.rule("🔍 OSINT Tools & Resources", style="cyan")
    
    console.print(Text("External Tools:", style="bold yellow"))
    tools_table = make_kv_table()
    
    name = fields.get("name", "").replace(" ", "%20") if fields.get("name") else ""
    email = fields.get("obfuscated_email", "")
    
    tools = [
        ("WhatsMyName", f"https://whatsmyname.app/?q={username}"),
        ("NameCheckr", f"https://www.namecheckr.com/availability/{username}"),
        ("UserSearch", f"https://usersearch.org/results_normal.php?URL_username={username}"),
        ("Sherlock", f"https://sherlock-project.github.io/?q={username}"),
        ("PimEyes", f"https://pimeyes.com/en (upload profile pic)"),
        ("TinEye", f"https://tineye.com (reverse image search)"),
        ("Have I Been Pwned", f"https://haveibeenpwned.com/account/{email}" if email else "https://haveibeenpwned.com"),
        ("Dehashed", f"https://dehashed.com/search?query={username}"),
        ("IntelX", f"https://intelx.io/?s={username}"),
        ("OSINT Industries", f"https://osint.industries/search/{username}"),
        ("Holehe", f"https://github.com/megadose/holehe (email enum)"),
        ("Maigret", f"https://github.com/soxoj/maigret"),
    ]
    
    for tool_name, url in tools:
        tools_table.add_row(tool_name, Text(url, style=f"underline link {url}"))
    
    console.print(tools_table)
    console.print()

def render_search_dorks(username: str, fields: Dict[str, Any]):
    console.rule("🔎 Advanced Search Dorks", style="cyan")
    
    dorks = []
    name = fields.get("name", "")
    
    # Google Dorks
    dorks.append(("Google", f'site:instagram.com "@{username}"', "Posts mentioning user"))
    dorks.append(("Google", f'"@{username}" -site:instagram.com', "External mentions"))
    dorks.append(("Google", f'"{username}" AND (email OR gmail OR outlook OR yahoo)', "Email associations"))
    dorks.append(("Google", f'site:pastebin.com "{username}"', "Data leaks"))
    dorks.append(("Google", f'site:linkedin.com "{name if name else username}"', "Professional profiles"))
    dorks.append(("Google", f'intext:"@{username}" site:linktr.ee OR site:beacons.ai OR site:carrd.co', "Link aggregators"))
    dorks.append(("Google", f'"{username}" filetype:pdf OR filetype:doc OR filetype:xls', "Documents"))
    dorks.append(("Google", f'site:github.com "{username}"', "Code repositories"))
    dorks.append(("Google", f'site:reddit.com "{username}" OR "@{username}"', "Reddit mentions"))
    dorks.append(("Google", f'site:twitter.com "@{username}" OR "{username}"', "Twitter/X mentions"))
    
    # Bing Dorks
    dorks.append(("Bing", f'site:instagram.com "collab" "@{username}"', "Collaborations"))
    dorks.append(("Bing", f'"{username}" AND (discord OR telegram)', "Communities"))
    
    # DuckDuckGo
    if name:
        dorks.append(("DuckDuckGo", f'"{name}" ("{username}" OR instagram)', "Name associations"))
    
    # Yandex
    dorks.append(("Yandex", f'site:instagram.com "{username}"', "Russian index"))
    dorks.append(("Yandex", f'"{username}" host:vk.com OR host:ok.ru', "Russian socials"))
    
    t = make_kv_table()
    for eng, q, desc in dorks:
        url = search_url(eng.lower(), q)
        search_link = Text.from_markup(f"[link={url}]🔗 Search[/link]")
        query_text = Text(f" — {q}", style="cyan")
        desc_text = Text(f" ({desc})", style="dim")
        combined = Text().join([search_link, query_text, desc_text])
        t.add_row(eng, combined)
    
    console.print(t)
    console.print()

def render_error_with_advice(shell: Dict[str, Any]):
    console.print(f"[bold red]❌ Error:[/bold red] {shell.get('note') or 'Unable to retrieve profile.'}")
    raw_err = shell.get("raw_error")
    if raw_err:
        tips = advice_from_error(raw_err.get("status"), raw_err.get("body"))
        if tips:
            console.print()
            console.rule("💡 Advice", style="yellow")
            for t in tips:
                console.print(f"  {t}")
            console.print()