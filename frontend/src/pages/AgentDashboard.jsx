import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
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
import { Pencil, Trash2, Plus } from "lucide-react";
import client from "../api/client";
import mockProperties from "../mocks/mockProperties";

const STATUS_COLORS = {
  available: "#16a34a",
  approved: "#16a34a",
  sold: "#dc2626",
  pending: "#ca8a04",
  rejected: "#6b7280",
};

// Mark mock rows so we know not to try deleting/editing them via the API
const demoListings = mockProperties.map((p) => ({ ...p, isDemo: true }));

export default function AgentDashboard() {
  const navigate = useNavigate();
  const [realListings, setRealListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const fetchListings = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await client.get("/properties/mine");
      setRealListings(data.properties || []);
    } catch (err) {
      console.error(err);
      setError("Couldn't load your live listings — showing demo data only.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, []);

  const handleDelete = async (property, title) => {
    if (property.isDemo) {
      alert("This is demo data and can't be deleted.");
      return;
    }
    const confirmed = window.confirm(
      `Delete "${title}"? This cannot be undone.`
    );
    if (!confirmed) return;

    setDeletingId(property.id);
    try {
      await client.delete(`/properties/${property.id}`);
      setRealListings((prev) => prev.filter((p) => p.id !== property.id));
    } catch (err) {
      console.error(err);
      alert("Failed to delete this listing. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  // Real listings first, demo listings after
  const listings = [...realListings, ...demoListings];

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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Agent Dashboard</h1>
        <Link
          to="/agent/add-property"
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          <Plus size={16} />
          Add Property
        </Link>
      </div>

      {error && (
        <div className="bg-yellow-50 text-yellow-800 p-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-500 text-sm">Loading your listings...</p>
      ) : (
        <>
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
                      <td className="p-3 text-gray-900">
                        {p.title}
                        {p.isDemo && (
                          <span className="ml-2 text-xs text-gray-400">
                            (demo)
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-gray-700">
                        {p.listing_type === "rent"
  ? `₹${Number(p.price).toLocaleString("en-IN")}/mo`
  : `₹${(p.price / 100000).toFixed(0)} L`}
                      </td>
                      <td className="p-3 text-gray-700">{p.bhk ?? "-"}</td>
                      <td className="p-3 capitalize text-gray-700">
                        {p.status}
                      </td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <button
                            className="text-gray-400 hover:text-blue-600 disabled:opacity-30"
                            title={
                              p.isDemo
                                ? "Demo data — not editable"
                                : "Edit listing"
                            }
                            disabled={p.isDemo}
                            onClick={() =>
                              !p.isDemo &&
                              navigate(`/agent/edit-property/${p.id}`)
                            }
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            className="text-gray-400 hover:text-red-600 disabled:opacity-30"
                            title={
                              p.isDemo
                                ? "Demo data — not deletable"
                                : "Delete listing"
                            }
                            disabled={p.isDemo || deletingId === p.id}
                            onClick={() => handleDelete(p, p.title)}
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
        </>
      )}
    </div>
  );
}