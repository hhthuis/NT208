"use client";

import { useState, FormEvent } from "react";
import { Search, Pill, Loader2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { searchDrugs, getDrugInteractions } from "@/lib/api";

interface DrugInfo {
  rxcui: string;
  name: string;
  synonym: string;
  tty: string;
}

interface DrugInteraction {
  drug1: string;
  drug2: string;
  description: string;
  severity: string;
  source: string;
}

export default function DrugLookupPage() {
  const [query, setQuery] = useState("");
  const [drugs, setDrugs] = useState<DrugInfo[]>([]);
  const [interactions, setInteractions] = useState<DrugInteraction[]>([]);
  const [selectedDrug, setSelectedDrug] = useState<DrugInfo | null>(null);
  const [searching, setSearching] = useState(false);
  const [loadingInteractions, setLoadingInteractions] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError("");
    setDrugs([]);
    setInteractions([]);
    setSelectedDrug(null);

    try {
      const result = await searchDrugs(query.trim());
      setDrugs(result.drugs || []);
      if (result.drugs?.length === 0) {
        setError("Không tìm thấy thuốc nào. Thử tìm bằng tên tiếng Anh (ví dụ: aspirin, metformin).");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi khi tìm kiếm");
    } finally {
      setSearching(false);
    }
  };

  const handleCheckInteractions = async (drug: DrugInfo) => {
    setSelectedDrug(drug);
    setLoadingInteractions(true);
    setInteractions([]);

    try {
      const result = await getDrugInteractions(drug.rxcui);
      setInteractions(result.interactions || []);
    } catch (err: unknown) {
      console.error("Failed to load interactions:", err);
    } finally {
      setLoadingInteractions(false);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="mx-auto w-full max-w-4xl px-4 py-6 md:px-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
            <Pill className="h-7 w-7 text-emerald-600" />
            Tra cứu thuốc
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Tìm kiếm thông tin thuốc và kiểm tra tương tác thuốc từ RxNorm / DrugBank
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="mb-6 flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Nhập tên thuốc (tiếng Anh: aspirin, ibuprofen, metformin...)"
            className="flex-1"
          />
          <Button type="submit" disabled={searching}>
            {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            <span className="ml-2 hidden sm:inline">Tìm kiếm</span>
          </Button>
        </form>

        {error && (
          <div className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-700">{error}</div>
        )}

        {/* Results */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Drug List */}
          <div>
            <h2 className="mb-3 text-sm font-semibold text-gray-700">
              Kết quả ({drugs.length})
            </h2>
            {drugs.length === 0 && !searching && !error && (
              <p className="text-sm text-gray-400">Nhập tên thuốc để bắt đầu tìm kiếm</p>
            )}
            <div className="space-y-2">
              {drugs.map((drug) => (
                <Card
                  key={drug.rxcui}
                  className={`cursor-pointer transition-colors hover:border-emerald-300 ${
                    selectedDrug?.rxcui === drug.rxcui ? "border-emerald-500 bg-emerald-50" : ""
                  }`}
                  onClick={() => handleCheckInteractions(drug)}
                >
                  <CardContent className="p-3">
                    <p className="font-medium text-gray-900">{drug.name}</p>
                    {drug.synonym && (
                      <p className="text-xs text-gray-500">Synonym: {drug.synonym}</p>
                    )}
                    <div className="mt-1 flex items-center gap-2">
                      <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                        RxCUI: {drug.rxcui}
                      </span>
                      {drug.tty && (
                        <span className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-600">
                          {drug.tty}
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Interactions */}
          <div>
            <h2 className="mb-3 text-sm font-semibold text-gray-700">
              Tương tác thuốc
              {selectedDrug && ` — ${selectedDrug.name}`}
            </h2>
            {loadingInteractions ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang kiểm tra tương tác...
              </div>
            ) : selectedDrug && interactions.length === 0 ? (
              <p className="text-sm text-gray-400">Không tìm thấy tương tác thuốc nào được ghi nhận.</p>
            ) : !selectedDrug ? (
              <p className="text-sm text-gray-400">Chọn một thuốc để xem tương tác</p>
            ) : (
              <div className="space-y-2">
                {interactions.map((interaction, i) => (
                  <Card key={i} className="border-amber-200 bg-amber-50">
                    <CardContent className="p-3">
                      <div className="mb-1 flex items-center gap-1.5">
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        <span className="text-sm font-medium text-amber-800">
                          {interaction.drug1} ↔ {interaction.drug2}
                        </span>
                      </div>
                      <p className="text-xs text-amber-700">{interaction.description}</p>
                      {interaction.severity && (
                        <span className="mt-1 inline-block rounded bg-amber-200 px-1.5 py-0.5 text-xs font-medium text-amber-800">
                          {interaction.severity}
                        </span>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-3 text-center text-xs text-amber-700">
          ⚕️ Thông tin thuốc chỉ mang tính tham khảo. Luôn tham vấn dược sĩ hoặc bác sĩ trước khi sử dụng.
        </div>
      </div>
    </div>
  );
}

