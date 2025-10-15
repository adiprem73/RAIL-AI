import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Info } from 'lucide-react';
import { api } from '../services/api';
import type { PlanningJob } from '../types';

export default function Planner() {
  const navigate = useNavigate();
  const [snapshot, setSnapshot] = useState({ orders: 0, stockyards: 0, rakes: 0 });
  const [scenarioName, setScenarioName] = useState('');
  const [notes, setNotes] = useState('');
  const [mode, setMode] = useState<'greedy' | 'or-tools' | 'hybrid'>('greedy');
  const [allowMultiDest, setAllowMultiDest] = useState(false);
  const [minRakeSize, setMinRakeSize] = useState(1000);
  const [freightWeight, setFreightWeight] = useState(1.0);
  const [demurrageWeight, setDemurrageWeight] = useState(0.5);
  const [idleWeight, setIdleWeight] = useState(0.3);
  const [loading, setLoading] = useState(false);
  const [activeJob, setActiveJob] = useState<PlanningJob | null>(null);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    loadSnapshot();
  }, []);

  useEffect(() => {
    if (activeJob && activeJob.status === 'running' && !polling) {
      setPolling(true);
      const interval = setInterval(async () => {
        try {
          const job = await api.getJobStatus(activeJob.id);
          setActiveJob(job);

          if (job.status === 'completed' && job.plan_id) {
            clearInterval(interval);
            setPolling(false);
            navigate(`/plans/${job.plan_id}`);
          } else if (job.status === 'failed' || job.status === 'cancelled') {
            clearInterval(interval);
            setPolling(false);
          }
        } catch (error) {
          console.error('Failed to poll job status:', error);
        }
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [activeJob, polling, navigate]);

  const loadSnapshot = async () => {
    try {
      const [orders, stockyards, rakes] = await Promise.all([
        api.getDataset('orders'),
        api.getDataset('stockyards'),
        api.getDataset('rakes'),
      ]);

      setSnapshot({
        orders: orders.data.filter((o: any) => o.status === 'pending').length,
        stockyards: stockyards.data.length,
        rakes: rakes.data.filter((r: any) => r.status === 'available').length,
      });
    } catch (error) {
      console.error('Failed to load snapshot:', error);
    }
  };

  const handleRunPlanner = async () => {
    if (!scenarioName.trim()) {
      alert('Please enter a scenario name');
      return;
    }

    setLoading(true);

    try {
      const config = {
        mode,
        allow_multi_destination: allowMultiDest,
        min_rake_size: minRakeSize,
        cost_weights: {
          freight: freightWeight,
          demurrage: demurrageWeight,
          idle: idleWeight,
        },
        freight_rate: 2.5,
        demurrage_rate: 500,
        idle_cost: 100,
      };

      const result = await api.generatePlan(scenarioName, config, notes);
      const job = await api.getJobStatus(result.job_id);
      setActiveJob(job);
    } catch (error: any) {
      alert(`Failed to start planner: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelJob = async () => {
    if (activeJob) {
      try {
        await api.cancelJob(activeJob.id);
        const updatedJob = await api.getJobStatus(activeJob.id);
        setActiveJob(updatedJob);
      } catch (error) {
        alert('Failed to cancel job');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Planner</h1>
        <p className="mt-2 text-sm text-gray-600">
          Configure and run rake formation optimization
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <Info className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Current Snapshot</h3>
            <div className="mt-2 text-sm text-blue-700">
              <span className="font-medium">{snapshot.orders}</span> pending orders,{' '}
              <span className="font-medium">{snapshot.rakes}</span> available rakes,{' '}
              <span className="font-medium">{snapshot.stockyards}</span> stockyards
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">
          Planner Configuration
        </h2>

        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Scenario Name
              </label>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                placeholder="e.g., October Week 2 Plan"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Planning Mode
              </label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="greedy">Greedy (Fast)</option>
                <option value="or-tools">OR-Tools (Optimal)</option>
                <option value="hybrid">Hybrid (Best of Both)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes about this planning run..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Rake Size (tonnes)
              </label>
              <input
                type="number"
                value={minRakeSize}
                onChange={(e) => setMinRakeSize(Number(e.target.value))}
                min={0}
                step={100}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center h-full">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={allowMultiDest}
                  onChange={(e) => setAllowMultiDest(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Allow multi-destination rakes
                </span>
              </label>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-4">Cost Weights</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-sm text-gray-600">Freight Cost</label>
                  <span className="text-sm font-medium text-gray-900">
                    {freightWeight.toFixed(1)}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={freightWeight}
                  onChange={(e) => setFreightWeight(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-sm text-gray-600">Demurrage Cost</label>
                  <span className="text-sm font-medium text-gray-900">
                    {demurrageWeight.toFixed(1)}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={demurrageWeight}
                  onChange={(e) => setDemurrageWeight(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-sm text-gray-600">Idle Freight Cost</label>
                  <span className="text-sm font-medium text-gray-900">
                    {idleWeight.toFixed(1)}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={idleWeight}
                  onChange={(e) => setIdleWeight(Number(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleRunPlanner}
              disabled={loading || !!activeJob}
              className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              <Play className="h-4 w-4 mr-2" />
              {loading ? 'Starting...' : 'Run Planner'}
            </button>
          </div>
        </div>
      </div>

      {activeJob && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Job Status: {activeJob.scenario_name}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Status:{' '}
                <span
                  className={`font-medium ${
                    activeJob.status === 'completed'
                      ? 'text-green-600'
                      : activeJob.status === 'failed'
                      ? 'text-red-600'
                      : 'text-blue-600'
                  }`}
                >
                  {activeJob.status}
                </span>
              </p>
            </div>
            {activeJob.status === 'running' && (
              <button
                onClick={handleCancelJob}
                className="px-3 py-1.5 border border-red-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50"
              >
                Cancel
              </button>
            )}
          </div>

          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Progress</span>
              <span>{activeJob.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${activeJob.progress}%` }}
              />
            </div>
          </div>

          <div className="bg-gray-900 text-gray-100 rounded-md p-4 font-mono text-xs overflow-y-auto max-h-64">
            {activeJob.logs || 'No logs yet...'}
          </div>
        </div>
      )}
    </div>
  );
}
