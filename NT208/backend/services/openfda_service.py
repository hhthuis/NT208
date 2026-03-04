"""
OpenFDA API Service
Khai thác dữ liệu hậu kiểm về thuốc — theo kiến trúc CLARA KNOWLEDGE RETRIEVAL.

CLARA yêu cầu: "OpenFDA API: Khai thác dữ liệu hậu kiểm về thuốc, thiết bị y tế
và thực phẩm, bao gồm báo cáo biến cố bất lợi (adverse events) và các thông báo
thu hồi (recalls)."

API Docs: https://open.fda.gov/apis/
Base URL: https://api.fda.gov/drug/
Free, no API key required (rate limited 240 req/min without key).

Endpoints:
  - event.json: Drug adverse event reports (FAERS)
  - enforcement.json: Drug recalls/enforcement
  - label.json: Drug labeling/package inserts
"""
import httpx
from typing import List, Dict, Optional

BASE_URL = "https://api.fda.gov/drug"

_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=15.0)
    return _http_client


async def search_adverse_events(
    drug_name: str, max_results: int = 5
) -> List[Dict]:
    """
    Tìm báo cáo tác dụng phụ (adverse events) của thuốc từ FDA FAERS.
    """
    try:
        client = _get_client()
        search_q = f'patient.drug.openfda.generic_name:"{drug_name}"'
        resp = await client.get(f"{BASE_URL}/event.json", params={
            "search": search_q,
            "limit": min(max_results, 10),
        })

        if resp.status_code != 200:
            # Retry with brand_name
            search_q = f'patient.drug.openfda.brand_name:"{drug_name}"'
            resp = await client.get(f"{BASE_URL}/event.json", params={
                "search": search_q,
                "limit": min(max_results, 10),
            })
            if resp.status_code != 200:
                print(f"[OpenFDA] AE search failed: {resp.status_code}")
                return []

        data = resp.json()
        results_raw = data.get("results", [])
        results = []

        for r in results_raw[:max_results]:
            patient = r.get("patient", {})
            reactions = patient.get("reaction", [])
            drugs = patient.get("drug", [])
            reaction_names = [
                rx.get("reactionmeddrapt", "") for rx in reactions if rx.get("reactionmeddrapt")
            ]
            drug_names = [
                d.get("medicinalproduct", "") for d in drugs if d.get("medicinalproduct")
            ]

            results.append({
                "source": "openfda_ae",
                "drug_name": drug_name,
                "reactions": reaction_names[:10],
                "drugs_involved": drug_names[:5],
                "serious": r.get("serious", ""),
                "seriousness_death": r.get("seriousnessdeath", ""),
                "seriousness_hospital": r.get("seriousnesshospitalization", ""),
                "receive_date": r.get("receivedate", ""),
                "report_country": r.get("occurcountry", ""),
            })

        print(f"[OpenFDA] Found {len(results)} adverse events for '{drug_name}'")
        return results

    except Exception as e:
        print(f"[OpenFDA] AE error: {e}")
        return []


async def search_drug_recalls(
    drug_name: str, max_results: int = 3
) -> List[Dict]:
    """
    Tìm thông báo thu hồi thuốc (drug recalls/enforcement) từ FDA.
    """
    try:
        client = _get_client()
        search_q = f'openfda.generic_name:"{drug_name}"'
        resp = await client.get(f"{BASE_URL}/enforcement.json", params={
            "search": search_q,
            "limit": min(max_results, 10),
        })

        if resp.status_code != 200:
            # Try brand_name
            search_q = f'openfda.brand_name:"{drug_name}"'
            resp = await client.get(f"{BASE_URL}/enforcement.json", params={
                "search": search_q,
                "limit": min(max_results, 10),
            })
            if resp.status_code != 200:
                return []

        data = resp.json()
        results = []

        for r in data.get("results", [])[:max_results]:
            results.append({
                "source": "openfda_recall",
                "drug_name": drug_name,
                "recall_reason": r.get("reason_for_recall", ""),
                "classification": r.get("classification", ""),
                "status": r.get("status", ""),
                "recall_date": r.get("recall_initiation_date", ""),
                "city": r.get("city", ""),
                "state": r.get("state", ""),
                "country": r.get("country", ""),
                "product_description": str(r.get("product_description", ""))[:300],
            })

        print(f"[OpenFDA] Found {len(results)} recalls for '{drug_name}'")
        return results

    except Exception as e:
        print(f"[OpenFDA] Recall error: {e}")
        return []


async def search_drug_labels(
    drug_name: str, max_results: int = 2
) -> List[Dict]:
    """
    Tìm thông tin nhãn thuốc (drug labels/SPL) từ FDA.
    Bao gồm: warnings, indications, contraindications, dosage.
    """
    try:
        client = _get_client()
        search_q = f'openfda.generic_name:"{drug_name}"'
        resp = await client.get(f"{BASE_URL}/label.json", params={
            "search": search_q,
            "limit": min(max_results, 5),
        })

        if resp.status_code != 200:
            search_q = f'openfda.brand_name:"{drug_name}"'
            resp = await client.get(f"{BASE_URL}/label.json", params={
                "search": search_q,
                "limit": min(max_results, 5),
            })
            if resp.status_code != 200:
                return []

        data = resp.json()
        results = []

        for r in data.get("results", [])[:max_results]:
            openfda = r.get("openfda", {})
            generic_names = openfda.get("generic_name", [])
            brand_names = openfda.get("brand_name", [])

            results.append({
                "source": "openfda_label",
                "drug_name": drug_name,
                "generic_name": generic_names[0] if generic_names else "",
                "brand_name": brand_names[0] if brand_names else "",
                "indications": str(r.get("indications_and_usage", [""])[0])[:500],
                "warnings": str(r.get("warnings", [""])[0])[:500],
                "contraindications": str(r.get("contraindications", [""])[0])[:400],
                "dosage": str(r.get("dosage_and_administration", [""])[0])[:400],
                "adverse_reactions": str(r.get("adverse_reactions", [""])[0])[:400],
            })

        print(f"[OpenFDA] Found {len(results)} drug labels for '{drug_name}'")
        return results

    except Exception as e:
        print(f"[OpenFDA] Label error: {e}")
        return []

