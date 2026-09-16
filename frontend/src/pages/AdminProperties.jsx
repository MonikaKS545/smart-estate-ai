import { useState, useEffect } from "react";
import { CheckCircle2, XCircle, Building2 } from "lucide-react";
import client from "../api/client";

const STATUS_TABS = ["pending", "approved", "rejected", "sold"];

const STATUS_BADGE = {
  pending: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-gray-100 text-gray-500",
  sold: "bg-red-100 text-red-700",
};

export default function AdminProperties() {
  const [activeTab, setActiveTab] = useState("pending");
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actingId, setActingId] = useState(null);

  const fetchProperties = async (status) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await client.get("/admin/properties", {
        params: { status },
      });
      setProperties(data.properties || []);
    } catch (err) {
      console.error(err);
      setError("Couldn't load properties. Please refresh and try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProperties(activeTab);
  }, [activeTab]);

  const updateStatus = async (propertyId, newStatus) => {
    setActingId(propertyId);
    try {
      await client.put(`/admin/properties/${propertyId}/status`, {
        status: newStatus,
      });
      // Remove it from the current tab's list since its status just changed
      setProperties((prev) => prev.filter((p) => p.id !== propertyId));
    } catch (err) {
      console.error(err);
      alert("Failed to update status. Please try again.");
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center">
          <Building2 size={18} className="text-blue-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Property Verification
        </h1>
      </div>

      <div className="flex gap-2 border-b border-gray-200">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
              activeTab === tab
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-800"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-500 text-sm">Loading...</p>
      ) : properties.length === 0 ? (
        <div className="border border-gray-200 rounded-xl p-8 text-center text-gray-500">
          No {activeTab} properties right now.
        </div>
      ) : (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-500">Title</th>
                <th className="text-left p-3 font-medium text-gray-500">Type</th>
                <th className="text-left p-3 font-medium text-gray-500">City</th>
                <th className="text-left p-3 font-medium text-gray-500">Price</th>
                <th className="text-left p-3 font-medium text-gray-500">Status</th>
                <th className="text-left p-3 font-medium text-gray-500">Submitted</th>
                <th className="text-left p-3 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {properties.map((p) => (
                <tr key={p.id} className="border-t border-gray-100">
                  <td className="p-3 text-gray-900">{p.title}</td>
                  <td className="p-3 text-gray-700 capitalize">
                    {p.property_type || "-"} · {p.listing_type}
                  </td>
                  <td className="p-3 text-gray-700">{p.city || "-"}</td>
                  <td className="p-3 text-gray-700">
                    {p.listing_type === "rent"
                      ? `₹${Number(p.price).toLocaleString("en-IN")}/mo`
                      : `₹${(p.price / 100000).toFixed(0)} L`}
                  </td>
                  <td className="p-3">
                    <span
                      className={`text-xs font-medium capitalize px-2 py-0.5 rounded-full ${STATUS_BADGE[p.status]}`}
                    >
                      {p.status}
                    </span>
                  </td>
                  <td className="p-3 text-gray-500 text-xs">
                    {p.created_at
                      ? new Date(p.created_at).toLocaleDateString()
                      : "-"}
                  </td>
                  <td className="p-3">
                    {activeTab === "pending" ? (
                      <div className="flex gap-2">
                        <button
                          className="flex items-center gap-1 text-green-600 hover:text-green-700 disabled:opacity-40 text-xs font-medium"
                          disabled={actingId === p.id}
                          onClick={() => updateStatus(p.id, "approved")}
                        >
                          <CheckCircle2 size={14} />
                          Approve
                        </button>
                        <button
                          className="flex items-center gap-1 text-red-600 hover:text-red-700 disabled:opacity-40 text-xs font-medium"
                          disabled={actingId === p.id}
                          onClick={() => updateStatus(p.id, "rejected")}
                        >
                          <XCircle size={14} />
                          Reject
                        </button>
                      </div>
                    ) : (
                      <span className="text-gray-300 text-xs">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}