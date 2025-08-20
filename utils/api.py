#!/usr/bin/env python3

import json
import urllib.parse
import requests
from typing import Dict, Any, Optional
from rich.console import Console

from .constants import build_web_headers, build_mobile_headers
from .helpers import try_parse_json_text, add_request_jitter

console = Console()

def web_profile_info(session: requests.Session, username: str, use_stealth: bool = True) -> Optional[Dict[str, Any]]:
    # Fetch profile info from web API 
    if use_stealth:
        add_request_jitter(0.3, 1.5) 
    
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={requests.utils.quote(username)}"
    
    headers = build_web_headers(username, randomize=use_stealth)
    
    r = session.get(
        url,
        headers=headers,
        allow_redirects=False,
        timeout=10,
    )
    
    if r.status_code == 404:
        return {"__not_found__": True}
    
    if not r.ok or r.status_code in {301, 302, 303, 307, 308}:
        return {"__error__": {"status": r.status_code, "body": r.text[:1000]}}
    
    try:
        content_type = (r.headers.get("content-type") or "").lower()
        data = r.json() if "json" in content_type else try_parse_json_text(r.text)
        return data
    except Exception:
        return {"__error__": {"status": r.status_code, "body": "parse_error"}}

def mobile_lookup(session: requests.Session, username: str, use_stealth: bool = True) -> Optional[Dict[str, Any]]:
    # perform mobile API lookup 
    if use_stealth:
        add_request_jitter(0.5, 2.0)  
    
    body = json.dumps({"q": username, "skip_recovery": "1"}, separators=(",", ":"))
    payload = f"signed_body=SIGNATURE.{urllib.parse.quote(body)}"
    
    headers = build_mobile_headers(randomize=use_stealth)
    
    r = session.post(
        "https://i.instagram.com/api/v1/users/lookup/",
        headers=headers,
        data=payload,
        timeout=10,
    )
    
    if not r.ok:
        return {"__error__": {"status": r.status_code, "body": r.text[:1000]}}
    
    try:
        data = r.json()
        return data
    except Exception:
        return {"__error__": {"status": r.status_code, "body": "parse_error"}}

def download_pfp(session: requests.Session, url: str, username: str, use_stealth: bool = True):
    # download profile picture 
    if use_stealth:
        add_request_jitter(0.2, 1.0)
    
    try:
        headers = {"User-Agent": build_web_headers(username, randomize=use_stealth)["User-Agent"]}
        r = session.get(url, headers=headers, stream=True, timeout=15)
        
        if r.ok:
            filename = f"{username}_pfp.jpg"
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            console.print(f"✅ Saved profile picture to [bold]{filename}[/bold]")
        else:
            console.print(f"❌ Failed to download profile picture. Status: {r.status_code}")
    except Exception as e:
        console.print(f"❌ Error downloading profile picture: {e}")

def fetch_profile_shell(session: requests.Session, username: str, use_stealth: bool = True) -> Dict[str, Any]:
    # fetch profile data shell
    raw = web_profile_info(session, username, use_stealth)
    
    if raw == {"__not_found__": True}:
        return {"found": False, "user": None, "note": "Not found"}
    
    if not isinstance(raw, dict) or not raw:
        return {"found": False, "user": None, "note": "Blocked or unexpected response"}
    
    if "__error__" in raw:
        return {
            "found": False, 
            "user": None, 
            "note": f"HTTP {raw['__error__'].get('status')}: web_profile_info error", 
            "raw_error": raw["__error__"]
        }
    
    user = (
        (raw.get("data") or {}).get("user")
        or (raw.get("graphql") or {}).get("user")
        or raw.get("user")
    )
    
    if not isinstance(user, dict):
        return {"found": False, "user": None, "note": "No user object"}
    
    # store raw response for debug mode
    return {"found": True, "user": user, "note": None, "_raw_response": raw}