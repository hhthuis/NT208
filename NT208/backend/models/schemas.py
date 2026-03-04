from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ========== AUTH ==========
class UserRegister(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(default="", max_length=100)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ========== CHAT ==========
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[int] = None


class Citation(BaseModel):
    source: str  # "pubmed" | "icd11" | "rxnorm"
    id: str  # PMID, ICD code, RxCUI
    title: str = ""
    url: str = ""


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    disclaimer: str = "⚕️ Thông tin chỉ mang tính tham khảo cho học tập và nghiên cứu, không thay thế tư vấn y khoa chuyên nghiệp."
    conversation_id: int
    message_id: int


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: list = []
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


# ========== DRUG LOOKUP ==========
class DrugSearchRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class DrugInfo(BaseModel):
    rxcui: str
    name: str
    synonym: str = ""
    tty: str = ""  # Term type


class DrugInteraction(BaseModel):
    drug1: str
    drug2: str
    description: str
    severity: str = ""
    source: str = ""


class DrugSearchResponse(BaseModel):
    drugs: List[DrugInfo] = []
    interactions: List[DrugInteraction] = []


# ========== ICD LOOKUP ==========
class ICDSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class ICDResult(BaseModel):
    code: str
    title: str
    definition: str = ""
    url: str = ""


class ICDSearchResponse(BaseModel):
    results: List[ICDResult] = []
    total: int = 0


# ========== BOOKMARK ==========
class BookmarkCreate(BaseModel):
    message_id: int
    note: str = ""


class BookmarkResponse(BaseModel):
    id: int
    message_id: int
    note: str
    created_at: datetime
    message: Optional[MessageResponse] = None

    class Config:
        from_attributes = True

