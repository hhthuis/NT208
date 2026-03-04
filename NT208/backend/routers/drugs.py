"""
Drug Lookup Router
GET /api/drugs/search?name=...  — Tìm thuốc
GET /api/drugs/:rxcui/interactions — Tương tác thuốc
POST /api/drugs/interactions  — Kiểm tra tương tác giữa nhiều thuốc
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List

from services import rxnorm_service
from models.schemas import DrugSearchResponse, DrugInfo, DrugInteraction

router = APIRouter()


@router.get("/search", response_model=DrugSearchResponse)
async def search_drugs(name: str = Query(..., min_length=1, description="Tên thuốc cần tìm")):
    """Tìm kiếm thuốc theo tên"""
    drugs = await rxnorm_service.search_drug(name)

    return DrugSearchResponse(
        drugs=[
            DrugInfo(
                rxcui=d.get("rxcui", ""),
                name=d.get("name", ""),
                synonym=d.get("synonym", ""),
                tty=d.get("tty", ""),
            )
            for d in drugs
        ]
    )


@router.get("/{rxcui}/interactions")
async def get_interactions(rxcui: str):
    """Lấy tương tác thuốc cho một RxCUI"""
    interactions = await rxnorm_service.get_drug_interactions(rxcui)

    return {
        "rxcui": rxcui,
        "interactions": [
            DrugInteraction(
                drug1=i.get("drug1", ""),
                drug2=i.get("drug2", ""),
                description=i.get("description", ""),
                severity=i.get("severity", ""),
                source=i.get("source", ""),
            )
            for i in interactions
        ],
        "total": len(interactions),
    }


@router.post("/interactions")
async def check_multi_interactions(rxcui_list: List[str]):
    """Kiểm tra tương tác giữa nhiều thuốc"""
    if len(rxcui_list) < 2:
        raise HTTPException(status_code=400, detail="Cần ít nhất 2 RxCUI")
    if len(rxcui_list) > 10:
        raise HTTPException(status_code=400, detail="Tối đa 10 RxCUI")

    interactions = await rxnorm_service.check_interactions_between(rxcui_list)

    return {
        "rxcuis": rxcui_list,
        "interactions": interactions,
        "total": len(interactions),
    }

