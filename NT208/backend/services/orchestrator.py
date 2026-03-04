"""
Orchestrator — Bộ não điều phối
Đây là phần cốt lõi, lấy cảm hứng từ kiến trúc Agent Orchestrator của CLARA.

Pipeline đơn giản hóa từ CLARA (14 bước → 5 bước):
1. Nhận câu hỏi
2. Phân tích intent + entities (GPT-5.2) — tương tự CLARA SINGLE EXTRACTOR
3. Gọi API phù hợp song song — tương tự CLARA KNOWLEDGE RETRIEVAL
   → PubMed, ICD-11, RxNorm, ClinicalTrials.gov, OpenFDA
4. Tổng hợp + trích dẫn (GPT-5.2) — tương tự CLARA LLM SUMMARIZER
5. Trả response có cấu trúc
"""
import asyncio
from typing import Dict, List, Optional
from services import (
    pubmed_service, icd_service, rxnorm_service,
    clinicaltrials_service, openfda_service,
    llm_service,
)


async def process_query(
    user_query: str,
    conversation_history: Optional[List[Dict]] = None,
) -> Dict:
    """
    Xử lý câu hỏi y khoa end-to-end.

    Returns:
        {
            "answer": str (markdown),
            "citations": list,
            "disclaimer": str,
        }
    """

    # ========== BƯỚC 1: Phân tích Intent (CLARA: SINGLE EXTRACTOR) ==========
    intent = await llm_service.analyze_intent(user_query)
    print(f"[Orchestrator] Intent: {intent.get('intent')} | PubMed:{intent.get('needs_pubmed')} | RxNorm:{intent.get('needs_rxnorm')} | ICD11:{intent.get('needs_icd11')} | CT:{intent.get('needs_clinicaltrials')} | FDA:{intent.get('needs_openfda')}")
    print(f"[Orchestrator] Keywords EN: {intent.get('keywords_en')} | Entities: {intent.get('entities')}")

    # ========== BƯỚC 1.5: Đảm bảo đầy đủ nguồn theo intent ==========
    # Luôn bổ sung nguồn phù hợp dựa trên intent type, không phụ thuộc LLM
    intent_type = intent.get("intent", "general_medical")

    # Đảm bảo luôn có ít nhất 1 nguồn
    has_any = any(intent.get(k, False) for k in [
        "needs_pubmed", "needs_rxnorm", "needs_icd11",
        "needs_clinicaltrials", "needs_openfda",
    ])
    if not has_any:
        intent["needs_pubmed"] = True

    # Bổ sung nguồn theo loại câu hỏi (multi-source retrieval)
    if intent_type in ("symptom_lookup", "disease_info", "general_medical"):
        intent["needs_pubmed"] = True
        intent["needs_icd11"] = True
        intent["needs_clinicaltrials"] = True   # Thử nghiệm lâm sàng liên quan
    elif intent_type in ("drug_info", "drug_interaction", "drug_safety"):
        intent["needs_rxnorm"] = True
        intent["needs_pubmed"] = True
        intent["needs_openfda"] = True           # FDA safety data
    elif intent_type == "treatment_info":
        intent["needs_pubmed"] = True
        intent["needs_clinicaltrials"] = True
        intent["needs_openfda"] = True
    elif intent_type == "clinical_trial":
        intent["needs_clinicaltrials"] = True
        intent["needs_pubmed"] = True

    print(f"[Orchestrator] After augment → PubMed:{intent.get('needs_pubmed')} | ICD11:{intent.get('needs_icd11')} | RxNorm:{intent.get('needs_rxnorm')} | CT:{intent.get('needs_clinicaltrials')} | FDA:{intent.get('needs_openfda')}")

    # ========== BƯỚC 2: Gọi API song song (CLARA: KNOWLEDGE RETRIEVAL) ==========
    evidence = await _gather_evidence(intent)
    print(f"[Orchestrator] Evidence collected: {len(evidence)} items")

    # ========== BƯỚC 3: Tổng hợp câu trả lời (CLARA: LLM SUMMARIZER) ==========
    synthesis = await llm_service.synthesize(
        query=user_query,
        evidence=evidence,
        conversation_history=conversation_history,
    )

    # ========== BƯỚC 4: Format response ==========
    return {
        "answer": synthesis.get("summary", "Không thể xử lý câu hỏi."),
        "citations": synthesis.get("citations", []),
        "disclaimer": (
            "⚕️ Thông tin chỉ mang tính tham khảo cho học tập và nghiên cứu, "
            "không thay thế tư vấn y khoa chuyên nghiệp."
        ),
    }


