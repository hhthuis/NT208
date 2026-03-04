"use client";

import { useState, FormEvent } from "react";
import { Search, FileCode, Loader2, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { searchICD } from "@/lib/api";

interface ICDResult {
  code: string;
  title: string;
  definition: string;
  url: string;
}

export default function ICDLookupPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ICDResult[]>([]);
  const [total, setTotal] = useState(0);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError("");
    setResults([]);
    setSearched(true);

    try {
      const data = await searchICD(query.trim());
      setResults(data.results || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi khi tìm kiếm");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="mx-auto w-full max-w-4xl px-4 py-6 md:px-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
            <FileCode className="h-7 w-7 text-purple-600" />
            Tra mã ICD-11
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Tra cứu mã bệnh theo chuẩn ICD-11 của Tổ chức Y tế Thế giới (WHO)
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="mb-6 flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Nhập từ khóa (tiếng Anh: diabetes, hypertension, pneumonia...)"
            className="flex-1"
          />
          <Button type="submit" disabled={searching}>
            {searching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            <span className="ml-2 hidden sm:inline">Tìm kiếm</span>
          </Button>
        </form>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>
        )}

        {/* Quick search suggestions */}
        {!searched && (
          <div className="mb-6">
            <p className="mb-2 text-sm text-gray-500">Gợi ý tìm kiếm:</p>
            <div className="flex flex-wrap gap-2">
              {[
                "diabetes mellitus",
                "hypertension",
                "COVID-19",
                "pneumonia",
                "asthma",
                "malaria",
                "tuberculosis",
                "depression",
              ].map((term) => (
                <button
                  key={term}
                  onClick={() => {
                    setQuery(term);
                    // Auto search
                    setSearching(true);
                    setSearched(true);
                    searchICD(term)
                      .then((data) => {
                        setResults(data.results || []);
                        setTotal(data.total || 0);
                      })
                      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Lỗi"))
                      .finally(() => setSearching(false));
                  }}
                  className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-600 hover:bg-purple-50 hover:border-purple-300 transition-colors"
                >
                  {term}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {searching ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-purple-600" />
            <span className="ml-2 text-sm text-gray-500">Đang tìm kiếm...</span>
          </div>
        ) : searched && results.length === 0 ? (
          <div className="py-12 text-center text-sm text-gray-400">
            Không tìm thấy kết quả. Hãy thử từ khóa tiếng Anh khác.
          </div>
        ) : (
          <>
            {total > 0 && (
              <p className="mb-3 text-sm text-gray-500">
                Tìm thấy {total} kết quả
              </p>
            )}
            <div className="space-y-3">
              {results.map((result, i) => (
                <Card key={i} className="hover:border-purple-200 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex items-center gap-2">
                          <span className="shrink-0 rounded bg-purple-100 px-2 py-0.5 text-xs font-semibold text-purple-700">
                            {result.code}
                          </span>
                          <h3 className="font-medium text-gray-900 truncate">
                            {result.title}
                          </h3>
                        </div>
                        {result.definition && (
                          <p className="text-sm text-gray-600 line-clamp-2">
                            {result.definition}
                          </p>
                        )}
                      </div>
                      {result.url && (
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0 rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-purple-600"
                          title="Xem trên WHO ICD-11"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}

        {/* Disclaimer */}
        <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-3 text-center text-xs text-amber-700">
          ⚕️ Dữ liệu từ WHO ICD-11. Mã bệnh chỉ mang tính tham khảo, cần xác nhận bởi chuyên gia y tế.
        </div>
      </div>
    </div>
  );
}

