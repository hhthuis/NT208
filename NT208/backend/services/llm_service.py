"""
LLM Service — OpenAI-compatible API Integration
Gọi OpenAI-compatible API (AgentRita / OpenAI / others) để phân tích intent và tổng hợp câu trả lời.
Reference: CLARA Section 6 — LLM Summarizer + Single Extractor nodes

System prompt thiết kế theo triết lý CLARA:
- Chỉ trả lời dựa trên evidence
- Bắt buộc trích dẫn nguồn
- Disclaimer y khoa
- Trả lời tiếng Việt

Note: Sử dụng httpx trực tiếp thay vì openai Python library
vì Cloudflare WAF chặn request pattern của openai library.
httpx với curl-like headers bypass được WAF.
"""
from typing import Dict, List, Optional
from config import get_settings
import httpx
import json

settings = get_settings()

# Reusable httpx client
_http_client: Optional[httpx.AsyncClient] = None


def _get_http_client() -> httpx.AsyncClient:
    """Get or create reusable httpx client with curl-like headers."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=90.0,
            verify=settings.openai_verify_ssl,
            http2=False,  # Force HTTP/1.1 — avoids Cloudflare WAF fingerprinting
        )
    return _http_client


def _get_headers() -> dict:
    """Get request headers that mimic curl to bypass Cloudflare WAF."""
    return {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/8.7.1",
        "Accept": "*/*",
    }


async def _chat_completion(messages: List[Dict], **kwargs) -> Dict:
    """
    Call OpenAI-compatible chat/completions endpoint using httpx directly.
    Returns the parsed JSON response.
    Raises Exception on failure.
    """
    client = _get_http_client()
    base_url = settings.openai_base_url.rstrip("/")
    url = f"{base_url}/chat/completions"

    payload = {
        "model": settings.openai_model,
        "messages": messages,
    }
    # Add optional parameters
    for key in ("temperature", "max_tokens", "response_format"):
        if key in kwargs and kwargs[key] is not None:
            payload[key] = kwargs[key]

    resp = await client.post(url, headers=_get_headers(), json=payload)

    if resp.status_code != 200:
        error_text = resp.text[:300]
        raise Exception(f"API returned {resp.status_code}: {error_text}")

    data = resp.json()

    # Extract message content
    content = data["choices"][0]["message"]["content"]
    return {"content": content, "raw": data}


# ==================== SYSTEM PROMPTS ====================

INTENT_SYSTEM_PROMPT = """Bạn là một hệ thống phân tích câu hỏi y khoa theo kiến trúc CLARA (Clinical Agent for Retrieval & Analysis). Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và trích xuất thông tin cần thiết để tra cứu 5 nguồn dữ liệu y khoa: PubMed, ICD-11, RxNorm, ClinicalTrials.gov, OpenFDA.

Trả về JSON với format:
{
    "intent": "drug_info" | "drug_interaction" | "disease_info" | "symptom_lookup" | "treatment_info" | "clinical_trial" | "drug_safety" | "general_medical",
    "entities": ["tên thuốc/bệnh/triệu chứng được nhắc đến"],
    "keywords_en": ["từ khóa tiếng Anh để tìm kiếm PubMed/ClinicalTrials"],
    "keywords_vi": ["từ khóa tiếng Việt"],
    "needs_pubmed": true/false,
    "needs_rxnorm": true/false,
    "needs_icd11": true/false,
    "needs_clinicaltrials": true/false,
    "needs_openfda": true/false
}

Hướng dẫn chọn nguồn:
- PubMed: Khi cần bài báo nghiên cứu, evidence-based medicine
- ICD-11: Khi cần mã bệnh, phân loại bệnh, triệu chứng
- RxNorm: Khi hỏi về thuốc cụ thể, tương tác thuốc
- ClinicalTrials.gov: Khi hỏi về thử nghiệm lâm sàng, phương pháp điều trị mới
- OpenFDA: Khi hỏi về tác dụng phụ thuốc, thu hồi thuốc, an toàn thuốc

Ví dụ:
- "Metformin có tương tác với Warfarin không?" → needs_rxnorm: true, needs_openfda: true
- "Triệu chứng của tiểu đường type 2" → needs_icd11: true, needs_pubmed: true
- "Có thử nghiệm lâm sàng nào về ung thư phổi?" → needs_clinicaltrials: true, needs_pubmed: true
- "Thuốc Paracetamol có tác dụng phụ gì?" → needs_openfda: true, needs_rxnorm: true
- "Tôi uống bia bị ngứa" → needs_pubmed: true, needs_icd11: true

CHỈ trả về JSON, không giải thích thêm."""

SYNTHESIS_SYSTEM_PROMPT = """Bạn là trợ lý tra cứu y khoa dành cho mục đích giáo dục và nghiên cứu, được phát triển dựa trên kiến trúc CLARA (Clinical Agent for Retrieval & Analysis).

