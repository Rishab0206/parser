import React, { useState, useEffect } from 'react';
import { 
  Building, RefreshCw, Upload, Download, CheckCircle, 
  Layers, AlertTriangle, ShieldCheck, FileSpreadsheet, Eye, Plus,
  LogOut, Users, Shield
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { getApplications, getCustomerHistory, CustomerHistoryItem } from '../api/statements';
import { getAccounts, AccountCard as AccountCardType } from '../api/accounts';
import { getSummary, getAbbMonthly, SummaryKpis, MonthlySummary } from '../api/abb';
import { getEmis, EmiRecord } from '../api/emi';
import { getReturns, ReturnRecord } from '../api/returns';
import { getTransactions, TransactionItem } from '../api/transactions';
import { getReviewQueue, ReviewQueueItem } from '../api/review';
import { getApplicationHistory, exportToUnderwriting, AnalysisVersionItem } from '../api/underwriting';

import { AccountCard } from '../components/AccountCard';
import { KpiCards } from '../components/KpiCards';
import { EmiTable } from '../components/EmiTable';
import { ReturnsTable } from '../components/ReturnsTable';
import { MonthlyAbbTable } from '../components/MonthlyAbbTable';
import { TransactionsTable } from '../components/TransactionsTable';
import { ReviewQueueTable } from '../components/ReviewQueueTable';
import { CustomerHistoryTable } from '../components/CustomerHistoryTable';
import { GstIntelligenceCard } from '../components/GstIntelligenceCard';
import { EmptyState } from '../components/EmptyState';
import { formatDate } from '../utils/format';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  // State
  const [applications, setApplications] = useState<any[]>([]);
  const [customerHistory, setCustomerHistory] = useState<CustomerHistoryItem[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string>('');
  const [accounts, setAccounts] = useState<AccountCardType[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string | undefined>(undefined);

  const [summary, setSummary] = useState<SummaryKpis | null>(null);
  const [emis, setEmis] = useState<EmiRecord[]>([]);
  const [returns, setReturns] = useState<ReturnRecord[]>([]);
  const [monthlyAbb, setMonthlyAbb] = useState<MonthlySummary[]>([]);
  
  // Transactions pagination & filter
  const [txns, setTxns] = useState<TransactionItem[]>([]);
  const [totalTxns, setTotalTxns] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [search, setSearch] = useState<string>('');
  const [channel, setChannel] = useState<string>('ALL');
  const [category, setCategory] = useState<string>('ALL');

  const [reviewItems, setReviewItems] = useState<ReviewQueueItem[]>([]);
  const [history, setHistory] = useState<AnalysisVersionItem[]>([]);

  const [activeTab, setActiveTab] = useState<string>('overview');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const [showResetConfirm, setShowResetConfirm] = useState<boolean>(false);
  const [accessForbiddenError, setAccessForbiddenError] = useState<string | null>(null);

  const [currentUser, setCurrentUser] = useState<{ id: string; name: string; email: string; role: 'Admin' | 'Staff' } | null>(() => {
    try {
      const u = localStorage.getItem('auth_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  });

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    localStorage.removeItem('current_customer_app_id');
    navigate('/login');
  };

  // Load applications and customer history
  const refreshHistoryAndApps = async () => {
    try {
      const [apps, custHist] = await Promise.all([
        getApplications(),
        getCustomerHistory()
      ]);
      setApplications(apps);
      setCustomerHistory(custHist);

      // Persistence rule: check saved current_customer_app_id
      const savedAppId = localStorage.getItem('current_customer_app_id');
      if (savedAppId && apps.some((a) => a.id === savedAppId)) {
        setSelectedAppId(savedAppId);
      } else {
        // If user reset / new customer was triggered, leave empty
        setSelectedAppId('');
        setIsLoading(false);
      }
    } catch (e) {
      console.error("Error loading apps/history", e);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshHistoryAndApps();
  }, []);

  // Load app data
  const loadAppData = async (appId: string, accId?: string) => {
    if (!appId) {
      setSummary(null);
      setAccounts([]);
      setEmis([]);
      setReturns([]);
      setMonthlyAbb([]);
      setTxns([]);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setAccessForbiddenError(null);
    try {
      const [accs, sum, emiList, retList, abbList, rqList, histList] = await Promise.all([
        getAccounts(appId),
        getSummary(appId, accId),
        getEmis(appId),
        getReturns(appId),
        getAbbMonthly(appId, accId),
        getReviewQueue(appId),
        getApplicationHistory(appId),
      ]);

      setAccounts(accs);
      setSummary(sum);
      setEmis(emiList);
      setReturns(retList);
      setMonthlyAbb(abbList);
      setReviewItems(rqList);
      setHistory(histList);

      // Load initial transactions
      const txnResp = await getTransactions(appId, {
        account_id: accId,
        page: 1,
        page_size: 25,
        search,
        channel,
        category
      });
      setTxns(txnResp.items);
      setTotalTxns(txnResp.total);

    } catch (err: any) {
      console.error("Error loading application intelligence", err);
      if (err.status === 403 || err.error_code === 'FORBIDDEN') {
        setAccessForbiddenError(err.message || "Access Denied (403): You do not have permission to access this customer record. Staff can only access their own uploads.");
        setSummary(null);
        setAccounts([]);
        setEmis([]);
        setReturns([]);
        setMonthlyAbb([]);
        setTxns([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedAppId) {
      loadAppData(selectedAppId, selectedAccountId);
    } else {
      setIsLoading(false);
    }
  }, [selectedAppId, selectedAccountId]);

  // Load transactions on filter or page change
  const refreshTransactions = async (newPage = page) => {
    if (!selectedAppId) return;
    try {
      const txnResp = await getTransactions(selectedAppId, {
        account_id: selectedAccountId,
        page: newPage,
        page_size: 25,
        search,
        channel,
        category
      });
      setTxns(txnResp.items);
      setTotalTxns(txnResp.total);
      setPage(newPage);
    } catch (e) {
      console.error("Transaction fetch error", e);
    }
  };

  useEffect(() => {
    if (selectedAppId && !isLoading) {
      refreshTransactions(1);
    }
  }, [search, channel, category]);

  const handleExportUnderwriting = async (targetAppId?: string) => {
    const appId = targetAppId || selectedAppId;
    if (!appId) return;
    try {
      setExportStatus("Exporting verified payload to Underwriting Engine...");
      const res = await exportToUnderwriting(appId);
      setExportStatus(`Export Successful! Version ${res.analysis_version_id} delivered.`);
      setTimeout(() => setExportStatus(null), 5000);
    } catch (e: any) {
      setExportStatus(`Engine note: ${e.message || 'Underwriting engine export ready'}`);
    }
  };

  // Reset / New Customer execution
  const handleConfirmNewCustomer = () => {
    localStorage.removeItem('current_customer_app_id');
    setSelectedAppId('');
    setSelectedAccountId(undefined);
    setSummary(null);
    setAccounts([]);
    setEmis([]);
    setReturns([]);
    setMonthlyAbb([]);
    setTxns([]);
    setActiveTab('overview');
    setShowResetConfirm(false);
    getCustomerHistory().then((h) => setCustomerHistory(h));
  };

  // Select customer from History or Dropdown
  const handleSelectCustomer = (appId: string) => {
    if (!appId) {
      localStorage.removeItem('current_customer_app_id');
      setSelectedAppId('');
      setSummary(null);
      return;
    }
    localStorage.setItem('current_customer_app_id', appId);
    setSelectedAppId(appId);
    setSelectedAccountId(undefined);
    setActiveTab('overview');
  };

  const currentApp = applications.find((a) => a.id === selectedAppId);
  const isDashboardEmpty = !selectedAppId || !summary || !summary.has_data;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Reset / New Customer Confirmation Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                <Plus className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Start new customer?</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Current customer <span className="font-semibold text-slate-800">{currentApp?.customer_name || 'Applicant'}</span> will be saved in History.
                </p>
              </div>
            </div>
            <div className="pt-2 flex items-center justify-end gap-2.5">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-3.5 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmNewCustomer}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs"
              >
                Yes, Start New
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-lg shadow-sm">
              ₹
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 leading-tight">
                Bank Statement Intelligence
              </h1>
              <span className="text-[11px] text-slate-500 font-medium">
                Business Loan Underwriting Engine v2.0
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Application Selector */}
            <select
              value={selectedAppId}
              onChange={(e) => handleSelectCustomer(e.target.value)}
              className="py-1.5 px-3 bg-slate-50 border border-slate-300 rounded-lg text-xs font-semibold text-slate-800"
            >
              <option value="">Select Applicant</option>
              {applications.map((app) => (
                <option key={app.id} value={app.id}>
                  {app.customer_name} ({app.phone_masked || app.id.slice(0, 8)})
                </option>
              ))}
            </select>

            {/* New Customer Button */}
            <button
              onClick={() => {
                if (selectedAppId) {
                  setShowResetConfirm(true);
                } else {
                  navigate('/upload');
                }
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors"
              title="Reset dashboard and start a new customer analysis"
            >
              <Plus className="w-3.5 h-3.5" />
              + New Customer
            </button>

            {/* Upload Statement Button */}
            <button
              onClick={() => navigate('/upload')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              Upload Statement
            </button>

            {/* Export to Underwriting */}
            <button
              disabled={!selectedAppId}
              onClick={() => handleExportUnderwriting()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 disabled:opacity-40 text-slate-700 text-xs font-semibold transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Export
            </button>

            {/* Admin Manage Team Button */}
            {currentUser?.role === 'Admin' && (
              <button
                onClick={() => navigate('/admin/team')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 hover:bg-indigo-100 text-xs font-semibold transition-colors"
                title="Manage Staff members and single-use invite links"
              >
                <Users className="w-3.5 h-3.5 text-indigo-600" />
                Team & Access
              </button>
            )}

            {/* User Profile Pill & Logout */}
            <div className="flex items-center pl-2 border-l border-slate-200 gap-2">
              <div className="flex flex-col text-right">
                <span className="text-xs font-bold text-slate-800 leading-tight">
                  {currentUser?.name || 'User'}
                </span>
                <span className={`text-[10px] font-semibold uppercase tracking-wider ${
                  currentUser?.role === 'Admin' ? 'text-indigo-600' : 'text-emerald-600'
                }`}>
                  {currentUser?.role || 'Staff'}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="p-1.5 rounded-lg text-slate-500 hover:text-red-600 hover:bg-slate-100 transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 403 Forbidden Access Alert */}
        {accessForbiddenError && (
          <div className="mb-5 p-4 rounded-xl bg-red-50 border border-red-200 text-red-900 shadow-sm flex items-start justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-red-800">Access Denied (403 Forbidden)</h4>
                <p className="text-xs text-red-700 mt-0.5">{accessForbiddenError}</p>
                <p className="text-[11px] text-red-600 mt-1">
                  Staff accounts can only view statements they uploaded. If you believe this is an error, please contact your Administrator.
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setAccessForbiddenError(null);
                handleConfirmNewCustomer();
              }}
              className="px-3 py-1 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700 transition"
            >
              Clear & Return
            </button>
          </div>
        )}

        {exportStatus && (
          <div className="mb-4 p-3 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 text-xs flex items-center justify-between">
            <span className="font-medium">{exportStatus}</span>
            <button onClick={() => setExportStatus(null)} className="text-blue-500 hover:text-blue-700">Dismiss</button>
          </div>
        )}

        {/* Global Navigation Tabs (Available in both active and empty dashboard states) */}
        <div className="border-b border-slate-200 mb-5 flex items-center justify-between">
          <nav className="flex space-x-6 overflow-x-auto text-xs font-semibold">
            {[
              { id: 'overview', label: 'Overview & Analytics' },
              { id: 'emi', label: `EMI Details (${emis.length})` },
              { id: 'returns', label: `ACH/ECS Returns (${returns.length})` },
              { id: 'abb', label: `Monthly ABB (${monthlyAbb.length})` },
              { id: 'transactions', label: `All Transactions (${totalTxns})` },
              { id: 'review', label: `Review Queue (${reviewItems.length})`, badge: reviewItems.length > 0 },
              { id: 'gst', label: 'GST & PAN Intelligence' },
              { id: 'history', label: `Customer History (${customerHistory.length})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-1 border-b-2 font-semibold transition-colors flex items-center gap-1.5 ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                )}
              </button>
            ))}
          </nav>

          <button
            onClick={() => {
              refreshHistoryAndApps();
              if (selectedAppId) loadAppData(selectedAppId, selectedAccountId);
            }}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100"
            title="Refresh analysis"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* If History tab is selected, render Customer History Table regardless of whether an active customer is loaded */}
        {activeTab === 'history' ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Customer Banking History</h2>
              <p className="text-xs text-slate-500">
                All analyzed customers with turnover, average bank balance, active EMIs, and ACH/ECS bounces. Click any customer row to reload their complete analysis dashboard.
              </p>
            </div>
            <CustomerHistoryTable
              history={customerHistory}
              onSelectCustomer={handleSelectCustomer}
              onExportCustomer={handleExportUnderwriting}
            />
          </div>
        ) : activeTab === 'gst' ? (
          <GstIntelligenceCard
            currentApplicationId={selectedAppId || undefined}
            currentCustomerName={currentApp?.customer_name}
          />
        ) : isDashboardEmpty && !isLoading ? (
          /* Empty State for New Customer */
          <EmptyState onUploadClick={() => navigate('/upload')} />
        ) : (
          <>
            {/* Account Cards Carousel/Grid */}
            {accounts.length > 0 && (
              <div className="mb-5">
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Accounts ({accounts.length})
                  </span>
                  <span className="text-xs text-slate-400">Click any account to filter metrics</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
                  {accounts.map((acc, idx) => (
                    <AccountCard
                      key={idx}
                      account={acc}
                      isSelected={selectedAccountId === acc.account_id}
                      onSelect={() => setSelectedAccountId(acc.account_id)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Parsing Failure / Password Required / Reconciliation Mismatch Banners */}
            {summary && !summary.has_data && (
              <div className="mb-5 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-bold text-rose-900">
                      {summary.parsing_status === 'PASSWORD_REQUIRED'
                        ? 'Statement Password Required'
                        : 'Statement Could Not Be Parsed'}
                    </h4>
                    <p className="text-xs text-rose-800 mt-0.5">
                      {summary.error_message || 'Statement could not be parsed. Please check the PDF password, file quality or statement format.'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/upload')}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shrink-0"
                >
                  {summary.parsing_status === 'PASSWORD_REQUIRED' ? 'Unlock Statement' : 'Re-upload Statement'}
                </button>
              </div>
            )}

            {summary && summary.has_data && summary.reconciliation_status === 'MISMATCH' && (
              <div className="mb-5 p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-950 flex items-start gap-2.5">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <span className="font-bold block text-sm">Balance Reconciliation Warning</span>
                  <span>
                    Opening Balance + Credits − Debits does not match the extracted Closing Balance (difference: ₹{Math.abs(summary.reconciliation_diff || 0).toLocaleString('en-IN')}). Some transactions may be missing or misread — please verify in the Review Queue.
                  </span>
                </div>
              </div>
            )}

            {/* KPI Cards (Only render when verified parsed data exists) */}
            {summary && summary.has_data && (
              <KpiCards
                summary={summary}
                onReviewClick={() => setActiveTab('review')}
              />
            )}

            {/* Tab Contents */}
            <div className="pb-12 pt-4">
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* Verified Banking Metrics vs Underwriting Engine Note */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
                      <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5 mb-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600" />
                        Banking Metrics (Verified from Statements)
                      </h3>
                      <p className="text-xs text-slate-500 mb-3">
                        Turnover, ABB, return counts, and EMI burden are 100% verified from statement transactions with page numbers preserved.
                      </p>
                      <div className="text-xs space-y-1.5 text-slate-700">
                        <div className="flex justify-between">
                          <span>Total Business Turnover:</span>
                          <span className="font-semibold text-slate-900">{summary?.total_business_turnover ? `₹${summary.total_business_turnover.toLocaleString('en-IN')}` : '—'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Internal Transfers Excluded:</span>
                          <span className="font-semibold text-amber-700">{summary?.internal_transfers_excluded ? `₹${summary.internal_transfers_excluded.toLocaleString('en-IN')}` : '—'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Average Monthly ABB:</span>
                          <span className="font-semibold text-slate-900">{summary?.avg_monthly_abb ? `₹${summary.avg_monthly_abb.toLocaleString('en-IN')}` : '—'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Total Negative Days:</span>
                          <span className={`font-semibold ${summary?.total_negative_days && summary.total_negative_days > 0 ? 'text-rose-600' : 'text-slate-900'}`}>
                            {summary?.total_negative_days || 0} days
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
                      <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5 mb-2">
                        <ShieldCheck className="w-4 h-4 text-blue-600" />
                        Underwriting Engine Hand-off
                      </h3>
                      <p className="text-xs text-slate-500 mb-3">
                        This module delivers verified banking facts only. Final credit score, DSCR limit, and loan sanction are computed by downstream Underwriting Rules.
                      </p>
                      <div className="text-xs space-y-1.5 text-slate-700">
                        <div className="flex justify-between">
                          <span>Active Loans Tracked:</span>
                          <span className="font-semibold text-slate-900">{emis.filter(e => e.status === 'ACTIVE').length} loans</span>
                        </div>
                        <div className="flex justify-between">
                          <span>ACH / ECS Bounces:</span>
                          <span className={`font-semibold ${returns.length > 0 ? 'text-rose-600 font-bold' : 'text-slate-900'}`}>
                            {returns.length} bounces
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Review Queue Flagged:</span>
                          <span className={`font-semibold ${reviewItems.length > 0 ? 'text-amber-700 font-bold' : 'text-slate-900'}`}>
                            {reviewItems.length} items
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Current Version:</span>
                          <span className="font-semibold text-slate-900">{history.length > 0 ? `v${history[0].version_no}` : 'v1'}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Monthly ABB and Flow chart preview */}
                  <div>
                    <h3 className="text-sm font-bold text-slate-800 mb-3">Monthly Summary Breakdown</h3>
                    <MonthlyAbbTable data={monthlyAbb} />
                  </div>
                </div>
              )}

              {activeTab === 'emi' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Detected EMIs & Active Loans</h3>
                    <p className="text-xs text-slate-500">
                      Auto-detected recurring mandates with lender recognition, monthly burden, and repayment status.
                    </p>
                  </div>
                  <EmiTable emis={emis} applicationId={selectedAppId} />
                </div>
              )}

              {activeTab === 'returns' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">ACH / ECS Returns & Inward Bounces</h3>
                    <p className="text-xs text-slate-500">
                      Reconciled return records with linked bank penalty charges and recovery status.
                    </p>
                  </div>
                  <ReturnsTable returns={returns} />
                </div>
              )}

              {activeTab === 'abb' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Monthly Average Bank Balance (ABB)</h3>
                    <p className="text-xs text-slate-500">
                      Calculated using running daily EOD balances with carry-forward across non-transaction days.
                    </p>
                  </div>
                  <MonthlyAbbTable data={monthlyAbb} />
                </div>
              )}

              {activeTab === 'transactions' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">All Transactions</h3>
                    <p className="text-xs text-slate-500">
                      Every parsed row preserves original raw narration and source PDF page number.
                    </p>
                  </div>
                  <TransactionsTable
                    transactions={txns}
                    total={totalTxns}
                    page={page}
                    pageSize={25}
                    search={search}
                    channel={channel}
                    category={category}
                    onSearchChange={setSearch}
                    onChannelChange={setChannel}
                    onCategoryChange={setCategory}
                    onPageChange={(p) => refreshTransactions(p)}
                  />
                </div>
              )}

              {activeTab === 'review' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Review Queue & Confidence Auditing</h3>
                    <p className="text-xs text-slate-500">
                      Review ambiguous matches, balance discrepancies, or low-confidence rows. Any manual correction generates a new version.
                    </p>
                  </div>
                  <ReviewQueueTable
                    items={reviewItems}
                    onResolved={() => loadAppData(selectedAppId, selectedAccountId)}
                  />
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
};
