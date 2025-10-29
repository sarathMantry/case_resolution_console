import React from 'react';

interface TriageDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  alertId: string;
}

interface ToolCall {
  id: string;
  name: string;
  status: 'ok' | 'error';
  duration: number;
  output?: string;
}

interface TriageData {
  riskScore: number;
  reasons: string[];
  plan: string[];
  toolCalls: ToolCall[];
  fallbacks: string[];
  citations: { title: string; text: string }[];
  recommendedAction: string;
}

export const TriageDrawer: React.FC<TriageDrawerProps> = ({ isOpen, onClose, alertId }) => {
  const drawerRef = React.useRef<HTMLDivElement>(null);
  const [triageData, setTriageData] = React.useState<TriageData>({
    riskScore: 0.85,
    reasons: [
      'Multiple high-value transactions in short time period',
      'New merchant location',
      'Device ID mismatch'
    ],
    plan: [
      'Check transaction history',
      'Verify device fingerprint',
      'Assess risk score',
      'Review policy compliance',
      'Determine action'
    ],
    toolCalls: [
      { id: '1', name: 'Transaction Analysis', status: 'ok', duration: 250 },
      { id: '2', name: 'Device Verification', status: 'error', duration: 150 },
      { id: '3', name: 'Risk Assessment', status: 'ok', duration: 300 }
    ],
    fallbacks: ['Used cached device data due to API timeout'],
    citations: [
      {
        title: 'High Risk Transaction Policy',
        text: 'Transactions above $5000 from new merchants require additional verification'
      }
    ],
    recommendedAction: 'FREEZE_CARD'
  });

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
              {/* Risk Score */}
              <div className="mb-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Risk Assessment</h3>
                <div className="flex items-center">
                  <div className="flex-1 mr-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-red-600 rounded-full h-2"
                        style={{ width: `${triageData.riskScore * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-lg font-medium text-gray-900">
                    {(triageData.riskScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Reasons */}
              <div className="mb-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Top Reasons</h3>
                <ul className="space-y-2">
                  {triageData.reasons.map((reason, index) => (
                    <li key={index} className="flex items-start">
                      <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-red-500 mt-2 mr-2" />
                      <span className="text-gray-600">{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Execution Plan */}
              <div className="mb-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Plan</h3>
                <div className="space-y-4">
                  {triageData.plan.map((step, index) => (
                    <div key={index} className="flex items-center">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                        <span className="text-sm text-blue-600 font-medium">{index + 1}</span>
                      </div>
                      <span className="text-gray-600">{step}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tool Calls */}
              <div className="mb-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Tool Execution</h3>
                <div className="space-y-3">
                  {triageData.toolCalls.map(tool => (
                    <div key={tool.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <span className={`w-2 h-2 rounded-full ${
                          tool.status === 'ok' ? 'bg-green-500' : 'bg-red-500'
                        } mr-3`} />
                        <span className="text-sm text-gray-900">{tool.name}</span>
                      </div>
                      <span className="text-sm text-gray-500">{tool.duration}ms</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Fallbacks */}
              {triageData.fallbacks.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Fallbacks Used</h3>
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                    <div className="flex">
                      <div className="ml-3">
                        <p className="text-sm text-yellow-700">
                          {triageData.fallbacks.join(', ')}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Citations */}
              <div className="mb-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Policy Citations</h3>
                <div className="space-y-4">
                  {triageData.citations.map((citation, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">{citation.title}</h4>
                      <p className="text-sm text-gray-600">{citation.text}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="border-t border-gray-200 pt-6">
                <div className="flex flex-col space-y-3">
                  <button
                    type="button"
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent 
                             text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 
                             focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Freeze Card
                  </button>
                  <button
                    type="button"
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent 
                             text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 
                             focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Open Dispute
                  </button>
                  <button
                    type="button"
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 
                             text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 
                             focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Contact Customer
                  </button>
                  <button
                    type="button"
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 
                             text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 
                             focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Mark False Positive
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};