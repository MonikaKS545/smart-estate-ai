import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Users, Building2, Flag, ShieldAlert } from "lucide-react";
import mockProperties from "../mocks/mockProperties";

/**
 * AdminDashboard page.
 *
 * Note: the spec's mocks/ folder (per its own file list) has no
 * mockUsers.js or mockReports.js, so small mock datasets for both are
 * defined here — same approach as the fraud data on PropertyDetail
 * and the verification result on DocumentVerification — rather than
 * adding unlisted mock files.
 */

const mockUsers = [
  { id: 1, name: "Ramesh Kumar", role: "agent", joined: "2024-01-12" },
  { id: 2, name: "Priya Sharma", role: "buyer", joined: "2024-03-05" },
  { id: 3, name: "Anil Verma", role: "agent", joined: "2024-02-20" },
  { id: 4, name: "Divya Iyer", role: "buyer", joined: "2024-04-18" },
  { id: 5, name: "Suresh Rao", role: "admin", joined: "2023-11-01" },
];

const mockReports = [
  {
    id: 1,
    propertyTitle: "3BHK Modern Apartment in Koramangala",
    reason: "Suspicious document mismatch",
    status: "open",
  },
  {
    id: 2,
    propertyTitle: "1BHK Compact Studio in HSR Layout",
    reason: "Duplicate listing reported",
    status: "resolved",
  },
  {
    id: 3,
    propertyTitle: "Luxury 4BHK Penthouse in Indiranagar",
    reason: "Price mismatch with market data",
    status: "open",
  },
];

const STATUS_COLORS = {
  available: "#16a34a",
  sold: "#dc2626",
  pending: "#ca8a04",
};

export default function AdminDashboard() {
  const [users] = useState(mockUsers);
  const [reports] = useState(mockReports);

  const statusCounts = mockProperties.reduce((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1;
    return acc;
  }, {});
  const statusData = Object.entries(statusCounts).map(([status, count]) => ({
    name: status,
    count,
  }));

  const openReportsCount = reports.filter((r) => r.status === "open").length;

  const stats = [
    { label: "Total Users", value: users.length, Icon: Users },
    { label: "Total Listings", value: mockProperties.length, Icon: Building2 },
    { label: "Open Reports", value: openReportsCount, Icon: Flag },
  ];

  return (
    <div className="p-6 md:p-8 space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stats.map(({ label, value, Icon }) => (
          <div
            key={label}
            className="border border-gray-200 rounded-xl p-4 flex items-center gap-3"
          >
            <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center">
              <Icon size={18} className="text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">{label}</p>
              <p className="text-xl font-bold text-gray-900">{value}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="border border-gray-200 rounded-xl p-4">
        <h3 className="font-semibold text-gray-900 mb-3">
          Listings by Status (Platform-wide)
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={statusData}>
            <XAxis dataKey="name" className="capitalize" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {statusData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={STATUS_COLORS[entry.name] || "#9ca3af"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <h3 className="font-semibold text-gray-900 p-4 border-b border-gray-100">
            Users
          </h3>
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-500">
                  Name
                </th>
                <th className="text-left p-3 font-medium text-gray-500">
                  Role
                </th>
                <th className="text-left p-3 font-medium text-gray-500">
                  Joined
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-gray-100">
                  <td className="p-3 text-gray-900">{u.name}</td>
                  <td className="p-3 capitalize text-gray-700">{u.role}</td>
                  <td className="p-3 text-gray-500">{u.joined}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <h3 className="font-semibold text-gray-900 p-4 border-b border-gray-100">
            Reports
          </h3>
          <ul className="divide-y divide-gray-100">
            {reports.map((r) => (
              <li key={r.id} className="p-3 flex items-start gap-2 text-sm">
                <ShieldAlert
                  size={16}
                  className={
                    r.status === "open"
                      ? "text-red-500 shrink-0 mt-0.5"
                      : "text-gray-300 shrink-0 mt-0.5"
                  }
                />
                <div>
                  <p className="text-gray-900 font-medium">
                    {r.propertyTitle}
                  </p>
                  <p className="text-gray-500 text-xs">{r.reason}</p>
                </div>
                <span
                  className={`ml-auto text-xs font-medium capitalize px-2 py-0.5 rounded-full ${
                    r.status === "open"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {r.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}