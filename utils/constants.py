#!/usr/bin/env python3

import random
from typing import List, Dict

# constants used throughout

# API Configuration
WEB_APP_ID = "936619743392459"
MOBILE_APP_ID = "124024574287414"

# User Agent Pool for rotation
USER_AGENTS = {
    "mobile": [
        # Instagram Android App versions
        "Instagram 279.0.0.20.112 Android (30/11; 420dpi; 1080x1920; Google; Pixel 4; flame; qcom; en_US; 123456789)",
        "Instagram 280.0.0.18.120 Android (31/12; 480dpi; 1080x2340; Samsung; SM-G991B; o1s; exynos2100; en_GB; 987654321)",
        "Instagram 278.0.0.21.117 Android (29/10; 440dpi; 1440x3040; OnePlus; GM1913; OnePlus7Pro; qcom; en_US; 456789123)",
        "Instagram 281.0.0.14.109 Android (32/12; 420dpi; 1080x2280; Xiaomi; Mi 11; venus; qcom; en_US; 789456123)",
        "Instagram 277.0.0.22.118 Android (30/11; 400dpi; 1080x2160; Google; Pixel 5; redfin; qcom; en_US; 321654987)",
    ],
    "web": [
        # Desktop browsers
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ],
    "tablet": [
        # iPad/Tablet browsers
        "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 16_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    ]
}

# accept-Language variations
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-US,en;q=0.8,es;q=0.6",
    "en-CA,en;q=0.9,fr;q=0.7",
    "en-AU,en;q=0.9",
    "en-US,en;q=0.9,de;q=0.8",
    "en-US,en;q=0.9,fr;q=0.8,de;q=0.7",
]

# accept headers variations
ACCEPT_HEADERS = [
    "application/json, text/plain, */*",
    "application/json",
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "*/*",
]

# sec-Fetch headers for more authenticity
SEC_FETCH_VARIANTS = [
    {
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    },
    {
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    },
    {
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none"
    }
]

# URL patterns
LYNX_HOSTS = {"l.instagram.com", "lm.instagram.com"}

# docial media host mapping
SOCIAL_HOSTS = {
    "instagram.com": "instagram",
    "twitter.com": "twitter", "x.com": "twitter",
    "facebook.com": "facebook", "fb.com": "facebook",
    "threads.net": "threads",
    "t.me": "telegram", "telegram.me": "telegram",
    "youtube.com": "youtube", "youtu.be": "youtube",
    "linkedin.com": "linkedin",
    "github.com": "github",
    "linktr.ee": "linktree", "beacons.ai": "beacons", "carrd.co": "carrd",
    "discord.gg": "discord", "discord.com": "discord",
    "bsky.app": "bluesky", "bsky.social": "bluesky",
    "mastodon.social": "mastodon",
    "onlyfans.com": "onlyfans", "patreon.com": "patreon", "substack.com": "substack",
    "tiktok.com": "tiktok", "snapchat.com": "snapchat",
    "pinterest.com": "pinterest", "twitch.tv": "twitch",
    "reddit.com": "reddit", "tumblr.com": "tumblr",
    "spotify.com": "spotify", "soundcloud.com": "soundcloud", "bandcamp.com": "bandcamp",
    "vsco.co": "vsco", "behance.net": "behance", "deviantart.com": "deviantart",
}

# display configuration
LABEL_STYLE = "bold blue"
FIELD_WIDTH = 22
VALUE_OVERFLOW = "fold"

# more stealthy features

def get_random_mobile_ua() -> str:
    return random.choice(USER_AGENTS["mobile"])

def get_random_web_ua() -> str:
    return random.choice(USER_AGENTS["web"])

def get_random_accept_language() -> str:
    return random.choice(ACCEPT_LANGUAGES)

def get_random_accept() -> str:
    return random.choice(ACCEPT_HEADERS)

def get_random_sec_fetch_headers() -> Dict[str, str]:
    return random.choice(SEC_FETCH_VARIANTS).copy()

def build_web_headers(username: str, randomize: bool = True) -> Dict[str, str]:
    headers = {
        "User-Agent": get_random_web_ua() if randomize else USER_AGENTS["web"][0],
        "Accept": get_random_accept() if randomize else ACCEPT_HEADERS[0],
        "Accept-Language": get_random_accept_language() if randomize else ACCEPT_LANGUAGES[0],
        "X-IG-App-ID": WEB_APP_ID,
        "Referer": f"https://www.instagram.com/{username}/",
        "Cache-Control": "no-cache",
        "DNT": "1",
    }
    
    if randomize and random.random() > 0.5:
        headers.update(get_random_sec_fetch_headers())

    if randomize:
        if random.random() > 0.7:
            headers["X-Requested-With"] = "XMLHttpRequest"
        if random.random() > 0.6:
            headers["Accept-Encoding"] = "gzip, deflate, br"
        if random.random() > 0.8:
            headers["Pragma"] = "no-cache"
    
    return headers

def build_mobile_headers(randomize: bool = True) -> Dict[str, str]:
    headers = {
        "User-Agent": get_random_mobile_ua() if randomize else USER_AGENTS["mobile"][0],
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-IG-App-ID": MOBILE_APP_ID,
        "Accept-Language": get_random_accept_language() if randomize else "en-US",
    }
    
    if randomize:
        if random.random() > 0.5:
            headers["X-IG-Device-ID"] = f"android-{random.randint(10000000000000000, 99999999999999999):x}"
        if random.random() > 0.6:
            headers["X-IG-Android-ID"] = f"android-{random.randint(10000000000000000, 99999999999999999):x}"
    
    return headers