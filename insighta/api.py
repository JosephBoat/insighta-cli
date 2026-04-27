import requests
from .auth import get_valid_token, BASE_URL

HEADERS = {"X-API-Version": "1"}


def get_headers() -> dict:
    token = get_valid_token()
    if not token:
        return None
    return {**HEADERS, "Authorization": f"Bearer {token}"}


def get_profiles(params: dict) -> dict | None:
    headers = get_headers()
    if not headers:
        return None
    try:
        response = requests.get(
            f"{BASE_URL}/api/profiles",
            headers=headers,
            params=params,
            timeout=15,
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_profile(profile_id: str) -> dict | None:
    headers = get_headers()
    if not headers:
        return None
    try:
        response = requests.get(
            f"{BASE_URL}/api/profiles/{profile_id}",
            headers=headers,
            timeout=15,
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def search_profiles(query: str, params: dict) -> dict | None:
    headers = get_headers()
    if not headers:
        return None
    try:
        response = requests.get(
            f"{BASE_URL}/api/profiles/search",
            headers=headers,
            params={"q": query, **params},
            timeout=15,
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_profile(name: str) -> dict | None:
    headers = get_headers()
    if not headers:
        return None
    try:
        response = requests.post(
            f"{BASE_URL}/api/profiles",
            headers={**headers, "Content-Type": "application/json"},
            json={"name": name},
            timeout=30,
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def export_profiles(params: dict) -> requests.Response | None:
    headers = get_headers()
    if not headers:
        return None
    try:
        response = requests.get(
            f"{BASE_URL}/api/profiles/export",
            headers=headers,
            params={"format": "csv", **params},
            timeout=30,
        )
        return response
    except Exception as e:
        return None


def whoami() -> dict | None:
    headers = get_headers()
    if not headers:
        return None
    try:
        response = requests.get(
            f"{BASE_URL}/auth/whoami",
            headers=headers,
            timeout=10,
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def logout(refresh_token: str) -> bool:
    try:
        requests.post(
            f"{BASE_URL}/auth/logout",
            json={"refresh_token": refresh_token},
            timeout=10,
        )
        return True
    except Exception:
        return False
