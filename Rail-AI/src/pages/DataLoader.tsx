import { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import CSVUploader from '../components/CSVUploader';
import { api } from '../services/api';
import type { DatasetType } from '../types';

const DATASETS: { key: DatasetType; label: string }[] = [
  { key: 'stockyards', label: 'Stockyards' },
  { key: 'orders', label: 'Orders' },
  { key: 'rakes', label: 'Rakes / Wagons' },
  { key: 'loading_points', label: 'Loading Points' },
  { key: 'products', label: 'Products' },
  { key: 'wagon_types', label: 'Wagon Types' },
];

export default function DataLoader() {
  const [activeTab, setActiveTab] = useState<DatasetType>('stockyards');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await api.getDataset(activeTab);
      setData(result.data || []);
    } catch (error) {
      console.error('Failed to load data:', error);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (confirm(`Are you sure you want to clear all ${activeTab} data?`)) {
      try {
        for (const record of data) {
          await api.deleteRecord(activeTab, record.id);
        }
        await loadData();
      } catch (error) {
        alert('Failed to clear data');
      }
    }
  };

  const renderValue = (value: any): string => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'object') return JSON.stringify(value);
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    return String(value);
  };

  const columns = data.length > 0 ? Object.keys(data[0]).filter(k => k !== 'created_at' && k !== 'updated_at') : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Data Loader</h1>
        <p className="mt-2 text-sm text-gray-600">
          Upload and manage your railway operational data
        </p>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-4 px-4" aria-label="Tabs">
            {DATASETS.map((dataset) => (
              <button
                key={dataset.key}
                onClick={() => setActiveTab(dataset.key)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === dataset.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {dataset.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <CSVUploader dataset={activeTab} onUploadComplete={loadData} />
            </div>

            <div className="lg:col-span-2">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-medium text-gray-700">
                  Data Preview ({data.length} records)
                </h3>
                <div className="space-x-2">
                  <button
                    onClick={loadData}
                    disabled={loading}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                  <button
                    onClick={handleClear}
                    disabled={data.length === 0}
                    className="inline-flex items-center px-3 py-1.5 border border-red-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50 disabled:opacity-50"
                  >
                    Clear All
                  </button>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : data.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">
                    No data available. Upload a CSV file to get started.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto border border-gray-200 rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {columns.slice(0, 6).map((col) => (
                          <th
                            key={col}
                            className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            {col.replace(/_/g, ' ')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data.slice(0, 100).map((row, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          {columns.slice(0, 6).map((col) => (
                            <td
                              key={col}
                              className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate"
                              title={renderValue(row[col])}
                            >
                              {renderValue(row[col])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {data.length > 100 && (
                    <div className="px-4 py-3 bg-gray-50 text-xs text-gray-500 text-center">
                      Showing first 100 of {data.length} records
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
