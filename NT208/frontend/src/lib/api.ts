const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ========== Helper ==========
function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function fetchAPI(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Lỗi không xác định" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ========== Auth ==========
export async function register(email: string, password: string, name: string) {
  const data = await fetchAPI("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  });
  localStorage.setItem("token", data.access_token);
  return data;
}

export async function login(email: string, password: string) {
  const data = await fetchAPI("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("token", data.access_token);
  return data;
}

export async function getMe() {
  return fetchAPI("/api/auth/me");
}

export function logout() {
  localStorage.removeItem("token");
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

// ========== Chat ==========
export async function sendMessage(message: string, conversationId?: number) {
  return fetchAPI("/api/chat/", {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_id: conversationId || null,
    }),
  });
}

export async function getConversations() {
  return fetchAPI("/api/chat/conversations");
}

export async function getConversation(id: number) {
  return fetchAPI(`/api/chat/conversations/${id}`);
}

export async function deleteConversation(id: number) {
  return fetchAPI(`/api/chat/conversations/${id}`, { method: "DELETE" });
}

// ========== Bookmarks ==========
export async function createBookmark(messageId: number, note: string = "") {
  return fetchAPI("/api/chat/bookmarks", {
    method: "POST",
    body: JSON.stringify({ message_id: messageId, note }),
  });
}

export async function getBookmarks() {
  return fetchAPI("/api/chat/bookmarks");
}

export async function deleteBookmark(id: number) {
  return fetchAPI(`/api/chat/bookmarks/${id}`, { method: "DELETE" });
}

// ========== Drug Lookup ==========
export async function searchDrugs(name: string) {
  return fetchAPI(`/api/drugs/search?name=${encodeURIComponent(name)}`);
}

export async function getDrugInteractions(rxcui: string) {
  return fetchAPI(`/api/drugs/${rxcui}/interactions`);
}

// ========== ICD-11 Lookup ==========
export async function searchICD(query: string) {
  return fetchAPI(`/api/icd/search?q=${encodeURIComponent(query)}`);
}

export async function getICDDetail(code: string) {
  return fetchAPI(`/api/icd/${encodeURIComponent(code)}`);
}

