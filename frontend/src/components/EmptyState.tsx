import React from 'react';
import { UploadCloud, FileText, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface EmptyStateProps {
  onUploadClick?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onUploadClick }) => {
  const navigate = useNavigate();

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-12 text-center max-w-2xl mx-auto shadow-sm my-8">
      <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-5">
        <UploadCloud className="w-8 h-8" />
      </div>
      <h3 className="text-xl font-bold text-slate-800 mb-2">No Statement Uploaded Yet</h3>
      <p className="text-slate-500 mb-6 text-sm max-w-md mx-auto">
        Upload your first bank statement (PDF, scanned PDF, Excel, or CSV) to verify banking turnover, compute ABB, and detect recurring EMIs.
      </p>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <button
          onClick={onUploadClick || (() => navigate('/upload'))}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm transition-colors shadow-sm"
        >
          <UploadCloud className="w-4 h-4" />
          Upload Bank Statement
        </button>
        <button
          onClick={() => navigate('/upload')}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium text-sm transition-colors"
        >
          <FileText className="w-4 h-4 text-slate-400" />
          Supported Banks List
        </button>
      </div>
    </div>
  );
};

