import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle, MessageSquare, ArrowLeft } from 'lucide-react';
import { api } from '../services/api';
import type { Plan } from '../types';

export default function PlanResults() {
  const { planId } = useParams<{ planId: string }>();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);

  useEffect(() => {
    if (planId) {
      loadPlan();
    }
  }, [planId]);

  const loadPlan = async () => {
    if (!planId) return;

    setLoading(true);
    try {
      const result = await api.getPlan(planId);
      setPlan(result);
    } catch (error) {
      console.error('Failed to load plan:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async () => {
    if (!planId) return;

    setLoadingExplanation(true);
    try {
      const result = await api.explainPlan(planId);
      setExplanation(result.explanation);
    } catch (error) {
      alert('Failed to generate explanation');
    } finally {
      setLoadingExplanation(false);
    }
  };

  const handleCommit = async () => {
    if (!planId || !plan) return;

    if (
      !confirm(
        'Are you sure you want to commit this plan? This will mark orders as assigned and update rake statuses.'
      )
    ) {
      return;
    }

    try {
      await api.commitPlan(planId);
      await loadPlan();
      alert('Plan committed successfully!');
    } catch (error: any) {
      alert(`Failed to commit plan: ${error.message}`);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Plan not found</p>
      </div>
    );
  }

  const utilizationColor =
    plan.utilization_pct >= 80
      ? 'text-green-600'
      : plan.utilization_pct >= 60
      ? 'text-orange-600'
      : 'text-red-600';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/planner"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Planner
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{plan.name}</h1>
            <p className="mt-1 text-sm text-gray-600">
              Generated using {plan.algorithm || 'unknown'} algorithm
            </p>
          </div>
        </div>

        {plan.committed && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            <CheckCircle className="h-4 w-4 mr-1" />
            Committed
          </span>
        )}
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Plan Summary</h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total Cost</p>
            <p className="text-2xl font-bold text-gray-900">
              ₹{plan.total_cost.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-600">Utilization</p>
            <p className={`text-2xl font-bold ${utilizationColor}`}>
              {plan.utilization_pct.toFixed(1)}%
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-600">Orders Fulfilled</p>
            <p className="text-2xl font-bold text-gray-900">
              {plan.orders_fulfilled} / {plan.total_orders}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-600">Rakes Used</p>
            <p className="text-2xl font-bold text-gray-900">{plan.rakes.length}</p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Freight Cost</p>
              <p className="font-semibold text-gray-900">
                ₹{plan.freight_cost.toLocaleString('en-IN')}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Demurrage Cost</p>
              <p className="font-semibold text-gray-900">
                ₹{plan.demurrage_cost.toLocaleString('en-IN')}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Idle Freight Cost</p>
              <p className="font-semibold text-gray-900">
                ₹{plan.idle_cost.toLocaleString('en-IN')}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex space-x-3">
        <button
          onClick={handleExplain}
          disabled={loadingExplanation}
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <MessageSquare className="h-4 w-4 mr-2" />
          {loadingExplanation ? 'Generating...' : 'Explain Plan'}
        </button>

        {!plan.committed && (
          <button
            onClick={handleCommit}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Commit Plan
          </button>
        )}
      </div>

      {explanation && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Plan Explanation
          </h2>
          <div className="prose max-w-none text-sm text-gray-700 whitespace-pre-wrap">
            {explanation}
          </div>
        </div>
      )}

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Rake Assignments</h2>

        {plan.rakes.map((rake, idx) => {
          const utilizationColor =
            rake.utilization_pct >= 80
              ? 'bg-green-100 text-green-800'
              : rake.utilization_pct >= 60
              ? 'bg-orange-100 text-orange-800'
              : 'bg-red-100 text-red-800';

          return (
            <div key={rake.id} className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Rake {idx + 1}: {rake.rake_number}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Origin: {rake.origin_stockyard_name || 'Multiple'} →{' '}
                    Destination: {rake.destinations.join(', ')}
                  </p>
                </div>
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${utilizationColor}`}
                >
                  {rake.utilization_pct.toFixed(1)}% utilized
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Total Weight</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {rake.total_weight.toFixed(0)} tonnes
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Orders Assigned</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {rake.orders_assigned.length}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Freight Cost</p>
                  <p className="text-lg font-semibold text-gray-900">
                    ₹{rake.freight_cost.toLocaleString('en-IN')}
                  </p>
                </div>
              </div>

              {rake.orders_assigned.length > 0 && (
                <div className="border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Order Details
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Order
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Product
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Quantity
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Destination
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {rake.orders_assigned.map((order) => (
                          <tr key={order.order_id}>
                            <td className="px-3 py-2 text-sm text-gray-900">
                              {order.order_number}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-900">
                              {order.product_code}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-900">
                              {order.quantity.toFixed(0)} t
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-900">
                              {order.destination}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
