import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  listUsersApi,
  listInvitesApi,
  createInviteApi,
  deleteUserApi,
  UserProfile,
  InviteItem,
} from '../api/auth';

export const AdminTeam: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [invites, setInvites] = useState<InviteItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Invite Form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successInvite, setSuccessInvite] = useState<{
    invite_url: string;
    email: string;
    name: string;
    expires_at: string;
  } | null>(null);

  const [copied, setCopied] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [u, inv] = await Promise.all([listUsersApi(), listInvitesApi()]);
      setUsers(u);
      setInvites(inv);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch team data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessInvite(null);

    if (!name.trim() || !email.trim()) {
      setError('Please provide member name and valid email.');
      return;
    }

    setCreating(true);
    try {
      const res = await createInviteApi(name.trim(), email.trim());
      // Compute full invite URL
      const fullUrl = `${window.location.origin}/invite/${res.token}`;
      setSuccessInvite({
        invite_url: fullUrl,
        email: res.email,
        name: res.name,
        expires_at: res.expires_at,
      });
      setName('');
      setEmail('');
      loadData();
    } catch (err: any) {
      setError(err.message || 'Could not generate invite link.');
    } finally {
      setCreating(false);
    }
  };

  const handleRemoveUser = async (userId: string, userName: string) => {
    if (!window.confirm(`Are you sure you want to remove ${userName}? They will no longer have access.`)) {
      return;
    }

    try {
      await deleteUserApi(userId);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to remove user');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const staffUsers = users.filter((u) => u.role === 'Staff');
  const staffCount = staffUsers.length;
  const maxStaff = 5;

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* Top Bar */}
      <header className="border-b border-slate-800 bg-slate-900/90 sticky top-0 z-30 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow">
            BSI
          </div>
          <div>
            <h1 className="text-base font-semibold leading-none">Team & Staff Access Control</h1>
            <p className="text-xs text-slate-400 mt-1">Admin Panel — Restrict & manage internal staff access</p>
          </div>
        </div>

        <button
          onClick={() => navigate('/')}
          className="px-3.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
        >
          &larr; Back to Dashboard
        </button>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Quota & Overview Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Staff Slots</p>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-3xl font-extrabold text-white">{staffCount}</span>
              <span className="text-sm text-slate-400">/ {maxStaff} Allowed</span>
            </div>
            <div className="w-full bg-slate-700 h-2 rounded-full mt-3 overflow-hidden">
              <div
                className={`h-full ${staffCount >= maxStaff ? 'bg-amber-500' : 'bg-indigo-500'}`}
                style={{ width: `${(staffCount / maxStaff) * 100}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-2">
              {maxStaff - staffCount} staff slot(s) remaining. Public signup is permanently disabled.
            </p>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Owner / Administrator</p>
            <p className="text-lg font-bold text-white mt-2">Rishab (Admin)</p>
            <p className="text-xs text-indigo-400 font-mono mt-0.5">rajesh.y7867@gmail.com</p>
            <p className="text-xs text-slate-400 mt-2">Full access to view all staff customer applications & audit history.</p>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Security Rule</p>
            <p className="text-sm font-semibold text-emerald-400 mt-2">Isolated Staff Workspaces</p>
            <p className="text-xs text-slate-400 mt-1">
              Staff only see their own uploaded customers. Accessing other staff customer IDs returns 403 Forbidden.
            </p>
          </div>
        </div>

        {/* Generate Invite Section */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-semibold text-white">Generate Staff Invite Link</h2>
          <p className="text-xs text-slate-400 mt-1">
            Create a secure, 24-hour single-use activation link for a new staff member.
          </p>

          {error && (
            <div className="mt-4 rounded-lg bg-red-900/30 border border-red-700/50 p-3 text-xs text-red-300">
              {error}
            </div>
          )}

          {successInvite && (
            <div className="mt-4 rounded-lg bg-emerald-950/40 border border-emerald-600/50 p-4">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Invite Link Created Successfully for {successInvite.name} ({successInvite.email})
              </div>
              <p className="text-xs text-slate-300 mt-1">
                Link expires in 24 hours and can be used once to set up password.
              </p>

              <div className="mt-3 flex flex-col sm:flex-row gap-2 items-stretch">
                <input
                  type="text"
                  readOnly
                  value={successInvite.invite_url}
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-emerald-300 select-all"
                />
                <button
                  type="button"
                  onClick={() => copyToClipboard(successInvite.invite_url)}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                >
                  {copied ? 'Copied!' : 'Copy Link'}
                </button>
                <a
                  href={`https://api.whatsapp.com/send?text=${encodeURIComponent(
                    `Hi ${successInvite.name}, here is your single-use invite link to access the Bank Statement Intelligence portal: ${successInvite.invite_url} (Expires in 24 hours)`
                  )}`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                >
                  Share to WhatsApp
                </a>
              </div>
            </div>
          )}

          <form className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4" onSubmit={handleCreateInvite}>
            <div>
              <label className="block text-xs font-medium text-slate-300">Staff Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Rahul Sharma"
                disabled={staffCount >= maxStaff || creating}
                className="mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300">Staff Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. rahul@company.com"
                disabled={staffCount >= maxStaff || creating}
                className="mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              />
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={staffCount >= maxStaff || creating}
                className="w-full h-[38px] px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? 'Generating Link...' : staffCount >= maxStaff ? 'Staff Limit Reached (5/5)' : '+ Generate 24hr Invite Link'}
              </button>
            </div>
          </form>
        </div>

        {/* Active Staff Members Table */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-slate-700/80 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">Active Team Members ({users.length})</h2>
              <p className="text-xs text-slate-400 mt-0.5">Staff users with authorized login credentials</p>
            </div>
            <button
              onClick={loadData}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition"
            >
              Refresh
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/60 text-slate-400 font-semibold uppercase border-b border-slate-700/60">
                <tr>
                  <th className="px-6 py-3">Member</th>
                  <th className="px-6 py-3">Email</th>
                  <th className="px-6 py-3">Role</th>
                  <th className="px-6 py-3">Applications</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-750/50">
                    <td className="px-6 py-3.5 font-medium text-white flex items-center gap-2.5">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${u.role === 'Admin' ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-200'}`}>
                        {u.name.charAt(0).toUpperCase()}
                      </div>
                      <span>{u.name}</span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-300 font-mono text-[11px]">{u.email}</td>
                    <td className="px-6 py-3.5">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                          u.role === 'Admin'
                            ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-300">
                      {u.customers_count || 0} customer(s)
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      {u.role === 'Staff' ? (
                        <button
                          onClick={() => handleRemoveUser(u.id, u.name)}
                          className="text-red-400 hover:text-red-300 text-xs font-medium hover:underline"
                        >
                          Remove
                        </button>
                      ) : (
                        <span className="text-slate-500 text-xs italic">Owner</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pending Invites List */}
        {invites.length > 0 && (
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-700/80">
              <h2 className="text-sm font-semibold text-white">Pending & Recent Invites</h2>
              <p className="text-xs text-slate-400 mt-0.5">24-hour single-use activation links</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/60 text-slate-400 font-semibold uppercase border-b border-slate-700/60">
                  <tr>
                    <th className="px-6 py-3">Invited Member</th>
                    <th className="px-6 py-3">Email</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Expires At</th>
                    <th className="px-6 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {invites.map((inv) => {
                    const isPending = inv.status === 'PENDING';
                    const link = `${window.location.origin}/invite/${inv.token}`;
                    return (
                      <tr key={inv.id} className="hover:bg-slate-750/50">
                        <td className="px-6 py-3 text-white font-medium">{inv.name}</td>
                        <td className="px-6 py-3 text-slate-300 font-mono text-[11px]">{inv.email}</td>
                        <td className="px-6 py-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                              inv.status === 'ACCEPTED'
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : inv.status === 'EXPIRED'
                                ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                                : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            }`}
                          >
                            {inv.status}
                          </span>
                        </td>
                        <td className="px-6 py-3 text-slate-400 text-[11px]">
                          {new Date(inv.expires_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-3 text-right">
                          {isPending && (
                            <button
                              onClick={() => copyToClipboard(link)}
                              className="text-indigo-400 hover:text-indigo-300 text-xs font-medium hover:underline"
                            >
                              Copy Link
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
