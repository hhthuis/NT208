"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Loader2, MessageSquare, Trash2 } from "lucide-react";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import { Button } from "@/components/ui/button";
import {
  sendMessage,
  getConversations,
  getConversation,
  deleteConversation,
  createBookmark,
} from "@/lib/api";

interface Citation {
  source: string;
  id: string;
  title: string;
  url: string;
}

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
}

interface Conversation {
  id: number;
  title: string;
  created_at: string;
  message_count: number;
}

export default function ChatPage() {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);
  const [loadingConv, setLoadingConv] = useState(false);
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<number>>(new Set());

  // Load conversations list
  const loadConversations = useCallback(async () => {
    try {
      const convs = await getConversations();
      setConversations(convs);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load specific conversation
  const loadConversation = useCallback(async (convId: number) => {
    setLoadingConv(true);
    try {
      const detail = await getConversation(convId);
      setMessages(detail.messages || []);
      setActiveConvId(convId);
    } catch (err) {
      console.error("Failed to load conversation:", err);
    } finally {
      setLoadingConv(false);
    }
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Start new chat
  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([]);
  };

  // Send message
  const handleSend = async (text: string) => {
    // Add user message optimistically
    const tempUserMsg: Message = {
      id: Date.now(),
      role: "user",
      content: text,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setSending(true);

    try {
      const response = await sendMessage(text, activeConvId || undefined);

      // Update active conversation id
      if (!activeConvId) {
        setActiveConvId(response.conversation_id);
      }

      // Add assistant response
      const assistantMsg: Message = {
        id: response.message_id,
        role: "assistant",
        content: response.answer,
        citations: response.citations || [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Refresh conversation list
      loadConversations();
    } catch (err: unknown) {
      // Show error as assistant message
      const errorMsg: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: `❌ Lỗi: ${err instanceof Error ? err.message : "Không thể gửi tin nhắn"}. Vui lòng thử lại.`,
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  // Delete conversation
  const handleDeleteConv = async (convId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Xóa cuộc hội thoại này?")) return;
    try {
      await deleteConversation(convId);
      if (activeConvId === convId) {
        setActiveConvId(null);
        setMessages([]);
      }
      loadConversations();
    } catch (err) {
      console.error("Failed to delete:", err);
    }
  };

  // Bookmark
  const handleBookmark = async (messageId: number) => {
    try {
      await createBookmark(messageId);
      setBookmarkedIds((prev) => new Set(prev).add(messageId));
    } catch (err) {
      console.error("Failed to bookmark:", err);
    }
  };

  return (
    <div className="flex h-full">
      {/* Conversation List Sidebar */}
      <div className="hidden w-64 flex-col border-r border-gray-200 bg-white md:flex">
        <div className="border-b p-3">
          <Button onClick={handleNewChat} variant="outline" className="w-full gap-2 text-sm">
            <MessageSquare className="h-4 w-4" />
            Hội thoại mới
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <p className="p-4 text-center text-sm text-gray-400">Chưa có hội thoại nào</p>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`group flex cursor-pointer items-center justify-between border-b border-gray-100 px-3 py-2.5 hover:bg-gray-50 ${
                  activeConvId === conv.id ? "bg-blue-50" : ""
                }`}
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-gray-700">{conv.title}</p>
                  <p className="text-xs text-gray-400">{conv.message_count} tin nhắn</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100"
                  onClick={(e) => handleDeleteConv(conv.id, e)}
                >
                  <Trash2 className="h-3.5 w-3.5 text-gray-400" />
                </Button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex flex-1 flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8">
          {loadingConv ? (
            <div className="flex h-full items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100">
                <MessageSquare className="h-8 w-8 text-blue-600" />
              </div>
              <h2 className="mb-2 text-xl font-semibold text-gray-900">
                Bắt đầu cuộc hội thoại
              </h2>
              <p className="max-w-md text-sm text-gray-500">
                Hỏi bất kỳ câu hỏi y khoa nào. Tôi sẽ tìm kiếm từ PubMed, ICD-11 và RxNorm
                để cung cấp câu trả lời có trích dẫn nguồn.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {[
                  "Triệu chứng của bệnh tiểu đường type 2?",
                  "Tác dụng phụ của Metformin?",
                  "ICD-11 code cho tăng huyết áp?",
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="rounded-full border border-gray-200 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl py-4">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  role={msg.role}
                  content={msg.content}
                  citations={msg.citations}
                  isBookmarked={bookmarkedIds.has(msg.id)}
                  onBookmark={
                    msg.role === "assistant" ? () => handleBookmark(msg.id) : undefined
                  }
                />
              ))}
              {sending && (
                <div className="flex gap-3 py-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-600">
                    <Loader2 className="h-4 w-4 animate-spin text-white" />
                  </div>
                  <div className="rounded-2xl bg-gray-100 px-4 py-3">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Đang tìm kiếm và phân tích...
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t bg-white px-4 py-3 md:px-8">
          <div className="mx-auto max-w-3xl">
            <ChatInput onSend={handleSend} disabled={sending} />
          </div>
        </div>
      </div>
    </div>
  );
}

