"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  Pill,
  FileCode,
  Bookmark,
  LogOut,
  Plus,
  Stethoscope,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SidebarProps {
  onNewChat?: () => void;
  onLogout?: () => void;
  userName?: string;
}

const navItems = [
  { href: "/chat", label: "Chat Y khoa", icon: MessageSquare },
  { href: "/drug-lookup", label: "Tra cứu thuốc", icon: Pill },
  { href: "/icd-lookup", label: "Tra mã ICD-11", icon: FileCode },
  { href: "/bookmarks", label: "Đã lưu", icon: Bookmark },
];

export default function Sidebar({ onNewChat, onLogout, userName }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r border-gray-200 bg-gray-50">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-4">
        <Stethoscope className="h-6 w-6 text-blue-600" />
        <div>
          <h1 className="text-sm font-bold text-gray-900">Medical Chatbot</h1>
          <p className="text-xs text-gray-500">Base on CLARA</p>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-3 py-3">
        <Button
          onClick={onNewChat}
          className="w-full justify-start gap-2"
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          Cuộc hội thoại mới
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="border-t border-gray-200 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-medium text-blue-600">
              {userName?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <span className="text-sm font-medium text-gray-700 truncate max-w-[120px]">
              {userName || "User"}
            </span>
          </div>
          <Button variant="ghost" size="icon" onClick={onLogout} title="Đăng xuất">
            <LogOut className="h-4 w-4 text-gray-500" />
          </Button>
        </div>
      </div>
    </div>
  );
}

