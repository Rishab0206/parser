import React, { useState, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileText, Lock, CheckCircle2, AlertCircle, Loader2, ArrowRight, Eye, EyeOff, KeyRound, ShieldCheck, AlertTriangle, X } from 'lucide-react';
import { uploadStatement, getStatementStatus, getApplications, unlockStatement, inspectStatementFile, PdfInspectionResult } from '../api/statements';
import { useNavigate } from 'react-router-dom';

interface UploadDropzoneProps {
  onUploadSuccess?: (statementId: string) => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onUploadSuccess }) => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isInspecting, setIsInspecting] = useState<boolean>(false);
  const [inspectionResult, setInspectionResult] = useState<PdfInspectionResult | null>(null);
  const [applicationId, setApplicationId] = useState<string>('');
  const [applications, setApplications] = useState<any[]>([]);
  const [customerName, setCustomerName] = useState<string>('');
  const [accountType, setAccountType] = useState<string>('SAVINGS');
  const [password, setPassword] = useState<string>('');
  const [isProtected, setIsProtected] = useState<boolean>(false);
  
  // Pending password unlock state
  const [pendingUnlockStatementId, setPendingUnlockStatementId] = useState<string | null>(null);
  const [unlockPassword, setUnlockPassword] = useState<string>('');
  const [showUnlockPassword, setShowUnlockPassword] = useState<boolean>(false);
  const [unlockError, setUnlockError] = useState<string | null>(null);
  const [isUnlocking, setIsUnlocking] = useState<boolean>(false);
  const [showPasswordHints, setShowPasswordHints] = useState<boolean>(false);

  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [stage, setStage] = useState<string>('');
  const [backendStage, setBackendStage] = useState<string>('FILE_UPLOADED');
  const [failedStage, setFailedStage] = useState<string | null>(null);
  const [parseResult, setParseResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [structuredError, setStructuredError] = useState<{ error_code: string; message: string; details: any } | null>(null);
  const pollTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollTimerRef.current !== null) {
        window.clearTimeout(pollTimerRef.current);
      }
    };
  }, []);

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
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const selected = acceptedFiles[0];
        setFile(selected);
        setErrorMsg(null);
        setStructuredError(null);
        setParseResult(null);
        setPendingUnlockStatementId(null);
        setInspectionResult(null);
        setPassword('');
        setIsProtected(false);

        setIsInspecting(true);
        try {
          const insp = await inspectStatementFile(selected);
          setInspectionResult(insp);
          if (!insp.is_valid) {
            setStructuredError({
              error_code: insp.file_status || 'INVALID_FILE',
              message: insp.message || 'Invalid or corrupted PDF file.',
              details: { classification: insp.classification }
            });
          } else if (insp.is_encrypted) {
            setIsProtected(true);
          } else {
            setIsProtected(false);
          }
        } catch (err: any) {
          setStructuredError({
            error_code: err.error_code || 'INSPECTION_FAILED',
            message: err.message || 'Could not inspect uploaded file.',
            details: err.details || {}
          });
        } finally {
          setIsInspecting(false);
        }
      }
    }
  });

  const handleUnlockSubmit = async () => {
    if (!pendingUnlockStatementId || !unlockPassword.trim()) {
      setUnlockError("Please enter your account / PDF password.");
      return;
    }

    setIsUnlocking(true);
    setUnlockError(null);

    try {
      const result = await unlockStatement(pendingUnlockStatementId, unlockPassword.trim());
      setIsUnlocking(false);
      setPendingUnlockStatementId(null);
      setUnlockPassword('');
      setParseResult(result);
      if (onUploadSuccess) onUploadSuccess(result.statement_id);
    } catch (err: any) {
      setIsUnlocking(false);
      setUnlockError(err.message || "Incorrect password. Please verify and try again.");
    }
  };

  const clearPollTimer = () => {
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setErrorMsg("Please select a bank statement file to upload.");
      return;
    }
    if (!applicationId) {
      setErrorMsg("Please select or create an application.");
      return;
    }

    clearPollTimer();
    setIsUploading(true);
    setErrorMsg(null);
    setStructuredError(null);
    setParseResult(null);
    setPendingUnlockStatementId(null);
    setUnlockError(null);
    setFailedStage(null);
    setBackendStage('FILE_UPLOADED');

    // Multi-stage progress animation
    setStage("Uploading file & checking encryption...");

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

      // Check if statement requires password
      if (resp.status === 'PASSWORD_REQUIRED') {
        setBackendStage('PASSWORD_VERIFICATION');
        setIsUploading(false);
        setPendingUnlockStatementId(resp.statement_id);
        setUnlockError(resp.error_message || resp.message || "This bank statement is password protected. Please enter the password.");
        return;
      }

      if (resp.status === 'PARSED' || resp.status === 'PARSED_WITH_WARNINGS' || resp.status === 'NEEDS_REVIEW') {
        const finalStatus = await getStatementStatus(resp.statement_id);
        setBackendStage(finalStatus.processing_stage || 'ANALYSIS_COMPLETED');
        setIsUploading(false);
        setParseResult(finalStatus);
        if (onUploadSuccess) onUploadSuccess(resp.statement_id);
        return;
      }

      if (resp.status === 'PARSING_FAILED' || resp.status === 'INVALID_FILE' || resp.status === 'FAILED') {
        setIsUploading(false);
        setFailedStage(backendStage || 'PDF_VERIFICATION');
        const errMsg = resp.error_message || "Statement could not be parsed. Please check the PDF password, file quality or statement format.";
        setErrorMsg(errMsg);
        setStructuredError({
          error_code: resp.status,
          message: errMsg,
          details: { statement_id: resp.statement_id }
        });
        return;
      }

      setBackendStage('PDF_VERIFICATION');
      setStage("Inspecting PDF & unlocking document...");

      const STAGE_LABELS: Record<string, string> = {
        FILE_UPLOADED: "File uploaded, queuing analysis...",
        PDF_VERIFICATION: "Verifying PDF structure...",
        PASSWORD_VERIFICATION: "Checking PDF password...",
        DOCUMENT_UNLOCKING: "Unlocking PDF in memory...",
        TRANSACTION_EXTRACTION: "Extracting pages & transaction tables...",
        TRANSACTION_CATEGORIZATION: "Detecting bank & categorizing transactions...",
        BANKING_ANALYSIS: "Computing EMI, returns & monthly ABB...",
        ANALYSIS_COMPLETED: "Analysis completed!"
      };

      const MAX_POLL_ATTEMPTS = 45; // 45 * 1.5s = 67.5 seconds max
      let attempts = 0;

      const pollStatus = async () => {
        attempts += 1;
        try {
          const status = await getStatementStatus(resp.statement_id);
          const currentStage = status.processing_stage || 'PDF_VERIFICATION';
          setBackendStage(currentStage);
          if (STAGE_LABELS[currentStage]) {
            setStage(STAGE_LABELS[currentStage]);
          }

          if (status.status === 'PARSED' || status.status === 'PARSED_WITH_WARNINGS' || status.status === 'NEEDS_REVIEW') {
            clearPollTimer();
            setBackendStage('ANALYSIS_COMPLETED');
            setIsUploading(false);
            setParseResult(status);
            if (onUploadSuccess) onUploadSuccess(resp.statement_id);
            return;
          }

          if (status.status === 'PASSWORD_REQUIRED') {
            clearPollTimer();
            setBackendStage('PASSWORD_VERIFICATION');
            setIsUploading(false);
            setPendingUnlockStatementId(resp.statement_id);
            setUnlockError(status.error_message || "This bank statement is password protected. Please enter the password.");
            return;
          }

          if (status.status === 'PARSING_FAILED' || status.status === 'INVALID_FILE' || status.status === 'FAILED') {
            clearPollTimer();
            setIsUploading(false);
            const errMsg = status.error_message || "Statement could not be parsed. Please check the PDF password, file quality or statement format.";
            if (errMsg.toLowerCase().includes("password")) {
              setFailedStage('PASSWORD_VERIFICATION');
              setPendingUnlockStatementId(resp.statement_id);
              setUnlockError(errMsg);
            } else {
              setFailedStage(currentStage);
              setErrorMsg(errMsg);
              setStructuredError({
                error_code: status.status,
                message: errMsg,
                details: status.error_report || { statement_id: status.statement_id, stage: currentStage }
              });
            }
            return;
          }

          if (attempts >= MAX_POLL_ATTEMPTS) {
            clearPollTimer();
            setIsUploading(false);
            setFailedStage(currentStage);
            const timeoutMsg = `Processing timed out at stage ${currentStage} after ${Math.round((MAX_POLL_ATTEMPTS * 1.5))}s. Please retry or check server logs.`;
            setErrorMsg(timeoutMsg);
            setStructuredError({
              error_code: "PROCESSING_TIMEOUT",
              message: timeoutMsg,
              details: { statement_id: resp.statement_id, last_stage: currentStage, status: status.status }
            });
            return;
          }

          pollTimerRef.current = window.setTimeout(pollStatus, 1500);
        } catch (e: any) {
          clearPollTimer();
          setIsUploading(false);
          setFailedStage(backendStage || 'FILE_UPLOADED');
          const msg = e?.message || "Could not fetch parsing progress.";
          setErrorMsg(msg);
          setStructuredError({
            error_code: e?.error_code || "PROGRESS_FETCH_FAILED",
            message: msg,
            details: e?.details || {}
          });
        }
      };

      pollTimerRef.current = window.setTimeout(pollStatus, 1000);

    } catch (err: any) {
      clearPollTimer();
      setIsUploading(false);
      if (
        err.error_code === 'PASSWORD_REQUIRED' ||
        err.error_code === 'INCORRECT_PASSWORD' ||
        (err.message && err.message.toLowerCase().includes('password'))
      ) {
        if (err.details?.statement_id) {
          setPendingUnlockStatementId(err.details.statement_id);
          setUnlockError(err.message);
          return;
        }
      }
      setFailedStage('FILE_UPLOADED');
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
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm w-full">
      <h2 className="text-base font-bold text-slate-900 mb-1">Upload Bank Statement</h2>
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

      {/* Password Unlock Card */}
      {pendingUnlockStatementId ? (
        <div className="p-6 rounded-xl bg-amber-50/80 border border-amber-300 text-slate-800 space-y-4 shadow-sm animate-in fade-in duration-200">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-700 shrink-0 mt-0.5">
              <Lock className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-amber-950 flex items-center gap-2">
                Password-Protected Statement Detected
              </h3>
              <p className="text-xs text-amber-900 mt-0.5">
                <strong>{file ? file.name : "Uploaded statement"}</strong> is encrypted with an account password. Please enter the password below to unlock and run the complete verified financial analysis.
              </p>
            </div>
          </div>

          {unlockError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-900 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span className="font-medium">{unlockError}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Account / Statement Password
            </label>
            <div className="relative">
              <input
                type={showUnlockPassword ? "text" : "password"}
                value={unlockPassword}
                onChange={(e) => {
                  setUnlockPassword(e.target.value);
                  setUnlockError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleUnlockSubmit();
                }}
                placeholder="Enter password (e.g. DOB in DDMMYYYY, PAN, or Name+DOB)"
                autoFocus
                className="w-full px-3 py-2.5 pr-10 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 font-mono shadow-xs"
              />
              <button
                type="button"
                onClick={() => setShowUnlockPassword(!showUnlockPassword)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                title={showUnlockPassword ? "Hide password" : "Show password"}
              >
                {showUnlockPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-[11px] text-slate-500">
              Passwords are used in RAM only for instant extraction and are never saved to disk or database.
            </p>
          </div>

          {/* Quick Indian Bank Password Hints */}
          <div className="bg-white/80 rounded-lg p-3 text-xs border border-amber-200 shadow-xs">
            <button
              type="button"
              onClick={() => setShowPasswordHints(!showPasswordHints)}
              className="w-full flex items-center justify-between text-amber-900 font-semibold text-[11px]"
            >
              <span className="flex items-center gap-1.5">
                <KeyRound className="w-3.5 h-3.5 text-amber-700" />
                Indian Bank Password Formats (HDFC, SBI, ICICI, Kotak, Axis)
              </span>
              <span className="text-amber-700 hover:text-amber-900 text-[10px] underline">
                {showPasswordHints ? "Hide hints ▲" : "View hints ▼"}
              </span>
            </button>

            {showPasswordHints && (
              <div className="mt-2.5 pt-2 border-t border-amber-200 text-[11px] text-amber-950 space-y-1.5 font-normal">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  <div><strong>HDFC Bank:</strong> Customer ID (9 digits) OR DOB (DDMMYYYY)</div>
                  <div><strong>State Bank of India (SBI):</strong> DOB (DDMMYYYY) + Last 5 digits of mobile</div>
                  <div><strong>ICICI Bank:</strong> First 4 letters of name (lowercase) + DOB (DDMM)</div>
                  <div><strong>Axis Bank:</strong> First 4 letters of name (CAPS) + Last 4 digits of account</div>
                  <div><strong>Kotak Bank:</strong> CRN number OR Date of birth (DDMMYYYY)</div>
                  <div><strong>Canara / BOB:</strong> Customer ID OR First 4 letters + DDMM</div>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              type="button"
              disabled={isUnlocking}
              onClick={() => {
                setPendingUnlockStatementId(null);
                setUnlockPassword('');
                setUnlockError(null);
                setIsUploading(false);
              }}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 bg-white border border-slate-300 rounded-lg"
            >
              Cancel
            </button>

            <button
              type="button"
              disabled={isUnlocking || !unlockPassword.trim()}
              onClick={handleUnlockSubmit}
              className="px-5 py-2 text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg flex items-center gap-1.5 shadow-sm transition-colors"
            >
              {isUnlocking ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Unlocking & Running Analysis...</span>
                </>
              ) : (
                <>
                  <Lock className="w-3.5 h-3.5" />
                  <span>Unlock & Start Analysis</span>
                </>
              )}
            </button>
          </div>
        </div>
      ) : parseResult ? (
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
              <span className="font-semibold">{parseResult.bank_name || 'Unavailable'}</span>
            </div>
            <div>
              <span className="text-emerald-700 block text-[11px]">Rows Parsed</span>
              <span className="font-semibold">{parseResult.rows_parsed} txns</span>
            </div>
            <div>
              <span className="text-emerald-700 block text-[11px]">Account No</span>
              <span className="font-mono font-semibold">{parseResult.account_no_masked || '—'}</span>
            </div>
            <div>
              <span className="text-emerald-700 block text-[11px]">Confidence</span>
              <span className="font-semibold">{parseResult.confidence}%</span>
            </div>
          </div>

          {parseResult.opening_balance !== undefined && parseResult.opening_balance !== null && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs py-2 border-b border-emerald-200">
              <div>
                <span className="text-emerald-700 block text-[11px]">Opening Balance</span>
                <span className="font-mono font-semibold">₹{Number(parseResult.opening_balance).toLocaleString('en-IN')}</span>
              </div>
              <div>
                <span className="text-emerald-700 block text-[11px]">Closing Balance</span>
                <span className="font-mono font-semibold">₹{Number(parseResult.closing_balance).toLocaleString('en-IN')}</span>
              </div>
              <div>
                <span className="text-emerald-700 block text-[11px]">Total Credits</span>
                <span className="font-mono font-semibold text-emerald-700">₹{Number(parseResult.total_credits || 0).toLocaleString('en-IN')}</span>
              </div>
              <div>
                <span className="text-emerald-700 block text-[11px]">Reconciliation</span>
                <span className={`font-semibold ${parseResult.reconciliation_status === 'MISMATCH' ? 'text-amber-700' : 'text-emerald-700'}`}>
                  {parseResult.reconciliation_status || 'UNAVAILABLE'}
                </span>
              </div>
            </div>
          )}

          {parseResult.reconciliation_status === 'MISMATCH' && (
            <div className="p-3 bg-amber-50 border border-amber-300 rounded-lg text-amber-900 text-xs flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">Balance Reconciliation Warning</span>
                <span>
                  Expected closing balance (₹{Number(parseResult.expected_closing_balance || 0).toLocaleString('en-IN')}) differs from extracted closing balance (₹{Number(parseResult.closing_balance || 0).toLocaleString('en-IN')}) by ₹{Number(parseResult.reconciliation_diff || 0).toLocaleString('en-IN')}. Please inspect the Review Queue.
                </span>
              </div>
            </div>
          )}
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
              <div className="flex items-center justify-center gap-3">
                <div className="text-left">
                  <p className="font-semibold text-sm text-slate-800">{file.name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    setInspectionResult(null);
                    setIsProtected(false);
                    setPassword('');
                    setErrorMsg(null);
                    setStructuredError(null);
                  }}
                  className="p-1.5 rounded-full bg-white border border-slate-200 text-slate-500 hover:text-rose-600 hover:border-rose-300 shadow-xs"
                  title="Remove file"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div>
                <p className="text-xs font-semibold text-slate-700">Drag & drop bank statement or click to browse</p>
                <p className="text-[11px] text-slate-400 mt-1">PDF, Scanned PDF, Excel, or CSV (Max 50MB)</p>
              </div>
            )}
          </div>

          {/* Automatic Backend PDF Inspection Status */}
          {isInspecting && (
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-xs flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span className="font-medium">Inspecting PDF security & encryption status...</span>
            </div>
          )}

          {!isInspecting && inspectionResult && inspectionResult.is_valid && (
            <div className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
              inspectionResult.is_encrypted
                ? 'bg-amber-50 border-amber-300 text-amber-900'
                : 'bg-emerald-50 border-emerald-200 text-emerald-900'
            }`}>
              <div className="flex items-center gap-2">
                {inspectionResult.is_encrypted ? (
                  <Lock className="w-4 h-4 text-amber-700 shrink-0" />
                ) : (
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                )}
                <div>
                  <span className="font-bold">
                    {inspectionResult.is_encrypted
                      ? 'PDF Security Status: Password Protected'
                      : 'PDF Verified – No Password Required'}
                  </span>
                  <span className="block text-[11px] opacity-90">{inspectionResult.message}</span>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/70 border border-current/20">
                {inspectionResult.page_count} page{inspectionResult.page_count !== 1 ? 's' : ''}
              </span>
            </div>
          )}

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

          {/* Dynamic Password Protection Section */}
          {(isProtected || !inspectionResult || inspectionResult.is_encrypted) ? (
            <div className={`p-4 rounded-xl border transition-all ${
              isProtected ? 'bg-amber-50/90 border-amber-300' : 'bg-slate-50 border-slate-200'
            }`}>
              <label className="flex items-center justify-between cursor-pointer select-none">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={isProtected}
                    onChange={(e) => setIsProtected(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <div>
                    <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-amber-600" />
                      This statement is password protected
                    </span>
                    <span className="text-[11px] text-slate-500 block">
                      {inspectionResult?.is_encrypted
                        ? 'Encryption automatically detected. Enter the PDF password to unlock & parse.'
                        : 'Check this box only if your bank statement requires a password to open'}
                    </span>
                  </div>
                </div>
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full ${
                  isProtected ? 'bg-amber-200 text-amber-900 border border-amber-300' : 'bg-slate-200 text-slate-600'
                }`}>
                  {isProtected ? 'Password Required' : 'Optional'}
                </span>
              </label>

              {isProtected && (
                <div className="mt-3 pt-3 border-t border-amber-200 space-y-2 animate-in fade-in duration-150">
                  <label className="block text-xs font-semibold text-slate-700">
                    Enter Bank Statement Password
                  </label>
                  <div className="relative">
                    <input
                      type={showUnlockPassword ? "text" : "password"}
                      autoComplete="new-password"
                      placeholder="Enter Bank Statement Password (e.g. DOB in DDMMYYYY, PAN)"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3 py-2 pr-10 text-xs bg-white border border-amber-300 rounded-lg text-slate-900 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 font-mono shadow-xs"
                    />
                    <button
                      type="button"
                      onClick={() => setShowUnlockPassword(!showUnlockPassword)}
                      className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                      title={showUnlockPassword ? "Hide password" : "Show password"}
                    >
                      {showUnlockPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-amber-900">
                    <span className="text-[10px] text-slate-500">
                      Password is held in RAM only during parsing and never saved to database or logs.
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowPasswordHints(!showPasswordHints)}
                      className="text-amber-800 hover:text-amber-950 font-semibold underline text-[10px]"
                    >
                      {showPasswordHints ? 'Hide bank hints ▲' : 'View bank hints ▼'}
                    </button>
                  </div>

                  {showPasswordHints && (
                    <div className="p-2.5 bg-white/90 rounded-lg border border-amber-200 text-[11px] text-slate-700 space-y-1">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[10px]">
                        <div><strong>HDFC:</strong> Customer ID (9 digits) or DOB (DDMMYYYY)</div>
                        <div><strong>SBI:</strong> DOB (DDMMYYYY) + Last 5 digits mobile</div>
                        <div><strong>ICICI:</strong> First 4 letters name (lowercase) + DDMM</div>
                        <div><strong>Axis:</strong> First 4 letters name (CAPS) + Last 4 acct</div>
                        <div><strong>Kotak:</strong> CRN or DOB (DDMMYYYY)</div>
                        <div><strong>Canara / BOB:</strong> Customer ID or Name + DDMM</div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-end">
              <label className="inline-flex items-center gap-1.5 text-[11px] text-slate-500 cursor-pointer hover:text-slate-700">
                <input
                  type="checkbox"
                  checked={isProtected}
                  onChange={(e) => setIsProtected(e.target.checked)}
                  className="w-3.5 h-3.5 rounded border-slate-300 text-blue-600"
                />
                <span>This statement is password protected (manual entry)</span>
              </label>
            </div>
          )}

          {/* Upload & 8-Step Processing Progress */}
          <div className="pt-3 space-y-3">
            {(isUploading || failedStage) && (
              <div className={`p-4 rounded-xl border space-y-3 text-xs ${
                failedStage
                  ? 'bg-rose-50/70 border-rose-200 text-rose-950'
                  : 'bg-blue-50/80 border-blue-200 text-blue-950'
              }`}>
                <div className="flex items-center justify-between font-semibold">
                  <div className="flex items-center gap-2">
                    {failedStage ? (
                      <>
                        <AlertCircle className="w-4 h-4 text-rose-600" />
                        <span>Processing Failed at Stage: {failedStage}</span>
                      </>
                    ) : (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                        <span>Processing Statement: {stage}</span>
                      </>
                    )}
                  </div>
                  <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded ${
                    failedStage ? 'bg-rose-100 text-rose-800' : 'bg-blue-100 text-blue-800'
                  }`}>
                    {failedStage || backendStage}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                  {[
                    { key: 'FILE_UPLOADED', label: '1. File Uploaded' },
                    { key: 'PDF_VERIFICATION', label: '2. PDF Verification' },
                    { key: 'PASSWORD_VERIFICATION', label: '3. Password Check' },
                    { key: 'DOCUMENT_UNLOCKING', label: '4. Doc Unlocking' },
                    { key: 'TRANSACTION_EXTRACTION', label: '5. Extraction' },
                    { key: 'TRANSACTION_CATEGORIZATION', label: '6. Categorization' },
                    { key: 'BANKING_ANALYSIS', label: '7. Banking Analysis' },
                    { key: 'ANALYSIS_COMPLETED', label: '8. Completed' },
                  ].map((step, idx, arr) => {
                    const activeKey = failedStage || backendStage;
                    const currentIdx = Math.max(0, arr.findIndex((s) => s.key === activeKey));
                    const isFailed = failedStage === step.key;
                    const isDone = !isFailed && (idx < currentIdx || (!failedStage && backendStage === 'ANALYSIS_COMPLETED'));
                    const isActive = !failedStage && idx === currentIdx && backendStage !== 'ANALYSIS_COMPLETED';
                    return (
                      <div
                        key={step.key}
                        className={`px-2 py-1.5 rounded-lg border text-[10px] font-medium flex items-center gap-1.5 ${
                          isFailed
                            ? 'bg-rose-100 border-rose-400 text-rose-900 font-bold'
                            : isDone
                            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                            : isActive
                            ? 'bg-white border-blue-400 text-blue-800 shadow-xs'
                            : 'bg-white/50 border-slate-200 text-slate-400'
                        }`}
                      >
                        {isFailed ? (
                          <AlertCircle className="w-3 h-3 text-rose-600 shrink-0" />
                        ) : isDone ? (
                          <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                        ) : isActive ? (
                          <Loader2 className="w-3 h-3 animate-spin text-blue-600 shrink-0" />
                        ) : (
                          <span className="w-2 h-2 rounded-full bg-slate-300 shrink-0" />
                        )}
                        <span className="truncate">{step.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {!isUploading && (
              <button
                disabled={!file || isUploading || isInspecting || inspectionResult?.is_valid === false || (isProtected && !password.trim())}
                onClick={handleUpload}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition-colors shadow-sm flex items-center justify-center gap-2"
              >
                {isProtected ? (
                  <>
                    <Lock className="w-3.5 h-3.5" />
                    <span>Unlock &amp; Continue</span>
                  </>
                ) : (
                  <span>Upload &amp; Start Verified Analysis</span>
                )}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

