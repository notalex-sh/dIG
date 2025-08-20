#!/usr/bin/env python3

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from utils.helpers import (
    extract_links_from_user_obj, 
    extract_bio_entities,
    pick_hd_profile_pic,
    clean_cdn_url,
    owner_edges,
    coauthors_from_node,
    advice_from_error
)

def extract_profile_fields(user: Dict[str, Any]) -> Dict[str, Any]:
    # extract all profile fields from user object
    websites, socials, fb_biolink_url = extract_links_from_user_obj(user)
    mentions, bio_hashtags = extract_bio_entities(user)
    
    posts = (
        user.get("edge_owner_to_timeline_media", {}).get("count") 
        or user.get("media_count") 
        or user.get("posts_count")
    )
    
    followers = (
        user.get("edge_followed_by", {}).get("count") 
        or user.get("follower_count")
    )
    
    following = (
        user.get("edge_follow", {}).get("count") 
        or user.get("following_count")
    )
    
    public_email = user.get("public_email") or user.get("email")
    public_phone = user.get("public_phone_number") or user.get("contact_phone_number")
    
    has_threads_by_link = any(s.get("service") == "threads" for s in socials)
    has_threads_by_flag = bool(
        user.get("has_onboarded_to_text_post_app") 
        or user.get("show_text_post_app_badge")
    )
    has_threads = has_threads_by_link or has_threads_by_flag
    
    original_pfp_url = pick_hd_profile_pic(user)
    
    return {
        "username": user.get("username"),
        "name": user.get("full_name") or user.get("name"),
        "bio": user.get("biography"),
        "bio_mentions": mentions,
        "bio_hashtags": bio_hashtags,
        "websites": websites,
        "linked_socials": socials,
        "fb_profile_biolink_url": fb_biolink_url,
        "has_threads": has_threads,
        "account_status": "private" if user.get("is_private") else "public" if "is_private" in user else None,
        "is_verified": bool(user.get("is_verified")) if "is_verified" in user else None,
        "is_business": bool(user.get("is_business_account")) if "is_business_account" in user else None,
        "business_contact_method": user.get("business_contact_method"),
        "business_email": user.get("business_email"),
        "business_phone_number": user.get("business_phone_number"),
        "business_address_json": user.get("business_address_json"),
        "category_name": user.get("category_name"),
        "public_email": public_email,
        "public_phone": public_phone,
        "followers": followers,
        "following": following,
        "posts": posts,
        "instagram_id": user.get("id") or user.get("pk"),
        "hd_profile_pic_url_original": original_pfp_url,
        "hd_profile_pic_url": clean_cdn_url(original_pfp_url),
    }

def collect_collab_posts_any_visibility(user: Dict[str, Any], owner_username: Optional[str]) -> List[Dict[str, Any]]:
    # collect collaboration posts from user data
    out: List[Dict[str, Any]] = []
    
    for e in owner_edges(user):
        node = e.get("node") or {}
        sc = node.get("shortcode")
        if not sc:
            continue
        
        coauthors = coauthors_from_node(node)
        if owner_username:
            coauthors = [u for u in coauthors if u.lower() != (owner_username or "").lower()]
        
        entry = {"url": f"https://www.instagram.com/p/{sc}/"}
        if coauthors:
            entry["coauthors"] = coauthors
        
        out.append(entry)
    
    return out

def assemble_json_result(username: str,
                        shell: Dict[str, Any],
                        fields: Optional[Dict[str, Any]],
                        lookup: Dict[str, Any],
                        collabs: List[Dict[str, Any]]) -> Dict[str, Any]:
    
    # assemble final JSON result
    out: Dict[str, Any] = {
        "target": username,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "found": bool(shell.get("found")),
        "note": shell.get("note"),
    }
    
    if not shell.get("found"):
        if shell.get("raw_error"):
            status = shell["raw_error"].get("status")
            body = shell["raw_error"].get("body")
            out["http_error"] = {"status": status}
            adv = advice_from_error(status, body)
            if adv:
                out["advice"] = adv
        return out
    
    out["profile"] = {
        "username": fields.get("username"),
        "name": fields.get("name"),
        "account_status": fields.get("account_status"),
        "is_verified": fields.get("is_verified"),
        "is_business": fields.get("is_business"),
        "category_name": fields.get("category_name"),
        "followers": fields.get("followers"),
        "following": fields.get("following"),
        "posts": fields.get("posts"),
        "instagram_id": fields.get("instagram_id"),
        "hd_profile_pic_url": fields.get("hd_profile_pic_url"),
        "hd_profile_pic_url_original": fields.get("hd_profile_pic_url_original"),
        "bio": fields.get("bio"),
        "bio_mentions": fields.get("bio_mentions"),
        "bio_hashtags": fields.get("bio_hashtags"),
        "websites": fields.get("websites"),
        "linked_socials": fields.get("linked_socials"),
        "fb_profile_biolink_url": fields.get("fb_profile_biolink_url"),
        "has_threads": fields.get("has_threads"),
        "public_email": fields.get("public_email"),
        "public_phone": fields.get("public_phone"),
        "business_contact_method": fields.get("business_contact_method"),
        "business_email": fields.get("business_email"),
        "business_phone_number": fields.get("business_phone_number"),
        "business_address_json": fields.get("business_address_json"),
    }
    
    u = lookup.get("user") if isinstance(lookup.get("user"), dict) else {}
    out["recovery"] = {
        "obfuscated_email": lookup.get("obfuscated_email") or u.get("obfuscated_email") or lookup.get("email"),
        "obfuscated_phone": (
            lookup.get("obfuscated_phone")
            or lookup.get("obfuscated_phone_number")
            or u.get("obfuscated_phone")
            or u.get("obfuscated_phone_number")
        ),
        "has_valid_phone": lookup.get("has_valid_phone"),
        "can_email_reset": lookup.get("can_email_reset"),
        "can_sms_reset": lookup.get("can_sms_reset"),
        "can_wa_reset": lookup.get("can_wa_reset"),
    }
    
    out["collaborations"] = collabs
    return out