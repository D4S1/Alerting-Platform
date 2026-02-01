import os
import requests
import httpx

METADATA_URL = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"
META_HEADERS = {"Metadata-Flavor": "Google"}

def _is_local(url: str) -> bool:
    """
    Checks if the service is working locally.
    """
    return "localhost" in url or "127.0.0.1" in url or "0.0.0.0" in url

# --- Version for Flask ---
def get_headers(target_audience: str) -> dict:
    if _is_local(target_audience):
        return {}

    try:
        resp = requests.get(
            METADATA_URL, 
            params={"audience": target_audience}, 
            headers=META_HEADERS, 
            timeout=2
        )
        if resp.status_code == 200:
            return {"Authorization": f"Bearer {resp.text.strip()}"}
        else:
            print(f"[Auth Sync] Error: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[Auth Sync] Exception: {e}")
    
    return {}

# --- Version for Asyncio ---
async def get_headers_async(target_audience: str) -> dict:
    if _is_local(target_audience):
        return {}

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                METADATA_URL, 
                params={"audience": target_audience}, 
                headers=META_HEADERS
            )
            if resp.status_code == 200:
                return {"Authorization": f"Bearer {resp.text.strip()}"}
            else:
                print(f"[Auth Async] Error: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[Auth Async] Exception: {e}")

    return {}


# API_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# def get_google_auth_token():
#     """
#     Retrieves the OIDC token from the Metadata Server (only when running on Google Cloud Run).
#     Requires 'API_URL' to be a valid target address (audience).
#     """

#     if "localhost" in API_URL or "127.0.0.1" in API_URL:  # if working local, Google token is not needed
#         return None

#     metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"
#     params = {"audience": API_URL}
#     headers = {"Metadata-Flavor": "Google"}

#     try:
#         response = requests.get(metadata_url, params=params, headers=headers, timeout=2)
#         if response.status_code == 200:
#             return response.text.strip()
#         else:
#             print(f"Error loading token from the metadata: {response.status_code} {response.text}")
#     except Exception as e:
#         print(f"Cannot connect to Metadata Server (are you working locally?): {e}")
    
#     return None

# def get_headers():
#     """
#     Creates headers with autorization token.
#     """
#     headers = {"Content-Type": "application/json"}
    
#     token = get_google_auth_token()
#     if token:
#         headers["Authorization"] = f"Bearer {token}"
        
#     return headers