import React from 'react';

interface TriageDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  alertId: string | null;
}

interface Customer {
  id: string;
  name: string;
  email_masked: string;
  kyc_level: string;
}

interface Transaction {
  id: string;
  merchant: string;
  amount_cents: number;
  currency: string;
  ts: string;
  mcc: string;
  city: string | null;
  country: string;
}

interface Triage {
  risk: string;
  reasons: { reasons: string[] };
  fallback_used: boolean;
  latency_ms: number | null;
  started_at: string | null;
  ended_at: string | null;
}

interface ToolCall {
  step: string;
  ok: boolean;
  duration_ms: number;
  detail: any;
  seq: number;
}

interface Citation {
  title: string;
  text: string;
  source: string;
}

interface TriageData {
  alert_id: string;
  status: string;
  created_at: string;
  customer: Customer | null;
  transaction: Transaction | null;
  triage: Triage;
  tool_calls: ToolCall[];
  recommended_action: string;
  citations: Citation[];
}

export const TriageDrawer: React.FC<TriageDrawerProps> = ({ isOpen, onClose, alertId }) => {
  const drawerRef = React.useRef<HTMLDivElement>(null);
  const wsRef = React.useRef<WebSocket | null>(null);
  const [triageData, setTriageData] = React.useState<TriageData | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [streamingMessage, setStreamingMessage] = React.useState<string>('');
  const [actionLoading, setActionLoading] = React.useState<string | null>(null);
  const [runningToolIndex, setRunningToolIndex] = React.useState<number | null>(null);

  // Connect to WebSocket when drawer opens
  React.useEffect(() => {
    if (!isOpen || !alertId) {
      // Cleanup WebSocket on close
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setTriageData(null);
      setStreamingMessage('');
      setRunningToolIndex(null);
      return;
    }

    streamTriageData();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [alertId, isOpen]);

  const streamTriageData = () => {
    if (!alertId) return;

    try {
      setLoading(true);
      setTriageData(null);
      setStreamingMessage('Connecting...');

      // Create WebSocket connection
      const ws = new WebSocket(`ws://localhost:3000/api/triage/ws/${alertId}`);
      wsRef.current = ws;

      // Initialize partial data with safe defaults
      const partialData: Partial<TriageData> = {
        alert_id: alertId,
        tool_calls: [],
        citations: [],
        triage: {
          risk: '',
          reasons: { reasons: [] },
          fallback_used: false,
          latency_ms: null,
          started_at: null,
          ended_at: null
        }
      };

      ws.onopen = () => {
        console.log('WebSocket connected');
        setStreamingMessage('Connected. Starting triage...');
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('WebSocket message:', message);

        switch (message.type) {
          case 'status':
            setStreamingMessage(message.message || '');
            break;

          case 'alert':
            Object.assign(partialData, message.data);
            setTriageData({ ...partialData } as TriageData);
            setStreamingMessage('Alert loaded. Analyzing risk...');
            break;

          case 'risk':
            partialData.triage = {
              risk: message.data.risk,
              reasons: { reasons: [] },
              fallback_used: false,
              latency_ms: null,
              started_at: null,
              ended_at: null
            };
            partialData.recommended_action = message.data.recommended_action;
            setTriageData({ ...partialData } as TriageData);
            setStreamingMessage('Risk assessed. Loading transaction...');
            break;

          case 'transaction':
            partialData.transaction = message.data;
            setTriageData({ ...partialData } as TriageData);
            setStreamingMessage('Transaction loaded. Analyzing reasons...');
            break;

          case 'reasons':
            if (partialData.triage) {
              partialData.triage.reasons = message.data;
            }
            setTriageData({ ...partialData } as TriageData);
            setStreamingMessage('Reasons identified. Executing tools...');
            break;

          case 'tool_call':
            const toolCall = message.data;
            const isRunning = toolCall.status === 'running';
            
            if (isRunning) {
              // Add tool as running
              const newIndex = partialData.tool_calls!.length;
              partialData.tool_calls!.push(toolCall);
              setRunningToolIndex(newIndex);
              setStreamingMessage(`Running: ${toolCall.step}...`);
            } else {
              // Update last tool with completed status
              const lastIndex = partialData.tool_calls!.length - 1;
              if (lastIndex >= 0) {
                partialData.tool_calls![lastIndex] = toolCall;
                setRunningToolIndex(null);
              }
            }
            setTriageData({ ...partialData } as TriageData);
            break;

          case 'citations':
            partialData.citations = message.data;
            setTriageData({ ...partialData } as TriageData);
            setStreamingMessage('Loading policy citations...');
            break;

          case 'complete':
            if (partialData.triage) {
              partialData.triage.latency_ms = message.data.latency_ms;
            }
            setTriageData({ ...partialData } as TriageData);
            setStreamingMessage('');
            setLoading(false);
            break;

          case 'error':
            console.error('WebSocket error message:', message.message);
            alert(`Error: ${message.message}`);
            setLoading(false);
            break;
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStreamingMessage('Connection error');
        setLoading(false);
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setLoading(false);
      };

    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      alert('Failed to connect to triage stream');
      setLoading(false);
    }
  };

  const handleAction = async (action: string, actionLabel: string) => {
    if (!alertId) return;

    if (!confirm(`Are you sure you want to ${actionLabel.toLowerCase()}?`)) {
      return;
    }

    try {
      setActionLoading(action);
      const response = await fetch(`http://localhost:3000/api/triage/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId })
      });

      if (!response.ok) throw new Error(`Failed to ${actionLabel}`);
      
      const result = await response.json();
      
      // Refresh triage data via WebSocket
      streamTriageData();
      
      // Show appropriate message based on idempotency
      if (result.already_processed) {
        alert(`${actionLabel}: ${result.message || 'Action already processed'}`);
      } else {
        alert(`${actionLabel} completed successfully`);
      }
    } catch (error) {
      alert(`Failed to ${actionLabel}: ${error}`);
    } finally {
      setActionLoading(null);
    }
  };

  const formatCurrency = (cents: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency
    }).format(cents / 100);
  };

  const getRiskColor = (risk: string) => {
    const riskLevel = risk?.toUpperCase();
    switch (riskLevel) {
      case 'HIGH':
        return 'bg-red-600';
      case 'MEDIUM':
        return 'bg-orange-600';
      case 'LOW':
        return 'bg-yellow-600';
      default:
        return 'bg-gray-600';
    }
  };

  const getRiskScore = (risk: string) => {
    const riskLevel = risk?.toUpperCase();
    switch (riskLevel) {
      case 'HIGH':
        return 0.85;
      case 'MEDIUM':
        return 0.5;
      case 'LOW':
        return 0.25;
      default:
        return 0;
    }
  };

  const getRecommendedActionLabel = (action: string) => {
    const labels: Record<string, string> = {
      FREEZE_CARD: 'Freeze Card',
      CONTACT_CUSTOMER: 'Contact Customer',
      OPEN_DISPUTE: 'Open Dispute',
      MONITOR: 'Monitor Transaction',
      REVIEW_MANUALLY: 'Manual Review'
    };
    return labels[action] || action;
  };

  // Handle ESC key
  React.useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Trap focus within drawer when open
  React.useEffect(() => {
    if (!isOpen) return;

    const drawer = drawerRef.current;
    if (!drawer) return;

    const focusableElements = drawer.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0] as HTMLElement;
    const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable.focus();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    };

    drawer.addEventListener('keydown', handleTab);
    firstFocusable.focus();

    return () => drawer.removeEventListener('keydown', handleTab);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 overflow-hidden z-50">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 pl-10 max-w-full flex">
        <div className="relative w-screen max-w-md">
          <div
            ref={drawerRef}
            className="h-full flex flex-col bg-white shadow-xl overflow-y-scroll"
          >
            {/* Header */}
            <div className="px-4 py-6 bg-blue-700 sm:px-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-white" id="slide-over-title">
                  Triage Alert #{alertId}
                </h2>
                <button
                  type="button"
                  className="text-blue-200 hover:text-white focus:outline-none focus:ring-2 focus:ring-white"
                  onClick={onClose}
                >
                  <span className="sr-only">Close panel</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="relative flex-1 px-4 py-6 sm:px-6">
              {loading && !triageData ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                  {streamingMessage && (
                    <p className="mt-4 text-sm text-gray-600">{streamingMessage}</p>
                  )}
                </div>
              ) : triageData ? (
                <>
                  {/* Risk Score */}
                  {triageData.triage && (
                    <div className="mb-8">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Risk Assessment</h3>
                      <div className="flex items-center">
                        <div className="flex-1 mr-4">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`rounded-full h-2 ${getRiskColor(triageData.triage.risk)}`}
                              style={{ width: `${getRiskScore(triageData.triage.risk) * 100}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-lg font-medium text-gray-900">
                          {triageData.triage.risk?.toUpperCase()}
                        </span>
                      </div>
                      {triageData.triage.fallback_used && (
                        <div className="mt-3 bg-yellow-50 border-l-4 border-yellow-400 p-3">
                          <p className="text-sm text-yellow-700">Fallback logic was used</p>
                        </div>
                      )}
                      {triageData.triage.latency_ms && (
                        <p className="text-xs text-gray-500 mt-2">
                          Completed in {triageData.triage.latency_ms}ms
                        </p>
                      )}
                    </div>
                  )}

                  {/* Reasons */}
                  {triageData.triage && (
                    <div className="mb-8">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Top Reasons</h3>
                      <ul className="space-y-2">
                        {triageData.triage.reasons?.reasons?.map((reason: string, index: number) => (
                          <li key={index} className="flex items-start">
                            <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-red-500 mt-2 mr-2" />
                            <span className="text-gray-600">{reason}</span>
                          </li>
                        )) || <p className="text-sm text-gray-500">No reasons available</p>}
                      </ul>
                    </div>
                  )}

                  {/* Transaction Details */}
                  {triageData.transaction && (
                    <div className="mb-8">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Transaction</h3>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Merchant</span>
                          <span className="text-sm font-medium text-gray-900">{triageData.transaction.merchant}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Amount</span>
                          <span className="text-sm font-medium text-gray-900">
                            {formatCurrency(triageData.transaction.amount_cents, triageData.transaction.currency)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Location</span>
                          <span className="text-sm font-medium text-gray-900">
                            {triageData.transaction.city ? `${triageData.transaction.city}, ` : ''}{triageData.transaction.country}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">MCC</span>
                          <span className="text-sm font-medium text-gray-900">{triageData.transaction.mcc}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Customer Info */}
                  {triageData.customer && (
                    <div className="mb-8">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Customer</h3>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Name</span>
                          <span className="text-sm font-medium text-gray-900">{triageData.customer.name}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Email</span>
                          <span className="text-sm font-medium text-gray-900">{triageData.customer.email_masked}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">KYC Level</span>
                          <span className="text-sm font-medium text-gray-900">{triageData.customer.kyc_level}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tool Calls */}
                  {triageData.tool_calls.length > 0 && (
                    <div className="mb-8">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">
                        Tool Execution
                        {streamingMessage && (
                          <span className="ml-2 text-sm font-normal text-blue-600 animate-pulse">
                            {streamingMessage}
                          </span>
                        )}
                      </h3>
                      <div className="space-y-3">
                        {triageData.tool_calls.map((tool, idx) => {
                          const isRunning = idx === runningToolIndex;
                          const bgColor = isRunning 
                            ? 'bg-blue-50 border border-blue-200 animate-pulse'
                            : tool.ok 
                              ? 'bg-green-50 border border-green-200' 
                              : 'bg-red-50 border border-red-200';
                          const dotColor = isRunning
                            ? 'bg-blue-500 animate-ping'
                            : tool.ok 
                              ? 'bg-green-500' 
                              : 'bg-red-500';
                          
                          return (
                            <div
                              key={idx}
                              className={`flex items-center justify-between p-3 rounded-lg ${bgColor}`}
                            >
                              <div className="flex items-center flex-1">
                                <span className={`w-2 h-2 rounded-full ${dotColor} mr-3`} />
                                <div className="flex-1">
                                  <span className="text-sm text-gray-900 font-medium">
                                    {tool.step}
                                    {isRunning && (
                                      <span className="ml-2 text-xs text-blue-600">running...</span>
                                    )}
                                  </span>
                                  {tool.detail && !isRunning && (
                                    <p className="text-xs text-gray-600 mt-1">
                                      {JSON.stringify(tool.detail).substring(0, 60)}...
                                    </p>
                                  )}
                                </div>
                              </div>
                              {!isRunning && (
                                <span className="text-sm text-gray-500 font-mono ml-2">{tool.duration_ms}ms</span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Citations */}
                  {triageData.citations.length > 0 && (
                    <div className="mb-8">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Policy Citations</h3>
                      <div className="space-y-4">
                        {triageData.citations.map((citation, index) => (
                          <div key={index} className="border border-blue-200 bg-blue-50 rounded-lg p-4">
                            <h4 className="font-medium text-blue-900 mb-2">{citation.title}</h4>
                            <p className="text-sm text-blue-700 mb-2">{citation.text}</p>
                            <span className="text-xs text-blue-600">Source: {citation.source}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommended Action */}
                  <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Recommended Action</h3>
                    <div className="p-4 bg-blue-50 border-2 border-blue-300 rounded-lg">
                      <p className="text-lg font-semibold text-blue-900">
                        {getRecommendedActionLabel(triageData.recommended_action)}
                      </p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="border-t border-gray-200 pt-6">
                    <div className="flex flex-col space-y-3">
                      <button
                        type="button"
                        onClick={() => handleAction('freeze-card', 'Freeze Card')}
                        disabled={actionLoading !== null}
                        className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent 
                                 text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 
                                 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {actionLoading === 'freeze-card' ? 'Processing...' : 'Freeze Card'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleAction('open-dispute', 'Open Dispute')}
                        disabled={actionLoading !== null}
                        className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent 
                                 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 
                                 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {actionLoading === 'open-dispute' ? 'Processing...' : 'Open Dispute'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleAction('contact-customer', 'Contact Customer')}
                        disabled={actionLoading !== null}
                        className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 
                                 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 
                                 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {actionLoading === 'contact-customer' ? 'Processing...' : 'Contact Customer'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleAction('mark-false-positive', 'Mark False Positive')}
                        disabled={actionLoading !== null}
                        className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 
                                 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 
                                 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {actionLoading === 'mark-false-positive' ? 'Processing...' : 'Mark False Positive'}
                      </button>
                    </div>
                  </div>

                  {/* Status Info */}
                  <div className="pt-4 border-t mt-4">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Status: <span className="font-medium text-gray-700">{triageData.status}</span></span>
                      <span>Created: {new Date(triageData.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center text-gray-500 py-12">
                  No triage data available
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};