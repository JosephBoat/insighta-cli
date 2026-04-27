import os
import json
import hashlib
import base64
import secrets
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

CREDENTIALS_PATH = os.path.expanduser("~/.insighta/credentials.json")
BASE_URL = os.getenv("INSIGHTA_API_URL", "https://hng-stage1-profiles.fly.dev")


def save_credentials(data: dict):
    """Save tokens to ~/.insighta/credentials.json"""
    os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)
    with open(CREDENTIALS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def load_credentials() -> dict | None:
    """Load tokens from ~/.insighta/credentials.json"""
    if not os.path.exists(CREDENTIALS_PATH):
        return None
    with open(CREDENTIALS_PATH, "r") as f:
        return json.load(f)


def clear_credentials():
    """Delete stored credentials"""
    if os.path.exists(CREDENTIALS_PATH):
        os.remove(CREDENTIALS_PATH)


def generate_pkce() -> tuple:
    """
    Generate PKCE code_verifier and code_challenge.
    PKCE flow:
    1. Generate random code_verifier
    2. Hash it with SHA256 → code_challenge
    3. Send code_challenge to GitHub
    4. Send code_verifier when exchanging code for token
    GitHub verifies that hash(code_verifier) == code_challenge
    This proves the same client that started the flow is completing it.
    """
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return code_verifier, code_challenge


def refresh_tokens(refresh_token: str) -> dict | None:
    """Exchange refresh token for new token pair"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def get_valid_token() -> str | None:
    """
    Get a valid access token.
    Auto-refreshes if expired.
    Returns None if not logged in or refresh fails.
    """
    creds = load_credentials()
    if not creds:
        return None

    # Try current access token first
    access_token = creds.get("access_token")
    if access_token:
        # Quick check — try to use it
        response = requests.get(
            f"{BASE_URL}/auth/whoami",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return access_token

    # Access token expired — try refresh
    refresh_token = creds.get("refresh_token")
    if not refresh_token:
        return None

    new_tokens = refresh_tokens(refresh_token)
    if not new_tokens:
        return None

    # Save new tokens
    creds["access_token"] = new_tokens["access_token"]
    creds["refresh_token"] = new_tokens["refresh_token"]
    save_credentials(creds)

    return creds["access_token"]


def login():
    """
    Full PKCE OAuth login flow:
    1. Generate state + PKCE values
    2. Start local callback server
    3. Open GitHub in browser
    4. Capture callback
    5. Exchange code for tokens
    6. Save credentials
    """
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(16)

    # This will hold the result from the callback
    result = {"code": None, "error": None}
    server_ready = threading.Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            if "code" in params:
                result["code"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"""
                    <html><body style="font-family:sans-serif;text-align:center;padding:50px">
                    <h2>Login successful!</h2>
                    <p>You can close this tab and return to the terminal.</p>
                    </body></html>
                """
                )
            else:
                result["error"] = params.get("error", ["Unknown error"])[0]
                self.send_response(400)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress server logs

    # Find available port
    server = HTTPServer(("localhost", 0), CallbackHandler)
    port = server.server_address[1]

    # Build GitHub OAuth URL
    github_url = (
        f"{BASE_URL}/auth/github"
        f"?state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )

    # Update redirect URI to use our local port
    # We pass cli=true so backend returns JSON instead of redirecting
    callback_url = f"http://localhost:{port}/callback"

    github_direct_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id=Ov23liPQCc0deMpLAqIc"
        f"&redirect_uri={BASE_URL}/auth/github/callback?cli=true"
        f"&scope=user:email"
        f"&state={state}"
    )

    print(f"Opening GitHub login in your browser...")
    webbrowser.open(github_direct_url)

    # Wait for callback in background thread
    def serve():
        server.handle_request()

    thread = threading.Thread(target=serve)
    thread.start()
    thread.join(timeout=120)  # Wait max 2 minutes

    if result["error"]:
        print(f'Login failed: {result["error"]}')
        return False

    if not result["code"]:
        # CLI redirect approach — get token from backend directly
        pass

    return True


def logout(refresh_token: str) -> bool:
    """Call backend logout endpoint to invalidate refresh token"""
    try:
        requests.post(
            f"{BASE_URL}/auth/logout",
            json={"refresh_token": refresh_token},
            timeout=10,
        )
        return True
    except Exception:
        return False
