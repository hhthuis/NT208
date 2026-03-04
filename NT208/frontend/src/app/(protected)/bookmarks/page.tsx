"use client";

import { useState, useEffect } from "react";
import { Bookmark, Trash2, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getBookmarks, deleteBookmark } from "@/lib/api";

interface BookmarkMessage {
  id: number;
  role: string;
  content: string;
  citations: { source: string; id: string; title: string; url: string }[];
  created_at: string;
}

interface BookmarkItem {
  id: number;
  message_id: number;
  note: string;
  created_at: string;
  message: BookmarkMessage | null;
}

export default function BookmarksPage() {
  const [bookmarks, setBookmarks] = useState<BookmarkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadBookmarks = async () => {
    try {
      const data = await getBookmarks();
      setBookmarks(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi khi tải bookmarks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBookmarks();
  }, []);

  const handleDelete = async (bookmarkId: number) => {
    if (!confirm("Xóa bookmark này?")) return;
    try {
      await deleteBookmark(bookmarkId);
      setBookmarks((prev) => prev.filter((b) => b.id !== bookmarkId));
    } catch (err: unknown) {
      console.error("Failed to delete bookmark:", err);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="mx-auto w-full max-w-4xl px-4 py-6 md:px-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
            <Bookmark className="h-7 w-7 text-yellow-500" />
            Đã lưu
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Các câu trả lời bạn đã bookmark để xem lại sau
          </p>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-sm text-red-600">{error}</div>
        ) : bookmarks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-yellow-100">
              <Bookmark className="h-8 w-8 text-yellow-500" />
            </div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">Chưa có bookmark nào</h2>
            <p className="max-w-sm text-sm text-gray-500">
              Khi chat, nhấn nút &quot;Lưu&quot; trên các câu trả lời để bookmark chúng lại tại đây.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {bookmarks.map((bookmark) => (
              <Card key={bookmark.id} className="overflow-hidden">
                <CardContent className="p-0">
                  {/* Bookmark header */}
                  <div className="flex items-center justify-between border-b bg-gray-50 px-4 py-2">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Bookmark className="h-3.5 w-3.5 fill-yellow-400 text-yellow-500" />
                      <span>
                        Lưu lúc{" "}
                        {new Date(bookmark.created_at).toLocaleString("vi-VN", {
                          dateStyle: "short",
                          timeStyle: "short",
                        })}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-gray-400 hover:text-red-500"
                      onClick={() => handleDelete(bookmark.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>

                  {/* Message content */}
                  <div className="p-4">
                    {bookmark.message ? (
                      <div className="prose prose-sm max-w-none text-gray-700">
                        <ReactMarkdown>{bookmark.message.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400 italic">Tin nhắn đã bị xóa</p>
                    )}
                  </div>

                  {/* Note */}
                  {bookmark.note && (
                    <div className="border-t bg-yellow-50 px-4 py-2">
                      <p className="text-xs text-yellow-700">
                        <span className="font-medium">Ghi chú:</span> {bookmark.note}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

