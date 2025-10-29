import React from 'react';
import { Card } from '../components/common/Card';

interface EvalResult {
  id: string;
  testCase: string;
  outcome: 'pass' | 'fail';
  toolMetrics: {
    name: string;
    success: number;
    total: number;
  }[];
  confusionMatrix: {
    predicted: string;
    actual: string;
    count: number;
  }[];
}

const ConfusionMatrix: React.FC<{ data: EvalResult['confusionMatrix'] }> = ({ data }) => {
  const labels = ['low', 'medium', 'high'];
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actual ↓ Predicted →
            </th>
            {labels.map(label => (
              <th
                key={label}
                className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {labels.map(actualLabel => (
            <tr key={actualLabel}>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {actualLabel}
              </td>
              {labels.map(predictedLabel => {
                const cell = data.find(
                  d => d.actual === actualLabel && d.predicted === predictedLabel
                );
                const value = cell?.count || 0;
                const isCorrect = actualLabel === predictedLabel;
                
                return (
                  <td
                    key={predictedLabel}
                    className={`px-6 py-4 whitespace-nowrap text-sm ${
                      isCorrect ? 'bg-green-50 text-green-900' : 'text-gray-500'
                    }`}
                  >
                    {value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const ToolMetrics: React.FC<{ metrics: EvalResult['toolMetrics'] }> = ({ metrics }) => (
  <div className="space-y-4">
    {metrics.map(tool => (
      <div key={tool.name}>
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">{tool.name}</span>
          <span className="text-gray-900">
            {((tool.success / tool.total) * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 rounded-full h-2"
            style={{ width: `${(tool.success / tool.total) * 100}%` }}
          />
        </div>
      </div>
    ))}
  </div>
);

export const EvalsPage: React.FC = () => {
  // Mock data - replace with actual API calls
  const evalResults: EvalResult[] = [
    {
      id: '1',
      testCase: 'Freeze with OTP',
      outcome: 'pass',
      toolMetrics: [
        { name: 'Risk Assessment', success: 95, total: 100 },
        { name: 'OTP Verification', success: 98, total: 100 },
        { name: 'Card Freeze', success: 97, total: 100 }
      ],
      confusionMatrix: [
        { predicted: 'low', actual: 'low', count: 85 },
        { predicted: 'low', actual: 'medium', count: 10 },
        { predicted: 'medium', actual: 'low', count: 5 },
        { predicted: 'medium', actual: 'medium', count: 75 },
        { predicted: 'high', actual: 'high', count: 90 }
      ]
    }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Evaluation Results</h1>
        <p className="text-gray-500">Model performance and test case outcomes</p>
      </div>

      <div className="space-y-6">
        {evalResults.map(result => (
          <Card key={result.id} className="p-6">
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">
                  {result.testCase}
                </h2>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    ${result.outcome === 'pass' 
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                    }`}
                >
                  {result.outcome.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">
                  Tool Performance
                </h3>
                <ToolMetrics metrics={result.toolMetrics} />
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">
                  Risk Level Confusion Matrix
                </h3>
                <ConfusionMatrix data={result.confusionMatrix} />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};