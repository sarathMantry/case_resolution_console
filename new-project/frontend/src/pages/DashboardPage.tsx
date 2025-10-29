import React from 'react';
import { Card } from '../components/common/Card';

interface KPICardProps {
  title: string;
  value: string | number;
  trend?: number;
  icon?: React.ReactNode;
}

const KPICard: React.FC<KPICardProps> = ({ title, value, trend, icon }) => (
  <Card className="flex flex-col p-6 space-y-2">
    <div className="flex items-center justify-between">
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      {icon && <span className="text-gray-400">{icon}</span>}
    </div>
    <div className="flex items-end justify-between">
      <p className="text-2xl font-semibold text-gray-900">{value}</p>
      {trend !== undefined && (
        <span className={`flex items-center ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
        </span>
      )}
    </div>
  </Card>
);

interface QuickFilterProps {
  label: string;
  count: number;
  selected?: boolean;
  onClick: () => void;
}

const QuickFilter: React.FC<QuickFilterProps> = ({ label, count, selected, onClick }) => (
  <button
    onClick={onClick}
    className={`inline-flex items-center px-4 py-2 rounded-full text-sm
      ${selected 
        ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      } transition-colors duration-150 ease-in-out`}
  >
    {label}
    <span className="ml-2 text-xs font-medium">
      {count}
    </span>
  </button>
);

export const DashboardPage: React.FC = () => {
  const [selectedFilter, setSelectedFilter] = React.useState<string>('all');

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-500">Overview of case resolution metrics and alerts</p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          title="Alerts in Queue"
          value={42}
          trend={5}
        />
        <KPICard
          title="Disputes Opened Today"
          value={8}
          trend={-2}
        />
        <KPICard
          title="Avg Triage Latency"
          value="1.2s"
          trend={-15}
        />
        <KPICard
          title="Resolution Rate"
          value="94%"
          trend={3}
        />
      </div>

      {/* Quick Filters */}
      <div className="mb-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Filters</h2>
        <div className="flex flex-wrap gap-3">
          <QuickFilter
            label="All Alerts"
            count={156}
            selected={selectedFilter === 'all'}
            onClick={() => setSelectedFilter('all')}
          />
          <QuickFilter
            label="High Risk"
            count={23}
            selected={selectedFilter === 'high'}
            onClick={() => setSelectedFilter('high')}
          />
          <QuickFilter
            label="Pending OTP"
            count={12}
            selected={selectedFilter === 'otp'}
            onClick={() => setSelectedFilter('otp')}
          />
          <QuickFilter
            label="Needs Review"
            count={45}
            selected={selectedFilter === 'review'}
            onClick={() => setSelectedFilter('review')}
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h2>
        <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
          {[1, 2, 3, 4, 5].map((item) => (
            <div key={item} className="p-4 hover:bg-gray-50 transition-colors duration-150 cursor-pointer">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Card Frozen - Transaction Suspicious
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    Customer ID: #1234{item}
                  </p>
                </div>
                <span className="text-xs text-gray-500">
                  {item}m ago
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};