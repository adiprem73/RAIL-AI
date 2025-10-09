import { Settings as SettingsIcon } from 'lucide-react';

export default function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-sm text-gray-600">
          Configure system parameters and defaults
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Cost Parameters
        </h2>

        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Freight Rate (₹/tonne-km)
              </label>
              <input
                type="number"
                defaultValue={2.5}
                step={0.1}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Demurrage Rate (₹/hour)
              </label>
              <input
                type="number"
                defaultValue={500}
                step={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Idle Freight Cost (₹/hour)
              </label>
              <input
                type="number"
                defaultValue={100}
                step={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Min Rake Utilization (%)
              </label>
              <input
                type="number"
                defaultValue={75}
                min={0}
                max={100}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Product-Wagon Compatibility Matrix
        </h2>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Product
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  BOXN
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  BCNA
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  BOX
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">COAL</td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">IRON_ORE</td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">STEEL</td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-sm text-gray-500">
          Check boxes indicate compatible product-wagon combinations. This matrix is
          used during planning to ensure valid assignments.
        </p>
      </div>

      <div className="flex justify-end">
        <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          <SettingsIcon className="h-4 w-4 mr-2" />
          Save Settings
        </button>
      </div>
    </div>
  );
}
