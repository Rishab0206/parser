import React, { useState } from 'react';
import { Search, ShieldAlert, ShieldCheck, CheckCircle2, AlertTriangle, Copy, Check, Building2, UserCheck, ExternalLink, MapPin } from 'lucide-react';
import { lookupGstOrPan, GstLookupResponse } from '../api/gst';

interface GstIntelligenceCardProps {
  currentApplicationId?: string;
  currentCustomerName?: string;
}

export const GstIntelligenceCard: React.FC<GstIntelligenceCardProps> = ({
  currentApplicationId,
  currentCustomerName,
}) => {
  const [query, setQuery] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<GstLookupResponse | null>(null);
  const [copiedGstin, setCopiedGstin] = useState<string | null>(null);
  const [copiedPan, setCopiedPan] = useState(false);

  const handleSearch = async (e?: React.FormEvent, stateOverride?: string) => {
    if (e) e.preventDefault();
    const q = query.trim().toUpperCase();
    if (!q) {
      setError('Please enter a 10-digit PAN or 15-digit GSTIN.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const stateToUse = stateOverride !== undefined ? stateOverride : selectedState;
      const res = await lookupGstOrPan(q, currentApplicationId, currentCustomerName, stateToUse || undefined);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to verify PAN/GSTIN. Please check the format.');
    } finally {
      setLoading(false);
    }
  };

  const handleStateChange = (stateCode: string) => {
    setSelectedState(stateCode);
    if (data && data.input_type === 'PAN') {
      handleSearch(undefined, stateCode);
    }
  };

  const copyToClipboard = (text: string, isPan = false) => {
    navigator.clipboard.writeText(text);
    if (isPan) {
      setCopiedPan(true);
      setTimeout(() => setCopiedPan(false), 2000);
    } else {
      setCopiedGstin(text);
      setTimeout(() => setCopiedGstin(null), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Header Box */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-600" />
              GST & PAN Verification Intelligence
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Verify PAN legal entity type, calculate Luhn Mod-36 checksum, and check state-specific GST registration
            </p>
          </div>
          {currentCustomerName && (
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-100 text-xs text-indigo-700">
              <UserCheck className="w-3.5 h-3.5" />
              <span>Current Applicant: <strong className="font-semibold">{currentCustomerName}</strong></span>
            </div>
          )}
        </div>

        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2.5">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value.toUpperCase())}
              placeholder="Enter 10-digit PAN (e.g. AJJPY0658E) or 15-digit GSTIN (e.g. 24AJJPY0658E1Z1)"
              className="w-full uppercase font-mono tracking-wider pl-3.5 pr-10 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-semibold text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition"
            />
            <span className="absolute right-3 top-2.5 text-[10px] font-mono text-slate-400 font-bold uppercase">
              {query.length}/15
            </span>
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center justify-center gap-1.5 transition cursor-pointer"
          >
            {loading ? (
              <span>Analyzing...</span>
            ) : (
              <>
                <Search className="w-3.5 h-3.5" />
                <span>Verify & Check</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Analysis Results Display */}
      {data && (
        <div className="space-y-6">
          {/* Key Intelligence Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Entity Classification */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Business Constitution
              </span>
              <p className="text-sm font-bold text-slate-900 mt-1 leading-snug">
                {data.entity_type}
              </p>
              <div className="mt-2 flex items-center gap-1.5">
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-100 text-indigo-800">
                  Code: '{data.entity_code}'
                </span>
                <span className="text-[11px] text-slate-500">
                  {data.entity_code === 'P' ? 'Proprietor' : data.entity_code === 'C' ? 'Corporate' : 'Firm'}
                </span>
              </div>
            </div>

            {/* PAN Identification */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Permanent Account Number
              </span>
              <p className="text-base font-extrabold font-mono text-slate-900 mt-1 tracking-wider">
                {data.pan}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">
                Surname Initial: <strong className="font-mono text-slate-800">'{data.name_initial}'</strong>
              </p>
            </div>

            {/* Verification Status */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Verification Mode
              </span>
              <div className="mt-1 flex items-center gap-2">
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  {data.input_type === 'GSTIN' ? '15-DIGIT GSTIN' : '10-DIGIT PAN'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1.5">
                {data.input_type === 'GSTIN' ? 'Specific State Registration' : 'Valid Legal Identity'}
              </p>
            </div>

            {/* Official GST Portal Link */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Official GST Portal Check
                </span>
                <p className="text-xs text-slate-600 mt-1">
                  Verify government records for PAN <strong className="font-mono">{data.pan}</strong>
                </p>
              </div>
              <a
                href={data.gov_search_url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
              >
                <span>Search by PAN on GST Portal</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* If Search was by PAN: State Selection Box (To avoid showing false states) */}
          {data.input_type === 'PAN' && (
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-indigo-600" />
                    Verify State GSTIN for this PAN
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    An individual or company only registers GST in states where they conduct business. Select your state to calculate and verify the exact 15-digit GSTIN:
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 items-center">
                <select
                  value={selectedState}
                  onChange={(e) => handleStateChange(e.target.value)}
                  className="w-full sm:w-80 px-3.5 py-2 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:border-indigo-600"
                >
                  <option value="">-- Select Your Business State --</option>
                  {data.all_states &&
                    Object.entries(data.all_states).map(([code, name]) => (
                      <option key={code} value={code}>
                        {name} ({code})
                      </option>
                    ))}
                </select>

                <button
                  type="button"
                  onClick={() => copyToClipboard(data.pan, true)}
                  className="px-3.5 py-2 bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  {copiedPan ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-700">PAN Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-slate-500" />
                      <span>Copy PAN for GST Portal</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* GSTIN Details (Only shows when an actual GSTIN was queried or a state was selected) */}
          {data.gstins.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                    {data.input_type === 'GSTIN' ? 'GSTIN Registration Details' : `Calculated GSTIN for Selected State`}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    15-character alphanumeric format with Luhn Mod-36 checksum verification
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 font-semibold uppercase border-b border-slate-200">
                    <tr>
                      <th className="px-6 py-3">State / Jurisdiction</th>
                      <th className="px-6 py-3">15-Digit GSTIN</th>
                      <th className="px-6 py-3">Entity No.</th>
                      <th className="px-6 py-3">Luhn Checksum</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.gstins.map((g, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-6 py-3.5 font-medium text-slate-800">
                          {g.state_name} <span className="font-mono text-slate-400 text-[10px]">({g.state_code})</span>
                        </td>
                        <td className="px-6 py-3.5 font-mono font-bold text-slate-900 tracking-wider">
                          {g.gstin}
                        </td>
                        <td className="px-6 py-3.5 font-mono text-slate-600">
                          {g.entity_number}
                        </td>
                        <td className="px-6 py-3.5">
                          <span
                            className={`inline-flex items-center gap-1 text-[11px] font-semibold ${
                              g.checksum_valid ? 'text-emerald-700' : 'text-red-600'
                            }`}
                          >
                            {g.checksum_valid ? <Check className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                            {g.checksum_valid ? 'Valid Checksum' : 'Invalid Checksum'}
                          </span>
                        </td>
                        <td className="px-6 py-3.5">
                          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            {g.status}
                          </span>
                        </td>
                        <td className="px-6 py-3.5 text-right">
                          <button
                            onClick={() => copyToClipboard(g.gstin)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-slate-200 hover:bg-slate-100 text-[11px] font-semibold text-slate-700 transition"
                          >
                            {copiedGstin === g.gstin ? (
                              <>
                                <Check className="w-3 h-3 text-emerald-600" />
                                <span className="text-emerald-700">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3 text-slate-500" />
                                <span>Copy GSTIN</span>
                              </>
                            )}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Cross-Verification & Underwriting Observations */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Underwriter Cross-Verification Report
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100 space-y-1">
                <span className="text-[11px] text-slate-500 font-medium">Bank Statement Customer Name</span>
                <p className="text-sm font-bold text-slate-900">{data.matching.customer_name}</p>
                <span className="text-[10px] text-slate-400">Extracted from statement header / application record</span>
              </div>

              <div className="p-3.5 rounded-lg bg-indigo-50/60 border border-indigo-100 space-y-1">
                <span className="text-[11px] text-indigo-700 font-semibold">Credit Recommendation</span>
                <p className="text-xs text-indigo-950 font-medium leading-relaxed">
                  {data.matching.underwriting_recommendation}
                </p>
              </div>
            </div>

            {/* Observations List */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <span className="text-xs font-semibold text-slate-700">Verification Checks & Observations:</span>
              <div className="space-y-1.5">
                {data.matching.observations.map((obs, idx) => (
                  <div
                    key={idx}
                    className={`p-2.5 rounded-lg text-xs flex items-start gap-2 ${
                      obs.startsWith('Mismatch')
                        ? 'bg-red-50 text-red-800 border border-red-200'
                        : obs.startsWith('Notice')
                        ? 'bg-amber-50 text-amber-800 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-800 border border-emerald-100'
                    }`}
                  >
                    {obs.startsWith('Mismatch') ? (
                      <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    )}
                    <span>{obs}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
