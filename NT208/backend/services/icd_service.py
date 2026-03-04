"""
WHO ICD-11 Service
Tra cứu mã bệnh ICD-11 từ WHO API.
Reference: CLARA Section 5 — Data Sources (WHO ICD-11)
API Docs: https://icd.who.int/docs/icd-api/APIDoc-Version2/

Cần đăng ký miễn phí tại: https://icd.who.int/icdapi
Nếu chưa có key, sẽ fallback sang search endpoint không cần auth.
"""
import httpx
from typing import List, Dict, Optional
from config import get_settings

settings = get_settings()

TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"
API_BASE = "https://id.who.int/icd"

# Cache token
_token_cache = {"token": None, "expires_at": 0}


async def _get_token() -> Optional[str]:
    """Lấy OAuth2 token từ WHO"""
    if not settings.icd_client_id or not settings.icd_client_secret:
        return None

    import time
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "client_id": settings.icd_client_id,
                    "client_secret": settings.icd_client_secret,
                    "scope": "icdapi_access",
                    "grant_type": "client_credentials",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()
            _token_cache["token"] = data["access_token"]
            _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600) - 60
            return _token_cache["token"]
    except Exception as e:
        print(f"[ICD-11] Token error: {e}")
        return None


async def search_icd(query: str, max_results: int = 10) -> List[Dict]:
    """
    Tìm kiếm mã ICD-11 theo từ khóa.
    Thử dùng WHO API trước, fallback sang linearization search.
    """
    token = await _get_token()

    if token:
        return await _search_with_auth(query, token, max_results)
    else:
        return await _search_without_auth(query, max_results)


async def _search_with_auth(query: str, token: str, max_results: int) -> List[Dict]:
    """Tìm kiếm ICD-11 với OAuth2 token"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{API_BASE}/release/11/2024-01/mms/search",
                params={
                    "q": query,
                    "subtreeFilterUsesFoundationDescendants": "false",
                    "includeKeywordResult": "true",
                    "useFlexisearch": "true",
                    "flatResults": "true",
                    "highlightingEnabled": "false",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                    "Accept-Language": "en",
                    "API-Version": "v2",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for entity in data.get("destinationEntities", [])[:max_results]:
                code = entity.get("theCode", "")
                title = entity.get("title", "")
                # Remove HTML tags from title
                import re
                title = re.sub(r"<[^>]+>", "", title)

                results.append({
                    "source": "icd11",
                    "code": code,
                    "title": title,
                    "definition": entity.get("definition", ""),
                    "url": f"https://icd.who.int/browse/2024-01/mms/en#/{code}",
                })
            return results
    except Exception as e:
        print(f"[ICD-11] Auth search error: {e}")
        return await _search_without_auth(query, max_results)


async def _search_without_auth(query: str, max_results: int) -> List[Dict]:
    """
    Fallback: Tìm ICD-11 qua developer test endpoint (không cần auth).
    https://icd11restapi-developer-test.azurewebsites.net
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(
                "https://icd11restapi-developer-test.azurewebsites.net/icd/release/11/2024-01/mms/search",
                params={
                    "q": query,
                    "useFlexisearch": "true",
                    "flatResults": "true",
                },
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en",
                    "API-Version": "v2",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for entity in data.get("destinationEntities", [])[:max_results]:
                code = entity.get("theCode", "")
                title = entity.get("title", "")
                import re
                title = re.sub(r"<[^>]+>", "", str(title))

                results.append({
                    "source": "icd11",
                    "code": code,
                    "title": title,
                    "definition": entity.get("definition", ""),
                    "url": f"https://icd.who.int/browse/2024-01/mms/en#/{code}" if code else "",
                })
            return results
    except Exception as e:
        print(f"[ICD-11] Fallback search error: {e}")
        return []


async def get_icd_details(code: str) -> Optional[Dict]:
    """Lấy chi tiết một mã ICD-11"""
    token = await _get_token()

    if token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{API_BASE}/release/11/2024-01/mms/codeinfo/{code}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                        "Accept-Language": "en",
                        "API-Version": "v2",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                import re
                title = re.sub(r"<[^>]+>", "", data.get("title", {}).get("@value", ""))

                return {
                    "source": "icd11",
                    "code": code,
                    "title": title,
                    "definition": data.get("definition", {}).get("@value", ""),
                    "url": f"https://icd.who.int/browse/2024-01/mms/en#/{code}",
                }
        except Exception as e:
            print(f"[ICD-11] Details error: {e}")

    # Fallback: use developer test endpoint (codeinfo → stemId → entity)
    return await _get_details_without_auth(code)



TEST_BASE = "https://icd11restapi-developer-test.azurewebsites.net"


async def _get_details_without_auth(code: str) -> Optional[Dict]:
    """
    Fallback: Lấy chi tiết ICD-11 từ developer test endpoint.
    Flow: codeinfo/{code} → stemId → replace domain → get entity details.
    """
    import re
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Step 1: Get codeinfo to find stemId
            resp = await client.get(
                f"{TEST_BASE}/icd/release/11/2024-01/mms/codeinfo/{code}",
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en",
                    "API-Version": "v2",
                },
            )
            resp.raise_for_status()
            codeinfo = resp.json()
            stem_id = codeinfo.get("stemId", "")

            if not stem_id:
                return {
                    "source": "icd11",
                    "code": code,
                    "title": f"ICD-11 Code: {code}",
                    "definition": "",
                    "url": f"https://icd.who.int/browse/2024-01/mms/en#/{code}",
                }

            # Step 2: Replace official domain with test domain
            test_url = stem_id.replace("http://id.who.int", TEST_BASE)

            resp2 = await client.get(
                test_url,
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en",
                    "API-Version": "v2",
                },
            )
            resp2.raise_for_status()
            data = resp2.json()

            title = data.get("title", {})
            definition = data.get("definition", {})
            if isinstance(title, dict):
                title = title.get("@value", "")
            if isinstance(definition, dict):
                definition = definition.get("@value", "")
            title = re.sub(r"<[^>]+>", "", str(title))

            return {
                "source": "icd11",
                "code": code,
                "title": title,
                "definition": definition or "",
                "url": f"https://icd.who.int/browse/2024-01/mms/en#/{code}",
            }
    except Exception as e:
        print(f"[ICD-11] Fallback details error: {e}")
        return None