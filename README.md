```
██████╗ ██╗ ██████╗   
██╔══██╗██║██╔════╝   
██║  ██║██║██║  ███╗  
██║  ██║██║██║   ██║  
██████╔╝██║╚██████╔╝  
╚═════╝ ╚═╝ ╚═════╝   
```

Instagram Intelligence Gathering Tool

## Technical Overview

dIG is an advanced OSINT tool that leverages Instagram's unauthenticated API endpoints to extract comprehensive profile intelligence. Unlike traditional scrapers, dIG combines multiple API vectors and correlation techniques to maximize data extraction, particularly from private accounts where traditional methods fail.

## Quick Start Guide

```
# Clone and install
git clone https://github.com/notalex-sh/dIG.git
cd dig
pip install requests rich

# Basic recon (finds email/phone)
python dig.py johndoe

# Full intelligence gathering
python dig.py johndoe --osint --download-pfp

# Export for analysis
python dig.py johndoe --json > target_intel.json
```

## Core Capabilities

### Primary Intelligence Gathering
- **Email Discovery**: Extracts obfuscated email addresses from recovery endpoints
- **Phone Intelligence**: Identifies obfuscated phone numbers and carrier validation status
- **Account Correlation**: Links secondary Instagram accounts and cross-platform profiles
- **Collaboration Network Mapping**: Discovers hidden connections through post collaborations
- **Recovery Vector Analysis**: Determines available account recovery methods (Email/SMS/WhatsApp)

### Private Accounts?
This tool was primarily created to gather slightly more info from the closed sources that are private accounts. The obfuscated info and collaboration posts can help decipher more information about your target, while remaining anonymous

## Technical Architecture

### API Endpoint Strategy

The tool employs a dual-endpoint approach, combining web and mobile API vectors:

#### 1. Web Profile API (`/api/v1/users/web_profile_info/`)
```python
Endpoint: https://www.instagram.com/api/v1/users/web_profile_info/
Method: GET
Headers: X-IG-App-ID: 936619743392459
Returns: Complete user object including collaboration data
```

This endpoint provides:
- Full profile metadata (bio, links, verification status)
- Business contact information
- **Critical**: First page of posts with collaboration data (even for private accounts)
- Profile picture URLs in HD quality
- Connected Facebook profile biolinks

#### 2. Mobile Recovery API (`/api/v1/users/lookup/`)
```python
Endpoint: https://i.instagram.com/api/v1/users/lookup/
Method: POST
Payload: signed_body=SIGNATURE.{url_encoded_json}
Headers: X-IG-App-ID: 124024574287414
Returns: Recovery information and validation flags
```

This endpoint exposes:
- Obfuscated email addresses (`n***@g****.com`)
- Obfuscated phone numbers (`+1 *** *** **89`)
- Recovery method availability flags
- Phone number validation status
- WhatsApp registration status

### Data Correlation Engine

The tool performs multi-stage correlation:

1. **URL Unwrapping**: Instagram wraps external URLs through `l.instagram.com` for tracking. The tool unwraps these to reveal true destinations.

2. **Social Platform Detection**: Analyzes bio links and external URLs against a database of 30+ social platforms to identify cross-platform presence.

3. **Collaboration Graph Analysis**: For private accounts, analyzes the `coauthor_producers` edges in post nodes to map collaboration networks, revealing connections and posts that would otherwise be hidden.

4. **Entity Extraction**: Parses `biography_with_entities` to extract:
   - Mentioned usernames (potential alt accounts or associates)
   - Hashtags (interests/affiliations)
   - Embedded URLs (often missed by basic scrapers)

## Stealth & Evasion Techniques

### Request Fingerprint Randomization

The tool implements sophisticated anti-detection measures:

```python
# User-Agent Pool (13+ variants)
- 5 Instagram Android app versions
- 6 Desktop browser combinations  
- 2 Tablet configurations

# Header Randomization
- Accept-Language rotation (7 variants)
- Accept header variations (4 types)
- Sec-Fetch-* headers (3 configurations)
- Optional headers randomly included/excluded
```

### Timing Evasion

```python
# Request Jitter
- Random delays: 0.3-2.0 seconds between requests
- Exponential backoff on rate limits
- Human-like request patterns
```

