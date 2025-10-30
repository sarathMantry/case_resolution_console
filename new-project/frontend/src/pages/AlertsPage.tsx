import React from 'react';
import { TriageDrawer } from '../components/TriageDrawer';

interface AlertItem {
  id: string;
  status: string;
  risk: string;
  created_at: string;
  suspect_txn_id: string | null;
  customer_id: string;
}

const AlertRow: React.FC<{ alert: AlertItem; onOpenTriage: (id: string) => void }> = ({ 
  alert, 
  onOpenTriage 
}) => {
  const getRiskColor = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case 'HIGH':
        return 'bg-red-500';
      case 'MEDIUM':
        return 'bg-orange-500';
      case 'LOW':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'OPEN':
        return 'bg-blue-100 text-blue-800';
      case 'IN_REVIEW':
        return 'bg-purple-100 text-purple-800';
      case 'CLOSED':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors duration-150 border-b border-gray-100">
      <div className="flex-1">
        <div className="flex items-center space-x-4">
          <div className={`w-2 h-2 rounded-full ${getRiskColor(alert.risk)}`} />
          <div>
            <p className="text-sm font-medium text-gray-900">
              Alert ID: {alert.id.substring(0, 8)}...
            </p>
            <p className="text-xs text-gray-500">
              Customer: {alert.customer_id.substring(0, 8)}... • Risk: {alert.risk}
            </p>
          </div>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
          {alert.status.replace('_', ' ')}
        </span>
        <span className="text-xs text-gray-500">{new Date(alert.created_at).toLocaleDateString()}</span>
        <button
          onClick={() => onOpenTriage(alert.id)}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 
                     font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none 
                     focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Triage →
        </button>
      </div>
    </div>
  );
};

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = React.useState<AlertItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [selectedAlertId, setSelectedAlertId] = React.useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [statusFilter, setStatusFilter] = React.useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = React.useState<string>('ALL');

  React.useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:3000/api/alerts');
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenTriage = (alertId: string) => {
    setSelectedAlertId(alertId);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setSelectedAlertId(null);
    // Refresh alerts after drawer closes
    fetchAlerts();
  };

  const filteredAlerts = alerts.filter(alert => {
    if (statusFilter !== 'ALL' && alert.status !== statusFilter) return false;
    if (severityFilter !== 'ALL' && alert.risk !== severityFilter) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Alert Queue</h1>
        <p className="text-gray-500">Review and triage suspicious activities</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center space-x-4">
        <select 
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none 
                    focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md border"
        >
          <option value="ALL">All Severities</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select 
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none 
                    focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md border"
        >
          <option value="ALL">All Status</option>
          <option value="OPEN">Open</option>
          <option value="IN_REVIEW">In Review</option>
          <option value="CLOSED">Closed</option>
        </select>

        <div className="flex-1" />

        <button
          onClick={fetchAlerts}
          className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Refresh
        </button>

        <div className="text-sm text-gray-500">
          Showing {filteredAlerts.length} of {alerts.length} alerts
        </div>
      </div>

      {/* Alert List */}
      {filteredAlerts.length === 0 ? (
        <div className="border border-gray-200 rounded-lg shadow bg-white p-12 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No alerts found</h3>
          <p className="mt-1 text-sm text-gray-500">Try adjusting your filters</p>
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg shadow bg-white overflow-auto">
          {filteredAlerts.map((alert) => (
            <AlertRow
              key={alert.id}
              alert={alert}
              onOpenTriage={handleOpenTriage}
            />
          ))}
        </div>
      )}

      <TriageDrawer
        isOpen={drawerOpen}
        onClose={handleCloseDrawer}
        alertId={selectedAlertId}
      />
    </div>
  );
};