HỆ THỐNG SỬ DỤNG 5 NGUỒN DỮ LIỆU Y KHOA:
1. PubMed — Bài báo nghiên cứu y sinh (36+ triệu trích dẫn)
2. WHO ICD-11 — Phân loại bệnh tật quốc tế
3. RxNorm (NIH) — Định danh thuốc chuẩn hóa
4. ClinicalTrials.gov — Thử nghiệm lâm sàng
5. OpenFDA — Dữ liệu an toàn thuốc, tác dụng phụ, thu hồi

QUY TẮC BẮT BUỘC:
1. CHỈ trả lời dựa trên dữ liệu trong phần [EVIDENCE]. KHÔNG bịa thêm thông tin.
2. Mỗi luận điểm PHẢI kèm trích dẫn: [PMID:xxx], [ICD-11:xxx], [RxCUI:xxx], [NCT:xxx], hoặc [FDA:drug_name].
3. Nếu không có đủ bằng chứng, nói rõ: "Không tìm thấy đủ bằng chứng trong cơ sở dữ liệu."
4. KHÔNG đưa ra lời khuyên điều trị cá nhân hóa.
5. Trả lời bằng tiếng Việt, rõ ràng, có cấu trúc.
6. Sử dụng markdown (heading, bold, bullet points, bảng nếu cần).

ĐỊNH DẠNG TRẢ LỜI:
- Tóm tắt ngắn gọn đầu tiên
- Nội dung chi tiết với trích dẫn inline
- Nếu có ClinicalTrials → mục riêng "🔬 Thử nghiệm lâm sàng liên quan"
- Nếu có OpenFDA → mục riêng "⚠️ Cảnh báo an toàn thuốc (FDA)"
- Phần "📚 Nguồn tham khảo:" liệt kê tất cả sources đã dùng
- Disclaimer cuối cùng

RESPONSE FORMAT (JSON):
{
    "summary": "câu trả lời đầy đủ bằng markdown",
    "citations": [
        {"source": "pubmed|icd11|rxnorm|clinicaltrials|openfda", "id": "PMID/code/RxCUI/NCT/drug", "title": "...", "url": "..."}
    ]
}"""


async def analyze_intent(query: str) -> Dict:
    """
    Phân tích intent của câu hỏi (như CLARA SINGLE EXTRACTOR node).
    Xác định loại câu hỏi và entities cần tra cứu.
    """
    try:
        messages = [
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
        response = await _chat_completion(
            messages,
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        result = json.loads(response["content"])
        return result

    except Exception as e:
        print(f"[LLM] Intent analysis error: {e}")
        # Fallback: trả về intent mặc định
        return {
            "intent": "general_medical",
            "entities": [],
            "keywords_en": [query],
            "keywords_vi": [query],
            "needs_pubmed": True,
            "needs_rxnorm": False,
            "needs_icd11": False,
        }


async def synthesize(query: str, evidence: List[Dict], conversation_history: List[Dict] = None) -> Dict:
    """
    Tổng hợp câu trả lời từ evidence (như CLARA LLM SUMMARIZER node).
    """
    # Format evidence thành text (giới hạn để không vượt context window)
    evidence_text = _format_evidence(evidence)
    # Truncate nếu evidence quá dài (tránh vượt context window)
    if len(evidence_text) > 12000:
        evidence_text = evidence_text[:12000] + "\n\n... [TRUNCATED — quá nhiều evidence, chỉ hiển thị phần đầu]"

    messages = [
        {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
    ]

    # Thêm lịch sử hội thoại (tối đa 6 tin nhắn gần nhất)
    if conversation_history:
        for msg in conversation_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    user_message = f"""Câu hỏi: {query}

[EVIDENCE]
{evidence_text}
[/EVIDENCE]