### Session Management

- Persistent session with connection pooling
- Cookie jar maintenance
- Automatic retry with backoff

## Data Extraction Methodology

### Private Account Intelligence

Private accounts expose unique data through several vectors:

1. **Collaboration Posts**: Even with private posts, the first page of the media edge includes collaboration metadata, revealing:
   - Co-authors (linked accounts)
   - Post IDs (for correlation)
   - Collaboration patterns

2. **Recovery Information**: Private accounts often have stricter security, leading to more recovery options being configured and thus exposed.

3. **Business Conversion Artifacts**: Many private accounts were previously business accounts, leaving residual business metadata.

### Information Hierarchy

```
Level 1 - Always Available:
├── Username, Name, Bio
├── Follower/Following counts
├── Profile picture (HD)
└── Account type (private/public)

Level 2 - Usually Available:
├── Obfuscated email
├── Obfuscated phone
├── External website
├── Bio entity mentions
└── Verification status

Level 3 - Sometimes Available:
├── Business email (if business account)
├── Collaboration network (private accounts)
├── Secondary Instagram accounts
├── Cross-platform profiles
└── Facebook profile biolink

Level 4 - Rarely Available:
├── Full email (business accounts)
├── Full phone (business accounts)
└── Physical address (business)
└── WhatsApp availability
```

## Advanced Usage

### Command-Line Interface

```bash
# Basic reconnaissance
python dig.py johndoe

# Full intelligence gathering with OSINT next step suggestions
python dig.py johndoe --osint

# Debug mode - see raw API responses
python dig.py johndoe --debug

# Download profile picture in HD
python dig.py johndoe --download-pfp

# JSON output for integration
python dig.py johndoe --json > target.json

# Disable stealth (for testing, not recommended)
python dig.py johndoe --no-stealth
```

### Debug Mode Analysis

Debug mode (`--debug`) reveals:
- Raw API responses for manual analysis
- Discovered collaboration posts with full metadata
- Failed endpoints and retry attempts
- Rate limit responses

### Integration Examples (JSON output)

```python
# Programmatic usage
import subprocess
import json

def get_instagram_intel(username):
    result = subprocess.run(
        ['python', 'dig.py', username, '--json'],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Process multiple targets
targets = ['user1', 'user2', 'user3']
for target in targets:
    data = get_instagram_intel(target)
    if data['found']:
        print(f"{target}: {data['recovery']['obfuscated_email']}")
```

## Limitations & Considerations

### Technical Limitations

1. **Rate Limiting**: Instagram implements aggressive rate limiting
2. **API Changes**: Endpoints may change without notice
3. **Obfuscation**: Email/phone are partially hidden
4. **Pagination**: Only first page of posts accessible

### Legal Considerations

- This tool accesses publicly available API endpoints
- No authentication bypass or exploitation occurs
- Users are responsible for compliance with applicable laws
- Respect privacy and terms of service

## Privacy & Operational Security

### For Researchers

1. **IP Rotation**: Use residential proxies or VPN services
2. **Request Spacing**: Add delays between multiple targets
3. **Session Isolation**: Don't reuse sessions across investigations
4. **Data Minimization**: Only collect necessary information

### For Targets

Understanding these techniques helps protect your information:

1. **Disable Account Recovery**: Remove email/phone from Instagram
2. **Avoid Collaborations**: These expose your account even when private
3. **Minimize Bio Links**: Each link is a correlation point
4. **Use Unique Usernames**: Avoid reusing usernames across platforms

## OSINT Correlation Techniques

The tool provides search dorks for extended reconnaissance:

### Email Discovery Patterns
```
"{username}" AND (gmail OR outlook OR yahoo OR proton)
site:pastebin.com "{username}" email
```

### Data Breach Correlation
```
site:dehashed.com "{username}"
site:haveibeenpwned.com "{obfuscated_email_pattern}"
```

### Social Media Expansion
```
site:twitter.com "@{username}" OR "{real_name}"
site:linkedin.com "{real_name}" {location_hints}
```

## Next Steps

- Ill add these once i figure it out

---

**Disclaimer**: This tool is for educational and authorized security research only. Users are responsible for ensuring their use complies with applicable laws and terms of service.
