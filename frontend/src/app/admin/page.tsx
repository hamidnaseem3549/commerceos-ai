"use client";

import { useState, useEffect } from "react";
import { getAdminStats, getAdminAlerts, getAdminLogs, getAgents, runFraudSweep, runPricingAnalysis, getLowStockProducts, type AdminStats } from "@/lib/api";

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [agents, setAgents] = useState<string[]>([]);
  const [sweeping, setSweeping] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [sweepResult, setSweepResult] = useState<any>(null);
  const [auth, setAuth] = useState({ password: "", authed: false });

  useEffect(() => {
    if (!auth.authed) return;
    getAdminStats().then(setStats);
    getAdminAlerts(10).then(({ alerts }) => setAlerts(alerts));
    getAdminLogs(20).then(({ logs }) => setLogs(logs));
    getAgents().then(({ agents }) => setAgents(agents));
  }, [auth.authed]);

  if (!auth.authed) {
    return (
      <div className="max-w-sm mx-auto mt-20 text-center">
        <div className="text-5xl mb-6">⚙️</div>
        <h1 className="text-2xl font-bold text-dark-100 mb-4">Admin Dashboard</h1>
        <input
          type="password"
          placeholder="Password"
          value={auth.password}
          onChange={(e) => setAuth({ ...auth, password: e.target.value })}
          className="input-field mb-3"
          onKeyDown={(e) => e.key === "Enter" && auth.password === "admin123" && setAuth({ ...auth, authed: true })}
        />
        <button
          onClick={() => auth.password === "admin123" && setAuth({ ...auth, authed: true })}
          className="btn-primary w-full"
        >
          Unlock
        </button>
        <p className="text-xs text-gray-400 mt-3">Default: admin123</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-dark-100">⚙️ Operations Dashboard</h1>
        <p className="text-gray-500">Real-time system overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Orders", value: stats?.total_orders || 0, color: "from-blue-500 to-blue-600" },
          { label: "Pending", value: stats?.pending_orders || 0, color: "from-yellow-500 to-orange-500" },
          { label: "Low Stock", value: stats?.low_stock_items || 0, color: "from-red-500 to-red-600" },
          { label: "Fraud Alerts", value: stats?.fraud_alerts || 0, color: "from-purple-500 to-purple-600" },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass-card !p-6">
            <p className="text-sm text-gray-500 mb-1">{label}</p>
            <p className={`text-3xl font-bold bg-gradient-to-r ${color} text-transparent bg-clip-text`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Agents */}
      <div className="glass-card !p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-3">🤖 Active Agents</h2>
        <div className="flex gap-2 flex-wrap">
          {agents.map((a) => (
            <span key={a} className="px-4 py-2 rounded-xl bg-gray-100 text-sm font-medium text-gray-700">
              {a}
            </span>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="glass-card !p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">⚡ Quick Actions</h2>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={async () => { setSweeping(true); const r = await runFraudSweep(); setSweepResult(r); setSweeping(false); }}
            disabled={sweeping}
            className="btn-secondary"
          >
            {sweeping ? "Scanning..." : "🔍 Run Fraud Sweep"}
          </button>
          <button
            onClick={async () => { setAnalyzing(true); const r = await runPricingAnalysis(); setSweepResult(r); setAnalyzing(false); }}
            disabled={analyzing}
            className="btn-secondary"
          >
            {analyzing ? "Analyzing..." : "🏷️ Analyze Pricing"}
          </button>
        </div>
        {sweepResult && (
          <div className="mt-4 p-4 bg-gray-50 rounded-xl text-sm">
            <pre className="text-gray-600">{JSON.stringify(sweepResult, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Alerts */}
      <div className="glass-card !p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">🚨 Recent Alerts</h2>
        {alerts.length === 0 ? (
          <p className="text-gray-400 text-sm">No alerts</p>
        ) : (
          <div className="space-y-2">
            {alerts.slice(0, 5).map((a, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-gray-50 text-sm">
                <span className={`mt-0.5 ${a.severity === "HIGH" ? "text-red-500" : "text-yellow-500"}`}>
                  {a.severity === "HIGH" ? "🔴" : "🟡"}
                </span>
                <div>
                  <p className="text-gray-700">{a.message}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{a.source} — {a.created_at}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Activity Log */}
      <div className="glass-card !p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">📋 Agent Activity</h2>
        <div className="space-y-1 max-h-60 overflow-y-auto">
          {logs.map((l, i) => (
            <div key={i} className="flex gap-3 text-sm py-1.5 border-b border-gray-50 last:border-0">
              <span className="text-gray-400 w-16 shrink-0 text-xs">{l.timestamp?.split(" ")[1]?.slice(0, 5) || ""}</span>
              <span className="font-medium text-gray-700 w-20 shrink-0">{l.agent}</span>
              <span className="text-gray-500">{l.action}</span>
              <span className="text-gray-400 truncate">{l.detail?.slice(0, 80)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
