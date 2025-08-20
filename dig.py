#!/usr/bin/env python3

"""
    ██████╗ ██╗ ██████╗       
    ██╔══██╗██║██╔════╝       
    ██║  ██║██║██╗  ███╗      
    ██║  ██║██║██║   ██║      
    ██████╔╝██║╚██████╔╝      
    ╚═════╝ ╚═╝ ╚═════╝       

dIG - Instagram Email Intelligence Tool
Unauthenticated OSINT Tool for Instagram Profile Analysis

v1.0

By notalex.sh
"""

import argparse
import json
import requests
from typing import Dict, Any, List
from rich.console import Console

from utils.helpers import norm_handle, advice_from_error
from utils.api import fetch_profile_shell, mobile_lookup, download_pfp
from utils.extractors import (
    extract_profile_fields,
    collect_collab_posts_any_visibility,
    assemble_json_result
)
from utils.renderers import (
    render_header,
    render_profile_block,
    render_bio,
    render_contacts_and_recovery,
    render_business_block,
    render_socials_block,
    render_collabs,
    render_osint_tools,
    render_search_dorks,
    render_error_with_advice
)

console = Console()

def run(username: str, args: argparse.Namespace):
    s = requests.Session()
    s.headers.update({"Connection": "keep-alive"})
    
    use_stealth = not args.no_stealth
    
    # fetch profile data
    if not args.json:
        with console.status("[bold cyan]Fetching profile data...", spinner="dots"):
            shell = fetch_profile_shell(s, username, use_stealth)
    else:
        shell = fetch_profile_shell(s, username, use_stealth)
    
    # debug output for raw API response
    if args.debug and shell.get("_raw_response"):
        console.print("\n[bold yellow]DEBUG: Raw web_profile_info response:[/bold yellow]")
        console.print(json.dumps(shell["_raw_response"], indent=2))
        console.print()
    
    # handle not found case
    if not shell.get("found"):
        if args.json:
            result = assemble_json_result(username, shell, None, {}, [])
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return
        render_error_with_advice(shell)
        return
    
    user = shell["user"]
    
    # extract profile fields
    if not args.json:
        with console.status("[bold cyan]Extracting profile fields...", spinner="dots"):
            fields = extract_profile_fields(user)
    else:
        fields = extract_profile_fields(user)
    
    # download profile picture if requested
    if args.download_pfp and fields.get("hd_profile_pic_url_original"):
        download_pfp(s, fields["hd_profile_pic_url_original"], username, use_stealth)
    
    # perform mobile lookup
    if not args.json:
        with console.status("[bold cyan]Performing mobile lookup...", spinner="dots"):
            lookup = mobile_lookup(s, username, use_stealth) or {}
    else:
        lookup = mobile_lookup(s, username, use_stealth) or {}
    
    # debug output for mobile lookup
    if args.debug and lookup:
        console.print("[bold yellow]DEBUG: Raw mobile lookup response:[/bold yellow]")
        console.print(json.dumps(lookup, indent=2))
        console.print()
    
    # update fields with lookup data
    u = lookup.get("user") if isinstance(lookup.get("user"), dict) else {}
    fields["obfuscated_email"] = (
        lookup.get("obfuscated_email") 
        or u.get("obfuscated_email") 
        or lookup.get("email")
    )
    fields["obfuscated_phone"] = (
        lookup.get("obfuscated_phone")
        or lookup.get("obfuscated_phone_number")
        or u.get("obfuscated_phone")
        or u.get("obfuscated_phone_number")
    )
    
    # analyse collaborations - ONLY FOR PRIVATE ACCOUNTS
    collabs: List[Dict[str, Any]] = []
    if fields.get("account_status") == "private":  
        if not args.json:
            with console.status("[bold cyan]Analyzing collaborations...", spinner="dots"):
                collabs = collect_collab_posts_any_visibility(user, owner_username=fields.get("username"))
        else:
            collabs = collect_collab_posts_any_visibility(user, owner_username=fields.get("username"))
        
        if args.debug and collabs:
            console.print("[bold yellow]DEBUG: Found collaborations:[/bold yellow]")
            console.print(json.dumps(collabs, indent=2))
            console.print()
    
    if args.json:
        result = assemble_json_result(username, shell, fields, lookup, collabs)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    render_profile_block(fields)
    render_bio(fields)
    render_contacts_and_recovery(fields, lookup)
    render_business_block(fields)
    render_socials_block(fields)

    if fields.get("account_status") == "private":
        render_collabs(collabs)
    
    if args.osint:
        render_osint_tools(username, fields)
        render_search_dorks(username, fields)

def main():
    # main entry point
    parser = argparse.ArgumentParser(
        description="dIG — Instagram Email Intelligence | Unauthenticated OSINT Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s johndoe                    # Basic profile lookup
  %(prog)s johndoe --download-pfp     # Download profile picture
  %(prog)s johndoe --osint            # Include OSINT tools
  %(prog)s johndoe --json             # JSON output
  %(prog)s johndoe --debug            # Show raw API responses
  %(prog)s johndoe --no-stealth       # Disable stealth features
        """
    )
    
    parser.add_argument(
        "username", 
        help="Target Instagram username (without @)"
    )
    
    parser.add_argument(
        "--download-pfp", 
        action="store_true", 
        help="Download HD profile picture"
    )
    
    parser.add_argument(
        "--osint", 
        action="store_true", 
        help="Show OSINT tools and search dorks"
    )
    
    parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output as JSON"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Show raw API responses for debugging"
    )
    
    parser.add_argument(
        "--no-stealth", 
        action="store_true", 
        help="Disable stealth features (not recommended)"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 2.0.1"
    )
    
    args = parser.parse_args()
    
    norm_user = norm_handle(args.username)

    if not args.json:
        render_header(norm_user)
    
    try:
        run(norm_user, args)
    except KeyboardInterrupt:
        if not args.json:
            console.print("\n⚠️ Interrupted by user")
        else:
            print(json.dumps({"error": "Interrupted"}, ensure_ascii=False))
    except Exception as e:
        if args.json:
            print(json.dumps({
                "error": str(e),
                "advice": advice_from_error(None, str(e))
            }, ensure_ascii=False))
        else:
            console.print(f"[bold red]❌ Unhandled Error:[/bold red] {e}")
            console.print()
            console.rule("💡 Advice", style="yellow")
            for tip in advice_from_error(None, str(e)):
                console.print(f"  {tip}")

if __name__ == "__main__":
    main()