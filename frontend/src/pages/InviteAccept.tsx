import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getInviteDetailsApi, acceptInviteApi } from '../api/auth';

export const InviteAccept: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [invite, setInvite] = useState<{ email: string; name: string; role: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    if (!token) {
      setError('Invalid invite link.');
      setLoading(false);
      return;
    }

    getInviteDetailsApi(token)
      .then((data) => {
        setInvite(data);
      })
      .catch((err) => {
        setError(err.message || 'This invite link is invalid, expired, or has already been used.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await acceptInviteApi(token!, password);
      localStorage.setItem('auth_token', res.access_token);
      localStorage.setItem('auth_user', JSON.stringify(res.user));
      navigate('/', { replace: true });
    } catch (err: any) {
      setError(err.message || 'Failed to activate account. The link may have expired.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-12 h-12 rounded-xl bg-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
        </div>
        <h2 className="mt-4 text-center text-2xl font-bold tracking-tight text-white">
          Activate Your Staff Account
        </h2>
        <p className="mt-1 text-center text-sm text-slate-400">
          Set up your password to begin analyzing bank statements
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800 py-8 px-6 shadow-xl border border-slate-700/60 rounded-xl sm:px-10">
          {loading && (
            <div className="text-center py-8 text-slate-400 text-sm">
              Verifying invite link...
            </div>
          )}

          {error && (
            <div className="mb-5 rounded-lg bg-red-900/30 border border-red-700/50 p-3.5 text-sm text-red-300 flex items-start gap-2">
              <svg className="w-5 h-5 flex-shrink-0 text-red-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-semibold">Activation Failed</p>
                <p className="text-xs text-red-300 mt-0.5">{error}</p>
                <button
                  onClick={() => navigate('/login')}
                  className="mt-3 text-xs underline font-medium text-red-200 hover:text-white"
                >
                  Return to Login
                </button>
              </div>
            </div>
          )}

          {!loading && invite && (
            <div>
              <div className="mb-6 rounded-lg bg-slate-900/60 border border-slate-700/60 p-4">
                <p className="text-xs text-slate-400">Invited Member</p>
                <p className="text-base font-semibold text-white mt-0.5">{invite.name}</p>
                <p className="text-xs text-slate-400">{invite.email}</p>
                <span className="inline-block mt-2 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  Role: {invite.role}
                </span>
              </div>

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Create Password
                  </label>
                  <div className="mt-1.5">
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Minimum 6 characters"
                      className="block w-full rounded-lg border border-slate-600 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Confirm Password
                  </label>
                  <div className="mt-1.5">
                    <input
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter password"
                      className="block w-full rounded-lg border border-slate-600 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {submitting ? 'Activating Account...' : 'Set Password & Enter Dashboard'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
