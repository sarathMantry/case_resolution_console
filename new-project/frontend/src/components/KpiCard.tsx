import React from 'react';

type KpiCardProps = {
  title: string;
  value: string | number;
  delta?: string | number;
  hint?: string;
  icon?: React.ReactNode;
};

export default function KpiCard({ title, value, delta, hint, icon }: KpiCardProps) {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm p-6 flex items-start gap-4">
      {icon && (
        <div className="flex-shrink-0 text-primary-500 dark:text-primary-400">
          {icon}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
          {title}
        </div>
        <div className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-1">
          {value}
        </div>
        {delta !== undefined && (
          <div className="text-sm text-slate-500 dark:text-slate-400">
            <span className="font-medium">{delta}</span> vs prev period
          </div>
        )}
        {hint && (
          <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            {hint}
          </div>
        )}
      </div>
    </div>
  );
}
