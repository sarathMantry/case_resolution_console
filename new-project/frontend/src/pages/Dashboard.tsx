import React, { useEffect, useState } from 'react';
import KpiCard from '../components/KpiCard';

type KPIs = {
  alertsInQueue: number;
  disputesOpened: number;
  avgTriageLatencyMs: number;
};

const sampleKpis: KPIs = {
  alertsInQueue: 12,
  disputesOpened: 4,
  avgTriageLatencyMs: 420,
};

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000';

export default function Dashboard() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const fetchKpis = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/dashboard/kpis`);
        if (!res.ok) throw new Error(`Status ${res.status}`);
        const data = await res.json();
        if (mounted) setKpis(data);
      } catch (err) {
        // Fallback to sample data when backend endpoint is not available
        if (mounted) {
          setError('Using sample KPIs (backend unreachable)');
          setKpis(sampleKpis);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchKpis();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Dashboard
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Overview of operational KPIs and case resolution metrics
          </p>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-amber-700 dark:text-amber-300">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <section className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-8">
          <KpiCard
            title="Alerts in Queue"
            value={loading ? '—' : (kpis?.alertsInQueue ?? '—')}
            delta="+3%"
            hint="Alerts awaiting triage"
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            }
          />
          <KpiCard
            title="Disputes Opened"
            value={loading ? '—' : (kpis?.disputesOpened ?? '—')}
            delta="-1"
            hint="Open dispute cases"
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            }
          />
          <KpiCard
            title="Avg Triage Latency"
            value={loading ? '—' : (kpis?.avgTriageLatencyMs ? `${kpis.avgTriageLatencyMs}ms` : '—')}
            delta="p95: 820ms"
            hint="Average time to resolve a triage run"
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            }
          />
        </section>

        {/* Quick Filters */}
        <section className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Quick Filters
          </h2>
          <div className="flex flex-wrap gap-3">
            <button className="px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors text-sm font-medium">
              High Risk
            </button>
            <button className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors text-sm font-medium">
              Last 24h
            </button>
            <button className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors text-sm font-medium">
              Untriaged
            </button>
            <button className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors text-sm font-medium">
              Pending OTP
            </button>
            <button className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors text-sm font-medium">
              Open Disputes
            </button>
          </div>
        </section>

        {/* Recent Activity */}
        <section className="mt-8 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            Recent Activity
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
              <div className="flex-shrink-0 w-2 h-2 rounded-full bg-red-500"></div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  High-risk alert generated
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Customer #1234 • Unusual transaction pattern
                </p>
              </div>
              <div className="text-xs text-slate-400">2m ago</div>
            </div>
            <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
              <div className="flex-shrink-0 w-2 h-2 rounded-full bg-amber-500"></div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  Dispute case opened
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Case #5678 • Unrecognized charge
                </p>
              </div>
              <div className="text-xs text-slate-400">15m ago</div>
            </div>
            <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
              <div className="flex-shrink-0 w-2 h-2 rounded-full bg-green-500"></div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  Card frozen successfully
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Card ending ****4532
                </p>
              </div>
              <div className="text-xs text-slate-400">1h ago</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
