import React from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';

interface AlertItem {
  id: string;
  customerId: string;
  riskScore: number;
  status: string;
  createdAt: string;
  description: string;
}

const AlertRow: React.FC<{ alert: AlertItem; onOpenTriage: (id: string) => void }> = ({ 
  alert, 
  onOpenTriage 
}) => (
  <div className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors duration-150">
    <div className="flex-1">
      <div className="flex items-center space-x-4">
        <div className={`
          w-2 h-2 rounded-full
          ${alert.riskScore >= 0.7 ? 'bg-red-500' : 
            alert.riskScore >= 0.4 ? 'bg-yellow-500' : 'bg-green-500'}
        `} />
        <div>
          <p className="text-sm font-medium text-gray-900">
            Customer #{alert.customerId}
          </p>
          <p className="text-sm text-gray-500">
            {alert.description}
          </p>
        </div>
      </div>
    </div>
    <div className="flex items-center space-x-4">
      <div className="text-sm text-gray-500">
        Risk Score: {(alert.riskScore * 100).toFixed(0)}%
      </div>
      <button
        onClick={() => onOpenTriage(alert.id)}
        className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 
                   font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none 
                   focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Open Triage
      </button>
    </div>
  </div>
);

export const AlertsPage: React.FC = () => {
  const [alerts] = React.useState<AlertItem[]>(() => 
    Array.from({ length: 1000 }, (_, i) => ({
      id: `alert-${i}`,
      customerId: `CUST-${Math.floor(Math.random() * 10000)}`,
      riskScore: Math.random(),
      status: Math.random() > 0.5 ? 'NEW' : 'IN_PROGRESS',
      createdAt: new Date(Date.now() - Math.random() * 86400000 * 30).toISOString(),
      description: 'Suspicious transaction pattern detected'
    }))
  );

  const parentRef = React.useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: alerts.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 82, // Approximate height of each row
    overscan: 5
  });

  const handleOpenTriage = (alertId: string) => {
    console.log('Opening triage for alert:', alertId);
    // TODO: Implement triage drawer opening logic
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Alert Queue</h1>
        <p className="text-gray-500">Review and triage suspicious activities</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center space-x-4">
        <select className="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none 
                          focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
          <option>All Risk Levels</option>
          <option>High Risk</option>
          <option>Medium Risk</option>
          <option>Low Risk</option>
        </select>

        <select className="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none 
                          focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
          <option>All Status</option>
          <option>New</option>
          <option>In Progress</option>
          <option>Resolved</option>
        </select>

        <div className="flex-1" />

        <div className="text-sm text-gray-500">
          Showing {alerts.length} alerts
        </div>
      </div>

      {/* Virtualized Alert List */}
      <div
        ref={parentRef}
        className="border border-gray-200 rounded-lg shadow bg-white overflow-auto"
        style={{ height: 'calc(100vh - 250px)' }}
      >
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative'
          }}
        >
          {virtualizer.getVirtualItems().map((virtualRow) => (
            <div
              key={virtualRow.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`
              }}
            >
              <AlertRow
                alert={alerts[virtualRow.index]}
                onOpenTriage={handleOpenTriage}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};