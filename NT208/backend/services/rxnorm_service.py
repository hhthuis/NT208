"""
RxNorm Service (NLM RxNav)
Tra cứu thuốc và tương tác thuốc.
Reference: CLARA Section 5 — Data Sources (RxNorm/RxNav)
API Docs: https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html
Không cần API key.

Note: Interaction API (DrugBank via RxNorm) đã bị NLM deprecated (trả 404).
Drug search vẫn hoạt động. Interactions trả empty array là bình thường.
"""
import httpx
from typing import List, Dict

BASE_URL = "https://rxnav.nlm.nih.gov/REST"


async def search_drug(name: str) -> List[Dict]:
    """Tìm thuốc theo tên, trả về danh sách kết quả với RxCUI"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Tìm theo approximate match
            resp = await client.get(
                f"{BASE_URL}/approximateTerm.json",
                params={"term": name, "maxEntries": 10}
            )
            resp.raise_for_status()
            data = resp.json()

            candidates = data.get("approximateGroup", {}).get("candidate", [])
            drugs = []
            seen_rxcuis = set()

            for c in candidates:
                rxcui = c.get("rxcui", "")
                if rxcui and rxcui not in seen_rxcuis:
                    seen_rxcuis.add(rxcui)
                    # Lấy properties
                    drug_info = await get_drug_properties(rxcui, client)
                    if drug_info:
                        drugs.append(drug_info)
                    if len(drugs) >= 5:
                        break

            return drugs
    except Exception as e:
        print(f"[RxNorm] Search error: {e}")
        return []


async def get_drug_properties(rxcui: str, client: httpx.AsyncClient = None) -> Dict:
    """Lấy thông tin chi tiết của thuốc theo RxCUI"""
    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)
        should_close = True

    try:
        resp = await client.get(f"{BASE_URL}/rxcui/{rxcui}/properties.json")
        resp.raise_for_status()
        data = resp.json()

        props = data.get("properties", {})
        return {
            "source": "rxnorm",
            "rxcui": props.get("rxcui", rxcui),
            "name": props.get("name", ""),
            "synonym": props.get("synonym", ""),
            "tty": props.get("tty", ""),
            "url": f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={rxcui}",
        }
    except Exception:
        return {"source": "rxnorm", "rxcui": rxcui, "name": "", "synonym": "", "tty": "", "url": ""}
    finally:
        if should_close:
            await client.aclose()


async def get_drug_interactions(rxcui: str) -> List[Dict]:
    """Kiểm tra tương tác thuốc cho 1 RxCUI"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{BASE_URL}/interaction/interaction.json",
                params={"rxcui": rxcui, "sources": "DrugBank"}
            )
            resp.raise_for_status()
            data = resp.json()

            interactions = []
            interaction_groups = data.get("interactionTypeGroup", [])

            for group in interaction_groups:
                for itype in group.get("interactionType", []):
                    for pair in itype.get("interactionPair", []):
                        desc = pair.get("description", "")
                        severity = pair.get("severity", "N/A")

                        concepts = pair.get("interactionConcept", [])
                        drug_names = [
                            c.get("minConceptItem", {}).get("name", "")
                            for c in concepts
                        ]

                        interactions.append({
                            "drug1": drug_names[0] if len(drug_names) > 0 else "",
                            "drug2": drug_names[1] if len(drug_names) > 1 else "",
                            "description": desc,
                            "severity": severity,
                            "source": "DrugBank via RxNorm",
                        })

            return interactions[:20]  # Giới hạn 20 tương tác
    except Exception as e:
        print(f"[RxNorm] Interaction error: {e}")
        return []


async def check_interactions_between(rxcui_list: List[str]) -> List[Dict]:
    """Kiểm tra tương tác giữa nhiều thuốc"""
    if len(rxcui_list) < 2:
        return []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            rxcuis_str = "+".join(rxcui_list)
            resp = await client.get(
                f"{BASE_URL}/interaction/list.json",
                params={"rxcuis": rxcuis_str, "sources": "DrugBank"}
            )
            resp.raise_for_status()
            data = resp.json()

            interactions = []
            for group in data.get("fullInteractionTypeGroup", []):
                for itype in group.get("fullInteractionType", []):
                    for pair in itype.get("interactionPair", []):
                        desc = pair.get("description", "")
                        severity = pair.get("severity", "N/A")
                        concepts = pair.get("interactionConcept", [])
                        drug_names = [
                            c.get("minConceptItem", {}).get("name", "")
                            for c in concepts
                        ]
                        interactions.append({
                            "drug1": drug_names[0] if len(drug_names) > 0 else "",
                            "drug2": drug_names[1] if len(drug_names) > 1 else "",
                            "description": desc,
                            "severity": severity,
                            "source": "DrugBank via RxNorm",
                        })
            return interactions[:20]
    except Exception as e:
        print(f"[RxNorm] Multi-interaction error: {e}")
        return []

