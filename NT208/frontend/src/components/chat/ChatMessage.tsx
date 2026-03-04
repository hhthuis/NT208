"use client";

import ReactMarkdown from "react-markdown";
import { Bookmark, User, Bot, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Citation {
  source: string;
  id: string;
  title: string;
  url: string;
}

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  onBookmark?: () => void;
  isBookmarked?: boolean;
}

export default function ChatMessage({
  role,
  content,
  citations = [],
  onBookmark,
  isBookmarked,
}: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={cn("flex gap-3 py-4", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-blue-600" : "bg-emerald-600"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-white" />
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          "flex max-w-[80%] flex-col gap-2",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm",
            isUser
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-900"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-a:text-blue-600">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Citations */}
        {!isUser && citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {citations.map((citation, i) => (
              <a
                key={i}
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100 transition-colors"
              >
                <span>
                  {citation.source === "pubmed" && `PMID:${citation.id}`}
                  {citation.source === "icd11" && `ICD-11:${citation.id}`}
                  {citation.source === "rxnorm" && `RxCUI:${citation.id}`}
                </span>
                <ExternalLink className="h-3 w-3" />
              </a>
            ))}
          </div>
        )}

        {/* Bookmark button */}
        {!isUser && onBookmark && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onBookmark}
            className="h-7 gap-1 text-xs text-gray-400 hover:text-yellow-500"
          >
            <Bookmark
              className={cn("h-3.5 w-3.5", isBookmarked && "fill-yellow-400 text-yellow-500")}
            />
            {isBookmarked ? "Đã lưu" : "Lưu"}
          </Button>
        )}
      </div>
    </div>
  );
}

