import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card } from '../components/common/Card';

interface Transaction {
  id: string;
  merchant: string;
  amount_cents: number;
  currency: string;
  ts: string;
  mcc: string;
  city: string | null;
  country: string;
  card_id: string;
  customer_id: string;
  device_id?: string | null;
}

interface Customer {
  id: string;
  name: string;
  email_masked: string;
  kyc_level: string;
}

interface TransactionFormData {
  merchant: string;
  amount_cents: number;
  mcc: string;
  city: string;
  country: string;
  currency: string;
}

interface TimelineData {
  date: string;
  amount_cents: number;
  count: number;
}

interface CategorySpend {
  name: string;
  amount_cents: number;
  percentage: number;
}

interface MerchantMix {
  merchant: string;
  total_cents: number;
  count: number;
}

interface Anomaly {
  date: string;
  type: string;
  description: string;
  severity: string;
  amount_cents?: number;
}

interface Analytics {
  timeline: TimelineData[];
  category_spend: CategorySpend[];
  merchant_mix: MerchantMix[];
  anomalies: Anomaly[];
  summary: {
    total_transactions: number;
    total_amount_cents: number;
    avg_transaction_cents: number;
    period_days: number;
  };
}

export const CustomerPage: React.FC = () => {
  const { id: customerId } = useParams<{ id: string }>();
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [formData, setFormData] = useState<TransactionFormData>({
    merchant: '',
    amount_cents: 0,
    mcc: '5411',
    city: '',
    country: 'US',
    currency: 'USD'
  });

  useEffect(() => {
    if (customerId) {
      fetchCustomer();
      fetchTransactions();
      fetchAnalytics();
    }
  }, [customerId]);

  const fetchCustomer = async () => {
    try {
      const response = await fetch(`http://localhost:3000/api/customers/${customerId}`);
      if (!response.ok) throw new Error('Failed to fetch customer');
      const data = await response.json();
      setCustomer(data);
    } catch (err) {
      console.error('Error fetching customer:', err);
    }
  };

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `http://localhost:3000/api/transactions?customer_id=${customerId}`
      );
      if (!response.ok) throw new Error('Failed to fetch transactions');
      const data = await response.json();
      setTransactions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error fetching transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setAnalyticsLoading(true);
      const response = await fetch(
        `http://localhost:3000/api/customers/${customerId}/analytics?days=90`
      );
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleCreateTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customer) return;

    try {
      const response = await fetch('http://localhost:3000/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: customer.id,
          card_id: transactions[0]?.card_id || 'default-card-id',
          ...formData
        })
      });

      if (!response.ok) throw new Error('Failed to create transaction');
      
      setShowCreateModal(false);
      setFormData({
        merchant: '',
        amount_cents: 0,
        mcc: '5411',
        city: '',
        country: 'US',
        currency: 'USD'
      });
      fetchTransactions();
      fetchAnalytics();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create transaction');
    }
  };

  const handleUpdateTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTransaction) return;

    try {
      const response = await fetch(
        `http://localhost:3000/api/transactions/${selectedTransaction.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        }
      );

      if (!response.ok) throw new Error('Failed to update transaction');
      
      setShowEditModal(false);
      setSelectedTransaction(null);
      fetchTransactions();
      fetchAnalytics();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update transaction');
    }
  };

  const handleDeleteTransaction = async (txnId: string) => {
    if (!confirm('Are you sure you want to delete this transaction?')) return;

    try {
      const response = await fetch(
        `http://localhost:3000/api/transactions/${txnId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) throw new Error('Failed to delete transaction');
      fetchTransactions();
      fetchAnalytics();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete transaction');
    }
  };

  const openEditModal = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setFormData({
      merchant: transaction.merchant,
      amount_cents: transaction.amount_cents,
      mcc: transaction.mcc,
      city: transaction.city || '',
      country: transaction.country,
      currency: transaction.currency
    });
    setShowEditModal(true);
  };

  const formatCurrency = (cents: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency
    }).format(cents / 100);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!customerId) {
    return <div className="p-6">Customer ID not found</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {customer ? customer.name : `Customer ${customerId.substring(0, 8)}...`}
        </h1>
        {customer && (
          <div className="text-sm text-gray-500 space-y-1">
            <p>Email: {customer.email_masked}</p>
            <p>KYC Status: <span className="font-medium">{customer.kyc_level}</span></p>
          </div>
        )}
      </div>

      {/* Analytics Section */}
      {analyticsLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card className="p-6">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="h-64 bg-gray-100 rounded"></div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="space-y-3">
                <div className="h-8 bg-gray-100 rounded"></div>
                <div className="h-8 bg-gray-100 rounded"></div>
                <div className="h-8 bg-gray-100 rounded"></div>
              </div>
            </div>
          </Card>
        </div>
      ) : analytics ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Transaction Timeline */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Transaction Timeline (Last 90 Days)</h3>
            {analytics.timeline.length > 0 ? (
              <div className="space-y-2">
                <div className="h-48 relative">
                  {analytics.timeline.slice(-30).map((point, idx) => {
                    const maxAmount = Math.max(...analytics.timeline.map(p => p.amount_cents));
                    const height = (point.amount_cents / maxAmount) * 100;
                    return (
                      <div
                        key={idx}
                        className="absolute bottom-0 bg-blue-500 hover:bg-blue-600 transition-colors"
                        style={{
                          left: `${(idx / 30) * 100}%`,
                          width: `${100 / 30}%`,
                          height: `${height}%`,
                          minHeight: '2px'
                        }}
                        title={`${point.date}: ${formatCurrency(point.amount_cents)} (${point.count} txns)`}
                      />
                    );
                  })}
                </div>
                <div className="text-xs text-gray-500 text-center">
                  Daily spending over time (last 30 days shown)
                </div>
                <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t">
                  <div>
                    <div className="text-xs text-gray-500">Total</div>
                    <div className="text-lg font-semibold">{analytics.summary.total_transactions}</div>
                    <div className="text-xs text-gray-400">transactions</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Spent</div>
                    <div className="text-lg font-semibold">{formatCurrency(analytics.summary.total_amount_cents)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Average</div>
                    <div className="text-lg font-semibold">{formatCurrency(analytics.summary.avg_transaction_cents)}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">No transaction data available</div>
            )}
          </Card>

          {/* Category Spend */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Category Spend</h3>
            {analytics.category_spend.length > 0 ? (
              <div className="space-y-4">
                {analytics.category_spend.map((category, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700 font-medium">{category.name}</span>
                      <span className="text-gray-900 font-semibold">
                        {formatCurrency(category.amount_cents)} ({category.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div
                        className="bg-blue-600 h-2.5 rounded-full transition-all"
                        style={{ width: `${category.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">No category data available</div>
            )}
          </Card>

          {/* Merchant Mix */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Top Merchants</h3>
            {analytics.merchant_mix.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {analytics.merchant_mix.map((merchant, idx) => (
                  <div key={idx} className="py-3 flex justify-between items-center">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{merchant.merchant}</div>
                      <div className="text-xs text-gray-500">{merchant.count} transactions</div>
                    </div>
                    <div className="text-sm font-semibold text-gray-900">
                      {formatCurrency(merchant.total_cents)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">No merchant data available</div>
            )}
          </Card>

          {/* Anomalies */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Detected Anomalies</h3>
            {analytics.anomalies.length > 0 ? (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {analytics.anomalies.map((anomaly, idx) => {
                  const severityColors: Record<string, string> = {
                    high: 'bg-red-100 border-red-300',
                    medium: 'bg-orange-100 border-orange-300',
                    low: 'bg-yellow-100 border-yellow-300'
                  };
                  const severityDots: Record<string, string> = {
                    high: 'bg-red-500',
                    medium: 'bg-orange-500',
                    low: 'bg-yellow-500'
                  };
                  return (
                    <div
                      key={idx}
                      className={`flex items-start space-x-3 p-3 rounded-lg border ${severityColors[anomaly.severity] || 'bg-gray-100 border-gray-300'}`}
                    >
                      <div className={`flex-shrink-0 w-2 h-2 mt-2 rounded-full ${severityDots[anomaly.severity] || 'bg-gray-500'}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{anomaly.description}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          {new Date(anomaly.date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                          {anomaly.amount_cents && ` • ${formatCurrency(anomaly.amount_cents)}`}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <svg className="mx-auto h-12 w-12 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="mt-2">No anomalies detected</p>
              </div>
            )}
          </Card>
        </div>
      ) : null}

      {/* Transactions Section */}
      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">Transactions</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + Add Transaction
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading transactions...</div>
        ) : error ? (
          <div className="p-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">Error: {error}</p>
              <button
                onClick={fetchTransactions}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          </div>
        ) : transactions.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No transactions found for this customer.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Date/Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Merchant
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    MCC
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Location
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((txn) => (
                  <tr key={txn.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(txn.ts)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {txn.merchant}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatCurrency(txn.amount_cents, txn.currency)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {txn.mcc}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {txn.city ? `${txn.city}, ${txn.country}` : txn.country}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button
                        onClick={() => openEditModal(txn)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteTransaction(txn.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create Transaction Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Add New Transaction</h3>
            <form onSubmit={handleCreateTransaction}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Merchant
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.merchant}
                    onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Amount (cents)
                  </label>
                  <input
                    type="number"
                    required
                    value={formData.amount_cents}
                    onChange={(e) => setFormData({ ...formData, amount_cents: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    MCC
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={4}
                    pattern="[0-9]{4}"
                    value={formData.mcc}
                    onChange={(e) => setFormData({ ...formData, mcc: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={2}
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Transaction Modal */}
      {showEditModal && selectedTransaction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Edit Transaction</h3>
            <form onSubmit={handleUpdateTransaction}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Merchant
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.merchant}
                    onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Amount (cents)
                  </label>
                  <input
                    type="number"
                    required
                    value={formData.amount_cents}
                    onChange={(e) => setFormData({ ...formData, amount_cents: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    MCC
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={4}
                    pattern="[0-9]{4}"
                    value={formData.mcc}
                    onChange={(e) => setFormData({ ...formData, mcc: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={2}
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setSelectedTransaction(null);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Update
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