async def _gather_evidence(intent: Dict) -> List[Dict]:
    """
    Gọi các API y khoa song song dựa trên intent.
    Tương tự CLARA KNOWLEDGE RETRIEVAL — Multi-Source Retrieval Engine.
    5 nguồn: PubMed, ICD-11, RxNorm, ClinicalTrials.gov, OpenFDA
    """
    tasks = []
    evidence = []

    keywords_en = intent.get("keywords_en", [])
    entities = intent.get("entities", [])

    # Dùng từng keyword riêng lẻ thay vì join tất cả
    primary_query = keywords_en[0] if keywords_en else (" ".join(entities) if entities else "")

    # ===== 1. PubMed — tìm tuần tự với delay để tránh 429 =====
    pubmed_results = []
    if intent.get("needs_pubmed", True) and keywords_en:
        for i, kw in enumerate(keywords_en[:3]):
            if i > 0:
                await asyncio.sleep(0.5)  # Rate limit: max 3 req/s without API key
            try:
                res = await pubmed_service.search_pubmed(kw, max_results=3)
                if res:
                    pubmed_results.extend(res)
            except Exception as e:
                print(f"[Orchestrator] PubMed '{kw}' error: {e}")
    elif intent.get("needs_pubmed", True) and primary_query:
        try:
            res = await pubmed_service.search_pubmed(primary_query, max_results=5)
            if res:
                pubmed_results.extend(res)
        except Exception as e:
            print(f"[Orchestrator] PubMed error: {e}")

    # Deduplicate PubMed results
    seen_ids = set()
    for item in pubmed_results:
        eid = item.get("pmid", "")
        if eid and eid not in seen_ids:
            seen_ids.add(eid)
            evidence.append(item)

    # ===== 2. RxNorm — tìm thuốc và tương tác =====
    if intent.get("needs_rxnorm", False) and entities:
        for entity in entities[:3]:
            tasks.append(("rxnorm_search", rxnorm_service.search_drug(entity)))

    # ===== 3. ICD-11 — tra mã bệnh =====
    if intent.get("needs_icd11", False):
        if keywords_en:
            for kw in keywords_en[:2]:
                tasks.append(("icd11", icd_service.search_icd(kw, max_results=5)))
        elif primary_query:
            tasks.append(("icd11", icd_service.search_icd(primary_query, max_results=5)))

    # ===== 4. ClinicalTrials.gov — thử nghiệm lâm sàng =====
    if intent.get("needs_clinicaltrials", False) and primary_query:
        tasks.append(("clinicaltrials", clinicaltrials_service.search_studies(
            primary_query, max_results=3
        )))

    # ===== 5. OpenFDA — tác dụng phụ, thu hồi, nhãn thuốc =====
    if intent.get("needs_openfda", False) and entities:
        for entity in entities[:2]:
            tasks.append(("openfda_ae", openfda_service.search_adverse_events(
                entity, max_results=3
            )))
            tasks.append(("openfda_label", openfda_service.search_drug_labels(
                entity, max_results=1
            )))

    # Chạy song song các API calls (trừ PubMed đã chạy tuần tự ở trên)
    if tasks:
        results = await asyncio.gather(
            *[task[1] for task in tasks],
            return_exceptions=True,
        )

        for (task_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                print(f"[Orchestrator] {task_name} failed: {result}")
                continue

            if task_name == "rxnorm_search" and isinstance(result, list):
                for item in result:
                    eid = item.get("rxcui", "")
                    if eid and eid not in seen_ids:
                        seen_ids.add(eid)
                        evidence.append(item)
                if intent.get("intent") == "drug_interaction":
                    rxcuis = [d.get("rxcui") for d in result if d.get("rxcui")]
                    if rxcuis:
                        interactions = await _get_interactions(rxcuis)
                        evidence.extend(interactions)
            elif task_name == "icd11" and isinstance(result, list):
                for item in result:
                    eid = item.get("code", "")
                    if eid and eid not in seen_ids:
                        seen_ids.add(eid)
                        evidence.append(item)
            elif task_name == "clinicaltrials" and isinstance(result, list):
                for item in result:
                    eid = item.get("nct_id", "")
                    if eid and eid not in seen_ids:
                        seen_ids.add(eid)
                        evidence.append(item)
            elif task_name in ("openfda_ae", "openfda_label") and isinstance(result, list):
                evidence.extend(result)

    print(f"[Orchestrator] Final evidence: {len(evidence)} items (deduplicated)")
    return evidence


async def _get_interactions(rxcuis: List[str]) -> List[Dict]:
    """Kiểm tra tương tác thuốc"""
    interactions = []

    if len(rxcuis) >= 2:
        # Kiểm tra tương tác giữa các thuốc
        multi_interactions = await rxnorm_service.check_interactions_between(rxcuis)
        for inter in multi_interactions:
            inter["source"] = "rxnorm_interaction"
            interactions.append(inter)
    elif len(rxcuis) == 1:
        # Kiểm tra tương tác của 1 thuốc
        single_interactions = await rxnorm_service.get_drug_interactions(rxcuis[0])
        for inter in single_interactions[:10]:
            inter["source"] = "rxnorm_interaction"
            interactions.append(inter)

    return interactions

