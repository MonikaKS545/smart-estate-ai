import { useState, useEffect } from "react";
import { ShieldCheck, ArrowUpDown } from "lucide-react";
import { computeTrustScore } from "../utils/trustScore";

/**
 * FilterPanel component with Trust Score sorting and verification filtering.
 *
 * Requirements fulfilled:
 * - "Sort by Trust Score" option (Requirement 5)
 * - "Filter: Verified listings only" checkbox (Requirement 5)
 * - Locality, BHK, Status, and Price filters
 */

function extractLocality(address) {
  if (!address) return "Other";
  const parts = address.split(",").map((p) => p.trim());
  return parts.length >= 2 ? parts[parts.length - 2] : parts[0];
}

export default function FilterPanel({ properties, onFilterChange }) {
  const localities = [
    ...new Set(properties.map((p) => extractLocality(p.address))),
  ].sort();

  const [locality, setLocality] = useState("all");
  const [bhk, setBhk] = useState("all");
  const [status, setStatus] = useState("all");
  const [maxPrice, setMaxPrice] = useState(50000000); // 5 crore default
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [sortBy, setSortBy] = useState("trust_desc"); // Default to Sort by Trust Score

  useEffect(() => {
    let filtered = [...properties];

    // Locality Filter
    if (locality !== "all") {
      filtered = filtered.filter(
        (p) => extractLocality(p.address) === locality
      );
    }

    // BHK Filter
    if (bhk !== "all") {
      filtered = filtered.filter((p) => p.bhk === Number(bhk));
    }

    // Status Filter
    if (status !== "all") {
      filtered = filtered.filter((p) => p.status === status);
    }

    // Max Price Filter
    filtered = filtered.filter((p) => p.price <= maxPrice);

    // Verified Listings Only Filter (Requirement 5: score >= 75 / High Tier)
    if (verifiedOnly) {
      filtered = filtered.filter((p) => {
        const score = typeof p.trust_score === "number"
          ? p.trust_score
          : computeTrustScore(p.trust_signals).score;
        return score >= 75;
      });
    }

    // Sorting (Requirement 5: Sort by Trust Score)
    if (sortBy === "trust_desc") {
      filtered.sort((a, b) => {
        const scoreA = typeof a.trust_score === "number"
          ? a.trust_score
          : computeTrustScore(a.trust_signals).score;
        const scoreB = typeof b.trust_score === "number"
          ? b.trust_score
          : computeTrustScore(b.trust_signals).score;
        return scoreB - scoreA;
      });
    } else if (sortBy === "price_asc") {
      filtered.sort((a, b) => a.price - b.price);
    } else if (sortBy === "price_desc") {
      filtered.sort((a, b) => b.price - a.price);
    }

    onFilterChange(filtered);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locality, bhk, status, maxPrice, verifiedOnly, sortBy, properties]);

  return (
    <div className="w-full sm:w-64 p-4 border border-gray-200 rounded-xl bg-white space-y-5 shadow-xs">
      <div className="flex items-center justify-between border-b border-gray-100 pb-2">
        <h3 className="font-semibold text-gray-900">Filters & Sorting</h3>
      </div>

      {/* Sort Control */}
      <div>
        <label htmlFor="filter-sort" className="flex items-center gap-1.5 text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
          <ArrowUpDown size={13} className="text-gray-500" />
          Sort By
        </label>
        <select
          id="filter-sort"
          name="sortBy"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:outline-hidden cursor-pointer"
        >
          <option value="trust_desc">Trust Score: High to Low</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="default">Default Listing Order</option>
        </select>
      </div>

      {/* Verified Only Checkbox Filter (Requirement 5) */}
      <div className="pt-1 pb-2 border-y border-gray-100">
        <label
          htmlFor="filter-verified-only"
          className="flex items-start gap-2.5 cursor-pointer select-none group"
        >
          <input
            id="filter-verified-only"
            type="checkbox"
            checked={verifiedOnly}
            onChange={(e) => setVerifiedOnly(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
          />
          <div className="text-xs">
            <div className="font-semibold text-gray-800 group-hover:text-emerald-700 flex items-center gap-1">
              <ShieldCheck size={14} className="text-emerald-600" />
              Verified listings only
            </div>
            <p className="text-gray-500 text-[11px] leading-tight mt-0.5">
              High confidence score (75+)
            </p>
          </div>
        </label>
      </div>

      {/* Locality */}
      <div>
        <label htmlFor="filter-locality" className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
          Locality
        </label>
        <select
          id="filter-locality"
          name="locality"
          value={locality}
          onChange={(e) => setLocality(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:outline-hidden cursor-pointer"
        >
          <option value="all">All localities</option>
          {localities.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </div>

      {/* BHK */}
      <div>
        <label htmlFor="filter-bhk" className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
          BHK
        </label>
        <select
          id="filter-bhk"
          name="bhk"
          value={bhk}
          onChange={(e) => setBhk(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:outline-hidden cursor-pointer"
        >
          <option value="all">Any BHK</option>
          <option value="1">1 BHK</option>
          <option value="2">2 BHK</option>
          <option value="3">3 BHK</option>
          <option value="4">4 BHK</option>
        </select>
      </div>

      {/* Status */}
      <div>
        <label htmlFor="filter-status" className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
          Listing Status
        </label>
        <select
          id="filter-status"
          name="status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:outline-hidden cursor-pointer"
        >
          <option value="all">All</option>
          <option value="available">Available</option>
          <option value="pending">Pending</option>
          <option value="sold">Sold</option>
        </select>
      </div>

      {/* Max Price Slider */}
      <div>
        <div className="flex items-center justify-between text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
          <span>Max Price</span>
          <span className="text-blue-600 font-bold lowercase">₹{(maxPrice / 100000).toFixed(0)} L</span>
        </div>
        <input
          id="filter-max-price"
          name="maxPrice"
          type="range"
          min="1000000"
          max="50000000"
          step="500000"
          value={maxPrice}
          onChange={(e) => setMaxPrice(Number(e.target.value))}
          className="w-full accent-blue-600 cursor-pointer"
        />
      </div>
    </div>
  );
}