"use client";

import { useState } from "react";
import { FileDown, Loader2 } from "lucide-react";
import type { ResearchResponse } from "@/types/research";

interface PDFExportButtonProps {
  result: ResearchResponse;
  citationStyle?: "IEEE" | "APA" | "ACM" | "Nature";
}

export default function PDFExportButton({
  result,
  citationStyle = "IEEE",
}: PDFExportButtonProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const researchData = {
        query: result.query,
        answer: result.answer,
        sources: result.sources,
        quality_assessment: result.quality_assessment,
      };

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/research/export/pdf?citation_style=${citationStyle}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(researchData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `PDF generation failed: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `research_paper_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      console.log("PDF downloaded successfully");
    } catch (err: any) {
      console.error("PDF export error:", err);
      setError(err.message || "Failed to generate PDF");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <>
      <button
        onClick={handleDownload}
        disabled={isGenerating}
        className={`btn-ghost flex items-center gap-2 ${isGenerating ? "opacity-50 cursor-not-allowed" : ""}`}
        title="Download as publication-quality PDF"
      >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-xs">Generating...</span>
            </>
          ) : (
            <>
              <FileDown className="w-4 h-4" />
              <span className="text-xs">PDF</span>
            </>
          )}
      </button>

      {error && (
        <div className="absolute top-full mt-2 right-0 text-sm text-[#9b3b2e] bg-[#f7e4dd] px-4 py-2 rounded-lg border border-[#e2b7a9] whitespace-nowrap z-30">
          Error: {error}
        </div>
      )}
    </>
  );
}
