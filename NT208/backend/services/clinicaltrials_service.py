"""
ClinicalTrials.gov API v2 Service
Tìm kiếm thử nghiệm lâm sàng — theo kiến trúc CLARA KNOWLEDGE RETRIEVAL.

CLARA yêu cầu: "ClinicalTrials.gov API v2: Tìm kiếm và lấy thông tin chi tiết
về các thử nghiệm lâm sàng, bao gồm tình trạng, thiết kế, và kết quả."

API Docs: https://clinicaltrials.gov/data-api/api
Base URL: https://clinicaltrials.gov/api/v2
Free, no API key required.
"""
import httpx
from typing import List, Dict, Optional

BASE_URL = "https://clinicaltrials.gov/api/v2"

_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=15.0)
    return _http_client


async def search_studies(
    query: str,
    max_results: int = 5,
    condition: str = None,
    intervention: str = None,
) -> List[Dict]:
    """
    Tìm kiếm thử nghiệm lâm sàng trên ClinicalTrials.gov.

    Args:
        query: Từ khóa tìm kiếm chung
        max_results: Số kết quả tối đa
        condition: Tên bệnh/tình trạng (optional)
        intervention: Tên thuốc/can thiệp (optional)

    Returns:
        List[Dict] với mỗi item gồm:
            source, nct_id, title, status, conditions, interventions, phases,
            start_date, enrollment, summary, url
    """
    try:
        client = _get_client()
        params = {
            "pageSize": min(max_results, 10),
            "format": "json",
        }

        # Build query params
        if condition:
            params["query.cond"] = condition
        if intervention:
            params["query.intr"] = intervention
        if query and not condition and not intervention:
            params["query.cond"] = query

        resp = await client.get(f"{BASE_URL}/studies", params=params)
        if resp.status_code != 200:
            print(f"[ClinicalTrials] Error: {resp.status_code} {resp.text[:200]}")
            return []

        data = resp.json()
        studies = data.get("studies", [])
        results = []

        for study in studies[:max_results]:
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            desc = proto.get("descriptionModule", {})
            cond_mod = proto.get("conditionsModule", {})
            arms_mod = proto.get("armsInterventionsModule", {})
            eligibility = proto.get("eligibilityModule", {})

            nct_id = ident.get("nctId", "")
            conditions = cond_mod.get("conditions", [])
            interventions_raw = arms_mod.get("interventions", [])
            intervention_names = [
                i.get("name", "") for i in interventions_raw if i.get("name")
            ]
            phases = design.get("phases", [])

            results.append({
                "source": "clinicaltrials",
                "nct_id": nct_id,
                "title": ident.get("briefTitle", ""),
                "status": status_mod.get("overallStatus", ""),
                "conditions": conditions[:5],
                "interventions": intervention_names[:5],
                "phases": phases,
                "start_date": status_mod.get("startDateStruct", {}).get("date", ""),
                "enrollment": design.get("enrollmentInfo", {}).get("count", ""),
                "summary": str(desc.get("briefSummary", ""))[:500],
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
            })

        print(f"[ClinicalTrials] Found {len(results)} studies for '{query}'")
        return results

    except Exception as e:
        print(f"[ClinicalTrials] Error: {e}")
        return []


async def get_study_detail(nct_id: str) -> Optional[Dict]:
    """Lấy chi tiết 1 thử nghiệm theo NCT ID."""
    try:
        client = _get_client()
        resp = await client.get(f"{BASE_URL}/studies/{nct_id}", params={"format": "json"})
        if resp.status_code != 200:
            return None

        study = resp.json()
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        desc = proto.get("descriptionModule", {})
        cond_mod = proto.get("conditionsModule", {})
        arms_mod = proto.get("armsInterventionsModule", {})
        design = proto.get("designModule", {})
        outcomes = proto.get("outcomesModule", {})

        primary_outcomes = [
            o.get("measure", "") for o in outcomes.get("primaryOutcomes", [])
        ]

        return {
            "source": "clinicaltrials",
            "nct_id": ident.get("nctId", nct_id),
            "title": ident.get("briefTitle", ""),
            "official_title": ident.get("officialTitle", ""),
            "status": status_mod.get("overallStatus", ""),
            "conditions": cond_mod.get("conditions", []),
            "summary": desc.get("briefSummary", ""),
            "detailed_description": str(desc.get("detailedDescription", ""))[:1000],
            "phases": design.get("phases", []),
            "study_type": design.get("studyType", ""),
            "primary_outcomes": primary_outcomes[:5],
            "url": f"https://clinicaltrials.gov/study/{nct_id}",
        }
    except Exception as e:
        print(f"[ClinicalTrials] Detail error for {nct_id}: {e}")
        return None

