import React, { useState, useEffect } from 'react';
import { UploadDropzone } from '../components/UploadDropzone';
import { getSupportedBanks } from '../api/statements';
import { ArrowLeft, CheckCircle2, Clock, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [banks, setBanks] = useState<any[]>([]);

  useEffect(() => {
    getSupportedBanks()
      .then((data) => setBanks(data))
      .catch((e) => console.error("Error fetching supported banks", e));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Back Link */}
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>

        {/* Upload Component */}
        <UploadDropzone onUploadSuccess={() => {}} />

        {/* Bank Support Matrix */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                Bank Format Support Matrix
              </h3>
              <p className="text-xs text-slate-500">
                Phase 1 banks verified with real statement test cases. Phase 2 currently undergoing format validation.
              </p>
            </div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              No generic claims
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {banks.map((b, idx) => (
              <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50 flex items-center justify-between text-xs">
                <div>
                  <span className="font-semibold text-slate-800 block">{b.name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">Phase {b.phase} • {b.code}</span>
                </div>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                  b.status === 'Verified' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                }`}>
                  {b.status === 'Verified' ? <CheckCircle2 className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                  {b.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

