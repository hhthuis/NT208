"""
ICD-11 Lookup Router
GET /api/icd/search?q=...  — Tìm mã ICD-11
GET /api/icd/:code         — Chi tiết mã ICD-11
"""
from fastapi import APIRouter, Query

from services import icd_service
from models.schemas import ICDSearchResponse, ICDResult

router = APIRouter()


@router.get("/search", response_model=ICDSearchResponse)
async def search_icd(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm (tiếng Anh)"),
    max_results: int = Query(10, ge=1, le=50, description="Số kết quả tối đa"),
):
    """Tìm kiếm mã ICD-11 theo từ khóa"""
    results = await icd_service.search_icd(q, max_results)

    return ICDSearchResponse(
        results=[
            ICDResult(
                code=r.get("code", ""),
                title=r.get("title", ""),
                definition=r.get("definition", ""),
                url=r.get("url", ""),
            )
            for r in results
        ],
        total=len(results),
    )


@router.get("/{code}")
async def get_icd_detail(code: str):
    """Lấy chi tiết một mã ICD-11"""
    detail = await icd_service.get_icd_details(code)

    if not detail:
        return {
            "code": code,
            "title": "",
            "definition": "Không tìm thấy thông tin. Hãy kiểm tra lại mã ICD-11.",
            "url": f"https://icd.who.int/browse/2024-01/mms/en#/{code}",
        }

    return detail

