import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import { AlertsPage } from './pages/AlertsPage';
import { CustomerPage } from './pages/CustomerPage';
import { CustomersPage } from './pages/CustomersPage';
import { EvalsPage } from './pages/EvalsPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
        {/* Navigation */}
        <nav className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <span className="text-xl font-bold text-primary-600 dark:text-primary-400">
                    Case Resolution Console
                  </span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <a
                    href="/"
                    className="border-primary-500 text-slate-900 dark:text-slate-100 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                  >
                    Dashboard
                  </a>
                  <a
                    href="/alerts"
                    className="border-transparent text-slate-500 dark:text-slate-400 hover:border-slate-300 hover:text-slate-700 dark:hover:text-slate-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                  >
                    Alerts
                  </a>
                  <a
                    href="/customers"
                    className="border-transparent text-slate-500 dark:text-slate-400 hover:border-slate-300 hover:text-slate-700 dark:hover:text-slate-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                  >
                    Customers
                  </a>
                  <a
                    href="/evals"
                    className="border-transparent text-slate-500 dark:text-slate-400 hover:border-slate-300 hover:text-slate-700 dark:hover:text-slate-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                  >
                    Evals
                  </a>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/customer/:id" element={<CustomerPage />} />
          <Route path="/evals" element={<EvalsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
