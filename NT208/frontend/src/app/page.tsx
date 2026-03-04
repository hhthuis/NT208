import Link from "next/link";
import { Stethoscope, MessageSquare, Pill, FileCode, ArrowRight, Shield } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <Stethoscope className="h-7 w-7 text-blue-600" />
            <span className="text-lg font-bold text-gray-900">Medical Chatbot</span>
          </div>
          <div className="flex gap-3">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              Đăng nhập
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Đăng ký
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="mx-auto max-w-6xl px-6">
        <div className="py-20 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-blue-100 px-4 py-1.5 text-sm font-medium text-blue-700">
            <Shield className="h-4 w-4" />
            Dựa trên kiến trúc CLARA
          </div>
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
            Trợ lý tra cứu <span className="text-blue-600">Y khoa</span> thông minh
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-gray-600">
            Chatbot AI hỗ trợ tra cứu y khoa với trích dẫn có nguồn từ PubMed, WHO ICD-11 và RxNorm.
            Mọi thông tin đều kèm nguồn tham khảo đáng tin cậy.
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-base font-medium text-white shadow-lg hover:bg-blue-700 transition-colors"
          >
            Bắt đầu tra cứu
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>

        {/* Features */}
        <div className="grid gap-6 pb-20 sm:grid-cols-3">
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100">
              <MessageSquare className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">Chat Y khoa</h3>
            <p className="text-sm text-gray-600">
              Hỏi đáp y khoa bằng tiếng Việt. AI tổng hợp từ PubMed, ICD-11, RxNorm với trích dẫn PMID.
            </p>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100">
              <Pill className="h-6 w-6 text-emerald-600" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">Tra cứu thuốc</h3>
            <p className="text-sm text-gray-600">
              Tìm kiếm thông tin thuốc từ RxNorm, kiểm tra tương tác thuốc với cơ sở dữ liệu DrugBank.
            </p>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100">
              <FileCode className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">Tra mã ICD-11</h3>
            <p className="text-sm text-gray-600">
              Tra cứu mã bệnh theo chuẩn ICD-11 của WHO. Hỗ trợ tìm kiếm bằng từ khóa tiếng Anh.
            </p>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mb-10 rounded-xl border border-amber-200 bg-amber-50 p-4 text-center text-sm text-amber-800">
          ⚕️ Thông tin trên ứng dụng chỉ mang tính tham khảo cho học tập và nghiên cứu,
          không thay thế tư vấn y khoa chuyên nghiệp.
        </div>
      </main>
    </div>
  );
}
