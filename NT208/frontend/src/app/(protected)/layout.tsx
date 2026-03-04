"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import Sidebar from "@/components/layout/Sidebar";
import { getMe, logout, isLoggedIn } from "@/lib/api";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [userName, setUserName] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    getMe()
      .then((user) => {
        setUserName(user.name || user.email);
        setLoading(false);
      })
      .catch(() => {
        logout();
        router.replace("/login");
      });
  }, [router]);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  const handleNewChat = () => {
    router.push("/chat");
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        userName={userName}
      />
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}

