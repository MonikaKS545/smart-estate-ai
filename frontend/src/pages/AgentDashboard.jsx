import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from "recharts";
import { Pencil, Trash2 } from "lucide-react";
import mockProperties from "../mocks/mockProperties";

/**
 * AgentDashboard page.
 *
 * Note: properties have no date field in the spec's shape, so "price
 * trend" is shown as price-across-listings (sorted ascending) rather
 * than a true time series. If a listed_date field is added later,
 * swap this chart for a real time-series line chart.
 *
 * Listings management here is UI-only (edit/delete buttons don't
 * mutate anything yet) — real CRUD wires up once Part 1's backend
 * endpoints exist.
 */

const STATUS_COLORS = {
  available: "#16a34a",
  sold: "#dc2626",
  pending: "#ca8a04",
};

export default function AgentDashboard() {
  // Treat all mock properties as "this agent's" listings for the demo.
  const [listings] = useState(mockProperties);

  const statusCounts = listings.reduce((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1;
    return acc;
  }, {});
  const statusData = Object.entries(statusCounts).map(([status, count]) => ({
    name: status,
    value: count,
  }));

  const priceData = [...listings]
    .sort((a, b) => a.price - b.price)
    .map((p) => ({
      name: p.title.length > 18 ? p.title.slice(0, 18) + "…" : p.title,
      price: p.price / 100000, // in lakhs, for readable axis labels
    }));

  return (
    <div className="p-6 md:p-8 space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Agent Dashboard</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border border-gray-200 rounded-xl p-4">
          <h3 className="font-semibold text-gray-900 mb-3">
            Listings by Status
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {statusData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={STATUS_COLORS[entry.name] || "#9ca3af"}
                  />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="border border-gray-200 rounded-xl p-4">
          <h3 className="font-semibold text-gray-900 mb-3">
            Price by Listing (₹ Lakhs)
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={priceData}>
              <XAxis dataKey="name" hide />
              <YAxis />
              <Tooltip />
              <Bar dataKey="price" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <h3 className="font-semibold text-gray-900 p-4 border-b border-gray-100">
          My Listings
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-500">
                  Title
                </th>
                <th className="text-left p-3 font-medium text-gray-500">
                  Price
                </th>
                <th className="text-left p-3 font-medium text-gray-500">
                  BHK
                </th>
                <th className="text-left p-3 font-medium text-gray-500">
                  Status
                </th>
                <th className="text-left p-3 font-medium text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {listings.map((p) => (
                <tr key={p.id} className="border-t border-gray-100">
                  <td className="p-3 text-gray-900">{p.title}</td>
                  <td className="p-3 text-gray-700">
                    ₹{(p.price / 100000).toFixed(0)} L
                  </td>
                  <td className="p-3 text-gray-700">{p.bhk}</td>
                  <td className="p-3 capitalize text-gray-700">{p.status}</td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button
                        className="text-gray-400 hover:text-blue-600"
                        title="Edit listing"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        className="text-gray-400 hover:text-red-600"
                        title="Delete listing"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}