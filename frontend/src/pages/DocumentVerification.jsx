import { useState } from "react";
import { Upload, FileText } from "lucide-react";
import DocumentChecklist from "../components/DocumentChecklist";

/**
 * DocumentVerification page.
 *
 * Note on mock data: the spec's mocks/ folder (per its own file list)
 * has no mockDocument.js, so — same approach as the fraud data on
 * PropertyDetail — a small mock verification result is defined right
 * here rather than adding an unlisted mock file. Swap
 * simulateVerification() for a real POST /documents/verify call later.
 */

function simulateVerification() {
  // Matches Part 3's shape exactly:
  // { extracted_fields, match_results: [{field, status}], overall_status, disclaimer }
  return {
    extracted_fields: {
      owner_name: "Ramesh Kumar",
      property_address: "5th Block, Koramangala, Bengaluru",
      survey_number: "SY-4521",
      document_date: "12-03-2024",
    },
    match_results: [
      { field: "owner_name", status: "match" },
      { field: "property_address", status: "match" },
      { field: "survey_number", status: "mismatch" },
      { field: "document_date", status: "match" },
    ],
    overall_status: "flagged",
    disclaimer:
      "This is an automated check and does not replace legal verification. Please consult a professional before proceeding.",
  };
}

export default function DocumentVerification() {
  const [fileName, setFileName] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState(null);
  const [error] = useState(null);

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setResult(null); // clear any previous result when a new file is picked
    }
  }

  function handleVerify() {
    if (!fileName) return;
    setIsVerifying(true);
    // Simulated network delay, matching how a real upload+verify call
    // would take a moment — swap this whole block for a real await
    // axios.post('/documents/verify', formData) later.
    setTimeout(() => {
      setResult(simulateVerification());
      setIsVerifying(false);
    }, 1200);
  }

  return (
    <div className="p-6 md:p-8 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">
        Document Verification
      </h1>

      <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center space-y-3">
        <Upload size={28} className="mx-auto text-gray-400" />
        <div>
          <label
            htmlFor="document-upload-input"
            className="inline-block cursor-pointer text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            Choose a file to upload
            <input
              id="document-upload-input"
              name="document"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
          <p className="text-xs text-gray-400 mt-1">
            PDF, JPG, or PNG accepted
          </p>
        </div>

        {fileName && (
          <div className="flex items-center justify-center gap-2 text-sm text-gray-700 bg-gray-50 rounded-lg px-3 py-2">
            <FileText size={14} />
            {fileName}
          </div>
        )}
      </div>

      <button
        onClick={handleVerify}
        disabled={!fileName || isVerifying}
        className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {isVerifying ? "Verifying..." : "Verify Document"}
      </button>

      {error && (
        <p className="text-sm text-red-600 text-center">
          Something went wrong verifying this document. Please try again.
        </p>
      )}

      {result && (
        <DocumentChecklist
          matchResults={result.match_results}
          overallStatus={result.overall_status}
          disclaimer={result.disclaimer}
        />
      )}
    </div>
  );
}