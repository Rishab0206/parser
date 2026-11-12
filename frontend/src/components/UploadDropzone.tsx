import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileText, Lock, CheckCircle2, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { uploadStatement, getStatementStatus, getApplications, createApplication } from '../api/statements';
import { useNavigate } from 'react-router-dom';

interface UploadDropzoneProps {
  onUploadSuccess?: (statementId: string) => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onUploadSuccess }) => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [applicationId, setApplicationId] = useState<string>('');
  const [applications, setApplications] = useState<any[]>([]);
  const [customerName, setCustomerName] = useState<string>('');
  const [accountType, setAccountType] = useState<string>('SAVINGS');
  const [password, setPassword] = useState<string>('');
  const [isProtected, setIsProtected] = useState<boolean>(false);
  
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [stage, setStage] = useState<string>('');
  const [parseResult, setParseResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [structuredError, setStructuredError] = useState<{ error_code: string; message: string; details: any } | null>(null);

  useEffect(() => {
    getApplications()
      .then((apps) => {
        setApplications(apps);
        const savedId = localStorage.getItem('current_customer_app_id');
        if (savedId && apps.some((a) => a.id === savedId)) {
          setApplicationId(savedId);
        } else {
          setApplicationId('NEW');
        }
      })
      .catch((err) => console.error("Error loading applications", err));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0]);
        setErrorMsg(null);
      }
    }
  });

  const handleUpload = async () => {
    if (!file) {
      setErrorMsg("Please select a bank statement file to upload.");
      return;
    }
    if (!applicationId) {
      setErrorMsg("Please select or create an application.");
      return;
    }

    setIsUploading(true);
    setErrorMsg(null);
    setStructuredError(null);
    setParseResult(null);

    // Multi-stage progress animation
    setStage("Extracting pages & checking encryption...");

    try {
      const targetAppId = applicationId === 'NEW' ? undefined : applicationId;
      const resp = await uploadStatement(
        file,
        targetAppId,
        isProtected ? password : undefined,
        accountType,
        customerName.trim() || undefined
      );

      if (resp.application_id) {
        localStorage.setItem('current_customer_app_id', resp.application_id);
      }

      setStage("Detecting bank & parsing transaction table...");
      
      // Poll statement status
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        try {
          const status = await getStatementStatus(resp.statement_id);
          if (status.status === 'PARSED' || status.status === 'NEEDS_REVIEW') {
            clearInterval(interval);
            setIsUploading(false);
            setParseResult(status);
            if (onUploadSuccess) onUploadSuccess(resp.statement_id);
          } else if (status.status === 'FAILED') {
            clearInterval(interval);
            setIsUploading(false);
            const errMsg = status.error_message || "Statement parsing failed.";
            setErrorMsg(errMsg);
            setStructuredError({
              error_code: "STATEMENT_PARSE_FAILED",
              message: errMsg,
              details: status.error_report || { statement_id: status.statement_id }
            });
          } else {
            if (attempts === 2) setStage("Classifying transactions & detecting EMIs...");
            if (attempts === 4) setStage("Reconciling returns & calculating monthly ABB...");
          }
        } catch (e: any) {
          clearInterval(interval);
          setIsUploading(false);
          setErrorMsg(e.message || "Could not fetch parsing progress.");
          setStructuredError({
            error_code: e.error_code || "PROGRESS_FETCH_FAILED",
            message: e.message || "Failed to poll status",
            details: e.details || {}
          });
        }
      }, 1500);

    } catch (err: any) {
      setIsUploading(false);
      setErrorMsg(err.message || "Upload failed");
      setStructuredError({
        error_code: err.error_code || "UPLOAD_FAILED",
        message: err.message || "Upload request failed",
        details: err.details || {}
      });
    }
  };

  const handleDownloadErrorReport = () => {
    const reportData = parseResult?.error_report || structuredError?.details || {
      error_code: structuredError?.error_code,
      message: structuredError?.message,
      timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error_report_${parseResult?.statement_id || 'statement'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm max-w-2xl mx-auto">
      <h2 className="text-lg font-bold text-slate-900 mb-1">Upload Bank Statement</h2>
      <p className="text-xs text-slate-500 mb-5">
        Supports PDF, scanned PDF, Excel (.xlsx, .xls), and CSV up to 50MB. Passwords are held in memory only during parsing and cleared immediately.
      </p>

      {structuredError && (
        <div className="mb-4 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs space-y-2">
          <div className="flex items-center justify-between font-bold text-rose-800">
            <span className="flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-rose-600" />
              Error [{structuredError.error_code}]
            </span>
            <button
              onClick={handleDownloadErrorReport}
              className="text-[11px] font-semibold text-rose-700 hover:text-rose-900 underline flex items-center gap-1"
            >
              Download Error Report
            </button>
          </div>
          <p className="font-medium">{structuredError.message}</p>
          {structuredError.details && Object.keys(structuredError.details).length > 0 && (
            <div className="font-mono text-[11px] bg-white/80 p-2 rounded border border-rose-200 text-rose-800 break-all">
              {JSON.stringify(structuredError.details)}
            </div>
          )}
        </div>
      )}

      {/* Result Card */}
      {parseResult ? (
        <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-950 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              {parseResult.failed_rows_count && parseResult.failed_rows_count > 0 ? (
                <span>Parsing Completed with Flagged Rows</span>
              ) : (
                <span>Statement Parsed Successfully!</span>
              )}
            </div>
            {((parseResult.failed_rows_count && parseResult.failed_rows_count > 0) || parseResult.review_queue_count > 0) && (
              <button
                onClick={handleDownloadErrorReport}
                className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 underline"
              >
                Download Error Report
              </button>
            )}
          </div>

          {parseResult.failed_rows_count && parseResult.failed_rows_count > 0 ? (
            <div className="p-3 bg-amber-50 border border-amber-300 rounded-lg text-amber-900 text-xs font-medium">
              Parsing failed on {parseResult.failed_rows_count} row(s). {parseResult.rows_parsed} row(s) parsed successfully. See Review Queue.
            </div>
          ) : null}

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs py-2 border-y border-emerald-200">
            <div>
              <span className="text-emerald-700 block text-[11px]">Bank Detected</span>
              <span className="font-semibold">{parseResult.bank_name}</span>
            </div>
            <div>
              <span className="text-emerald-700 block text-[11px]">Rows Parsed</span>
              <span className="font-semibold">{parseResult.rows_parsed} txns</span>
            </div>
            <div>
              <span className="text-emerald-700 block text-[11px]">Account No</span>
              <span className="font-mono font-semibold">{parseResult.account_no_masked}</span>
            </div>
            <div>
              <span className="text-emerald-700 block text-[11px]">Confidence</span>
              <span className="font-semibold">{parseResult.confidence}%</span>
            </div>
          </div>
          {parseResult.review_queue_count > 0 && (
            <p className="text-xs text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
              Note: {parseResult.review_queue_count} transaction(s) have been added to the Review Queue for underwriter verification.
            </p>
          )}
          <div className="pt-2 flex justify-end gap-2">
            <button
              onClick={() => {
                setFile(null);
                setParseResult(null);
                setStructuredError(null);
              }}
              className="px-4 py-2 border border-slate-300 bg-white rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Upload Another
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
            >
              Go to Dashboard
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-blue-500 bg-blue-50/50' : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
            }`}
          >
            <input {...getInputProps()} />
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm text-blue-600">
              <UploadCloud className="w-6 h-6" />
            </div>
            {file ? (
              <div>
                <p className="font-semibold text-sm text-slate-800">{file.name}</p>
                <p className="text-xs text-slate-400 mt-0.5">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-semibold text-slate-700">Drag & drop bank statement or click to browse</p>
                <p className="text-[11px] text-slate-400 mt-1">PDF, Scanned PDF, Excel, or CSV (Max 50MB)</p>
              </div>
            )}
          </div>

          {/* Form options */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-slate-600 font-medium mb-1">Customer / Applicant</label>
              <select
                value={applicationId}
                onChange={(e) => setApplicationId(e.target.value)}
                className="w-full p-2 bg-white border border-slate-300 rounded-lg text-slate-800"
              >
                <option value="NEW">+ New Customer (Auto-create)</option>
                {applications.map((app) => (
                  <option key={app.id} value={app.id}>
                    {app.customer_name} ({app.phone_masked || app.id.slice(0, 8)})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-600 font-medium mb-1">Account Type</label>
              <select
                value={accountType}
                onChange={(e) => setAccountType(e.target.value)}
                className="w-full p-2 bg-white border border-slate-300 rounded-lg text-slate-800"
              >
                <option value="SAVINGS">Savings Account</option>
                <option value="CURRENT">Current Account</option>
                <option value="OD">Overdraft (OD)</option>
                <option value="CC">Cash Credit (CC)</option>
              </select>
            </div>

            {applicationId === 'NEW' && (
              <div className="sm:col-span-2">
                <label className="block text-slate-600 font-medium mb-1">
                  Customer / Business Name <span className="text-slate-400 font-normal">(Optional — auto-extracted from bank statement header if blank)</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Vishal Rajeshkumar Mishra"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  className="w-full p-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400"
                />
              </div>
            )}
          </div>

          {/* Password Protection */}
          <div className="pt-2 border-t border-slate-100">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-700">
              <input
                type="checkbox"
                checked={isProtected}
                onChange={(e) => setIsProtected(e.target.checked)}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="flex items-center gap-1 font-medium">
                <Lock className="w-3.5 h-3.5 text-slate-400" />
                This PDF is password protected
              </span>
            </label>

            {isProtected && (
              <div className="mt-2">
                <input
                  type="password"
                  autoComplete="new-password"
                  placeholder="Enter PDF password (e.g. pan+dob)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full sm:w-80 p-2 text-xs bg-white border border-slate-300 rounded-lg"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Password is used only in RAM during parsing and never saved to DB or logs.
                </p>
              </div>
            )}
          </div>

          {/* Upload & Progress */}
          <div className="pt-3">
            {isUploading ? (
              <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 space-y-2 text-xs">
                <div className="flex items-center gap-2 font-semibold">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span>Processing Statement: {stage}</span>
                </div>
                <div className="w-full bg-blue-200 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-blue-600 h-full w-2/3 animate-pulse rounded-full" />
                </div>
              </div>
            ) : (
              <button
                disabled={!file || isUploading}
                onClick={handleUpload}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition-colors shadow-sm"
              >
                Upload & Start Verified Analysis
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