Hãy trả lời câu hỏi dựa trên evidence trên. Trả về JSON với "summary" và "citations"."""

    messages.append({"role": "user", "content": user_message})

    try:
        response = await _chat_completion(
            messages,
            temperature=0.3,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )

        content = response["content"].strip()
        if not content:
            raise Exception("LLM returned empty response")

        # Try to extract JSON from response (sometimes wrapped in markdown)
        if content.startswith("```"):
            # Remove markdown code block
            content = content.strip("`").strip()
            if content.startswith("json"):
                content = content[4:].strip()

        result = json.loads(content)

        # Đảm bảo format đúng
        if "summary" not in result:
            result["summary"] = response["content"]
        if "citations" not in result:
            result["citations"] = []

        return result

    except Exception as e:
        print(f"[LLM] Synthesis error: {e}")
        return {
            "summary": f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn. Lỗi: {str(e)}",
            "citations": [],
        }


def _format_evidence(evidence_list: List[Dict]) -> str:
    """Format danh sách evidence thành text cho LLM"""
    if not evidence_list:
        return "Không tìm thấy dữ liệu liên quan."

    parts = []
    for i, ev in enumerate(evidence_list, 1):
        source = ev.get("source", "unknown")

        if source == "pubmed":
            abstract = ev.get('abstract', 'N/A')[:800]  # Truncate abstract
            parts.append(
                f"--- PubMed Article [{i}] ---\n"
                f"PMID: {ev.get('pmid', 'N/A')}\n"
                f"Title: {ev.get('title', 'N/A')}\n"
                f"Authors: {', '.join(ev.get('authors', []))}\n"
                f"Journal: {ev.get('journal', 'N/A')} ({ev.get('year', 'N/A')})\n"
                f"Abstract: {abstract}\n"
                f"URL: {ev.get('url', '')}\n"
            )
        elif source == "rxnorm":
            parts.append(
                f"--- RxNorm Drug [{i}] ---\n"
                f"RxCUI: {ev.get('rxcui', 'N/A')}\n"
                f"Name: {ev.get('name', 'N/A')}\n"
                f"Type: {ev.get('tty', 'N/A')}\n"
                f"URL: {ev.get('url', '')}\n"
            )
        elif source == "rxnorm_interaction":
            parts.append(
                f"--- Drug Interaction [{i}] ---\n"
                f"Drug 1: {ev.get('drug1', 'N/A')}\n"
                f"Drug 2: {ev.get('drug2', 'N/A')}\n"
                f"Description: {ev.get('description', 'N/A')}\n"
                f"Severity: {ev.get('severity', 'N/A')}\n"
            )
        elif source == "icd11":
            parts.append(
                f"--- ICD-11 [{i}] ---\n"
                f"Code: {ev.get('code', 'N/A')}\n"
                f"Title: {ev.get('title', 'N/A')}\n"
                f"Definition: {ev.get('definition', 'N/A')}\n"
                f"URL: {ev.get('url', '')}\n"
            )
        elif source == "clinicaltrials":
            conditions = ", ".join(ev.get("conditions", []))
            interventions = ", ".join(ev.get("interventions", []))
            phases = ", ".join(ev.get("phases", []))
            parts.append(
                f"--- ClinicalTrials.gov [{i}] ---\n"
                f"NCT ID: {ev.get('nct_id', 'N/A')}\n"
                f"Title: {ev.get('title', 'N/A')}\n"
                f"Status: {ev.get('status', 'N/A')}\n"
                f"Conditions: {conditions}\n"
                f"Interventions: {interventions}\n"
                f"Phases: {phases}\n"
                f"Enrollment: {ev.get('enrollment', 'N/A')}\n"
                f"Summary: {ev.get('summary', 'N/A')}\n"
                f"URL: {ev.get('url', '')}\n"
            )
        elif source == "openfda_ae":
            reactions = ", ".join(ev.get("reactions", []))
            drugs = ", ".join(ev.get("drugs_involved", []))
            parts.append(
                f"--- FDA Adverse Event [{i}] ---\n"
                f"Drug: {ev.get('drug_name', 'N/A')}\n"
                f"Reported Reactions: {reactions}\n"
                f"Drugs Involved: {drugs}\n"
                f"Serious: {ev.get('serious', 'N/A')}\n"
                f"Death: {ev.get('seriousness_death', 'N/A')}\n"
                f"Hospitalization: {ev.get('seriousness_hospital', 'N/A')}\n"
                f"Report Date: {ev.get('receive_date', 'N/A')}\n"
                f"Country: {ev.get('report_country', 'N/A')}\n"
            )
        elif source == "openfda_recall":
            parts.append(
                f"--- FDA Drug Recall [{i}] ---\n"
                f"Drug: {ev.get('drug_name', 'N/A')}\n"
                f"Reason: {ev.get('recall_reason', 'N/A')}\n"
                f"Classification: {ev.get('classification', 'N/A')}\n"
                f"Status: {ev.get('status', 'N/A')}\n"
                f"Date: {ev.get('recall_date', 'N/A')}\n"
                f"Product: {ev.get('product_description', 'N/A')}\n"
            )
        elif source == "openfda_label":
            parts.append(
                f"--- FDA Drug Label [{i}] ---\n"
                f"Drug: {ev.get('generic_name', ev.get('drug_name', 'N/A'))}\n"
                f"Brand: {ev.get('brand_name', 'N/A')}\n"
                f"Indications: {ev.get('indications', 'N/A')}\n"
                f"Warnings: {ev.get('warnings', 'N/A')}\n"
                f"Contraindications: {ev.get('contraindications', 'N/A')}\n"
                f"Adverse Reactions: {ev.get('adverse_reactions', 'N/A')}\n"
                f"Dosage: {ev.get('dosage', 'N/A')}\n"
            )
        else:
            parts.append(f"--- Source [{i}] ---\n{json.dumps(ev, ensure_ascii=False)}\n")

    return "\n".join(parts)

