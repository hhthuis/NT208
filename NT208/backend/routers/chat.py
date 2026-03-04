"""
Chat Router — Core chatbot API
POST /api/chat/           — Gửi tin nhắn, nhận câu trả lời
GET  /api/chat/conversations — Danh sách hội thoại
GET  /api/chat/conversations/:id — Chi tiết hội thoại
DELETE /api/chat/conversations/:id — Xóa hội thoại
POST /api/chat/bookmarks  — Bookmark tin nhắn
GET  /api/chat/bookmarks  — Danh sách bookmark
DELETE /api/chat/bookmarks/:id — Xóa bookmark
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import List

from database.db import get_db
from database.models import User, Conversation, Message, Bookmark
from models.schemas import (
    ChatRequest, ChatResponse, ConversationResponse,
    ConversationDetailResponse, MessageResponse,
    BookmarkCreate, BookmarkResponse,
)
from routers.auth import get_current_user
from services.orchestrator import process_query

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def send_message(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Gửi câu hỏi y khoa và nhận câu trả lời có trích dẫn"""

    # Tạo hoặc lấy conversation
    if data.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == data.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Cuộc hội thoại không tồn tại")
    else:
        # Tạo conversation mới, title = 30 ký tự đầu của câu hỏi
        title = data.message[:50] + ("..." if len(data.message) > 50 else "")
        conversation = Conversation(user_id=current_user.id, title=title)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # Lưu tin nhắn user
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=data.message,
    )
    db.add(user_msg)
    await db.commit()

    # Lấy lịch sử hội thoại (để truyền context)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history_msgs = result.scalars().all()
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in reversed(history_msgs)
    ]

    # Gọi Orchestrator xử lý
    try:
        result = await process_query(
            user_query=data.message,
            conversation_history=conversation_history,
        )
    except Exception as e:
        result = {
            "answer": f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi. Vui lòng thử lại.\n\nLỗi: {str(e)}",
            "citations": [],
            "disclaimer": "⚕️ Thông tin chỉ mang tính tham khảo.",
        }

    # Lưu tin nhắn assistant
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        citations=result.get("citations", []),
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        answer=result["answer"],
        citations=result.get("citations", []),
        disclaimer=result.get("disclaimer", ""),
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Danh sách hội thoại của user"""
    result = await db.execute(
        select(
            Conversation,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message)
        .where(Conversation.user_id == current_user.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
    )
    rows = result.all()

    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=count,
        )
        for conv, count in rows
    ]


@router.get("/conversations/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chi tiết hội thoại với tất cả tin nhắn"""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Cuộc hội thoại không tồn tại")

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[MessageResponse.model_validate(m) for m in conversation.messages],
    )


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Xóa hội thoại"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Cuộc hội thoại không tồn tại")

    await db.delete(conversation)
    await db.commit()
    return {"message": "Đã xóa hội thoại"}


@router.post("/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark một tin nhắn"""
    result = await db.execute(select(Message).where(Message.id == data.message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Tin nhắn không tồn tại")

    bookmark = Bookmark(
        user_id=current_user.id,
        message_id=data.message_id,
        note=data.note,
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)

    return BookmarkResponse.model_validate(bookmark)


@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def list_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Danh sách bookmark của user"""
    result = await db.execute(
        select(Bookmark)
        .options(selectinload(Bookmark.message))
        .where(Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
    )
    bookmarks = result.scalars().all()

    return [
        BookmarkResponse(
            id=b.id,
            message_id=b.message_id,
            note=b.note,
            created_at=b.created_at,
            message=MessageResponse.model_validate(b.message) if b.message else None,
        )
        for b in bookmarks
    ]


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Xóa bookmark"""
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == current_user.id,
        )
    )
    bookmark = result.scalar_one_or_none()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark không tồn tại")

    await db.delete(bookmark)
    await db.commit()
    return {"message": "Đã xóa bookmark"}

