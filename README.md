# Insighta Labs — CLI

A globally installable command-line tool for the Insighta Labs platform.

## Installation

```bash
pip install -e .
```

After installation, `insighta` is available from any directory.

## Authentication

Credentials are stored at `~/.insighta/credentials.json`.
Tokens are auto-refreshed when expired.

## Commands

### Auth
```bash
insighta login        # Login with GitHub OAuth
insighta logout       # Logout and clear credentials
insighta whoami       # Show current user info
```

### Profiles
```bash
# List profiles
insighta profiles list
insighta profiles list --gender male
insighta profiles list --country NG --age-group adult
insighta profiles list --min-age 25 --max-age 40
insighta profiles list --sort-by age --order desc
insighta profiles list --page 2 --limit 20

# Get single profile
insighta profiles get <id>

# Natural language search
insighta profiles search "young males from nigeria"
insighta profiles search "female adults from kenya"

# Create profile (admin only)
insighta profiles create --name "Harriet Tubman"

# Export to CSV
insighta profiles export --format csv
insighta profiles export --format csv --gender male --country NG
```

## Login Flow

1. Run `insighta login`
2. Visit the URL shown in terminal
3. Authorize with GitHub
4. Copy access token and refresh token from the redirect URL
5. Paste them when prompted

## Token Handling

- Access tokens expire in 3 minutes
- Refresh tokens expire in 5 minutes  
- CLI auto-refreshes tokens on every request
- If refresh fails, re-run `insighta login`

## Credentials File

Stored at `~/.insighta/credentials.json`:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "username": "JosephBoat",
  "role": "admin"
}
```