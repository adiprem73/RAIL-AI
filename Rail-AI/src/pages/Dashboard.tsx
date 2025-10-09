import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Package, Truck, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

interface KPIData {
  totalOrders: number;
  pendingOrders: number;
  availableRakes: number;
  totalStockyards: number;
}

export default function Dashboard() {
  const [kpis, setKpis] = useState<KPIData>({
    totalOrders: 0,
    pendingOrders: 0,
    availableRakes: 0,
    totalStockyards: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadKPIs();
  }, []);

  const loadKPIs = async () => {
    try {
      const [orders, rakes, stockyards] = await Promise.all([
        api.getDataset('orders'),
        api.getDataset('rakes'),
        api.getDataset('stockyards'),
      ]);

      setKpis({
        totalOrders: orders.data.length,
        pendingOrders: orders.data.filter((o: any) => o.status === 'pending').length,
        availableRakes: rakes.data.filter((r: any) => r.status === 'available').length,
        totalStockyards: stockyards.data.length,
      });
    } catch (error) {
      console.error('Failed to load KPIs:', error);
    } finally {
      setLoading(false);
    }
  };

  const kpiCards = [
    {
      title: 'Total Orders',
      value: kpis.totalOrders,
      icon: Package,
      color: 'blue',
    },
    {
      title: 'Pending Orders',
      value: kpis.pendingOrders,
      icon: AlertCircle,
      color: 'orange',
    },
    {
      title: 'Available Rakes',
      value: kpis.availableRakes,
      icon: Truck,
      color: 'green',
    },
    {
      title: 'Stockyards',
      value: kpis.totalStockyards,
      icon: TrendingUp,
      color: 'gray',
    },
  ];

  const colorClasses = {
    blue: 'bg-blue-500',
    orange: 'bg-orange-500',
    green: 'bg-green-500',
    gray: 'bg-gray-500',
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Overview of your rake formation system
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {kpiCards.map((kpi) => {
              const Icon = kpi.icon;
              return (
                <div
                  key={kpi.title}
                  className="bg-white overflow-hidden shadow rounded-lg"
                >
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <Icon
                          className={`h-6 w-6 text-white ${colorClasses[kpi.color as keyof typeof colorClasses]}`}
                        />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">
                            {kpi.title}
                          </dt>
                          <dd className="text-lg font-semibold text-gray-900">
                            {kpi.value}
                          </dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Quick Actions
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Link
                to="/data"
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Load Data
              </Link>
              <Link
                to="/planner"
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
              >
                Run Planner
              </Link>
              <Link
                to="/settings"
                className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Configure Settings
              </Link>
            </div>
          </div>

          {kpis.pendingOrders > 0 && (
            <div className="bg-orange-50 border-l-4 border-orange-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-orange-400" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-orange-700">
                    You have {kpis.pendingOrders} pending orders that need to be
                    assigned to rakes.{' '}
                    <Link
                      to="/planner"
                      className="font-medium underline hover:text-orange-600"
                    >
                      Run planner
                    </Link>{' '}
                    to generate an optimal plan.
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
