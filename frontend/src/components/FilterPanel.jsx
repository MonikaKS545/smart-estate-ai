import { useState, useEffect } from "react";

/**
 * Structured filter sidebar. Filters live-update as the user changes
 * any control — no "Apply" button.
 *
 * Locality is derived from each property's `address` field (the
 * second-to-last comma-separated segment, since address is formatted
 * as "<street>, <locality>, <city>"). We don't have a separate
 * locality field in the data shape from the spec, so this reuses
 * `address` rather than inventing a new field Parts 1-4 don't expect.
 *
 * Props:
 *  - properties: full array of properties (used to derive locality list, price bounds)
 *  - onFilterChange: called with the filtered array whenever filters change
 */

function extractLocality(address) {
  const parts = address.split(",").map((p) => p.trim());
  // address format: "<street>, <locality>, <city>" -> take second-to-last part
  return parts.length >= 2 ? parts[parts.length - 2] : parts[0];
}

export default function FilterPanel({ properties, onFilterChange }) {
  const localities = [
    ...new Set(properties.map((p) => extractLocality(p.address))),
  ].sort();

  const [locality, setLocality] = useState("all");
  const [bhk, setBhk] = useState("all");
  const [status, setStatus] = useState("all");
  const [maxPrice, setMaxPrice] = useState(50000000); // 5 crore ceiling default

  useEffect(() => {
    let filtered = properties;

    if (locality !== "all") {
      filtered = filtered.filter(
        (p) => extractLocality(p.address) === locality
      );
    }
    if (bhk !== "all") {
      filtered = filtered.filter((p) => p.bhk === Number(bhk));
    }
    if (status !== "all") {
      filtered = filtered.filter((p) => p.status === status);
    }
    filtered = filtered.filter((p) => p.price <= maxPrice);

    onFilterChange(filtered);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locality, bhk, status, maxPrice, properties]);

  return (
    <div className="w-full sm:w-64 p-4 border border-gray-200 rounded-xl bg-white space-y-5">
      <h3 className="font-semibold text-gray-900">Filters</h3>

      <div>
        <label htmlFor="filter-locality" className="block text-sm font-medium text-gray-700 mb-1">
          Locality
        </label>
        <select
          id="filter-locality"
          name="locality"
          value={locality}
          onChange={(e) => setLocality(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
        >
          <option value="all">All localities</option>
          {localities.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="filter-bhk" className="block text-sm font-medium text-gray-700 mb-1">
          BHK
        </label>
        <select
          id="filter-bhk"
          name="bhk"
          value={bhk}
          onChange={(e) => setBhk(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
        >
          <option value="all">Any</option>
          <option value="1">1 BHK</option>
          <option value="2">2 BHK</option>
          <option value="3">3 BHK</option>
          <option value="4">4 BHK</option>
        </select>
      </div>

      <div>
        <label htmlFor="filter-status" className="block text-sm font-medium text-gray-700 mb-1">
          Status
        </label>
        <select
          id="filter-status"
          name="status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
        >
          <option value="all">All</option>
          <option value="available">Available</option>
          <option value="pending">Pending</option>
          <option value="sold">Sold</option>
        </select>
      </div>

      <div>
        <label htmlFor="filter-max-price" className="block text-sm font-medium text-gray-700 mb-1">
          Max Price: ₹{(maxPrice / 100000).toFixed(0)} L
        </label>
        <input
          id="filter-max-price"
          name="maxPrice"
          type="range"
          min="1000000"
          max="50000000"
          step="500000"
          value={maxPrice}
          onChange={(e) => setMaxPrice(Number(e.target.value))}
          className="w-full"
        />
      </div>
    </div>
  );
}