HEAD
import { useState } from "react";
import { Check, Heart } from "lucide-react";
import PropertyCard from "../components/PropertyCard";
import FilterPanel from "../components/FilterPanel";
import NaturalLanguageSearchBar from "../components/NaturalLanguageSearchBar";
import Compare from "./Compare";
import mockProperties from "../mocks/mockProperties";

/**
 * PropertySearch page.
 *
 * Flow: FilterPanel narrows the full mock list down to `filteredResults`.
 * The search bar then searches WITHIN `filteredResults` (not the full
 * list), so filters and search narrow down together rather than
 * fighting each other. Changing a filter resets whatever the search
 * bar had narrowed down to.
 *
 * Compare: each card gets a checkbox (rendered here, not inside
 * PropertyCard, to keep that component general-purpose). Once 2+ are
 * checked, a "Compare Selected" button reveals the Compare page
 * inline below the grid — since there's no router yet to send users
 * to a real /compare route.
 *
 * Favorites: same lifted-state pattern as Compare — a heart-toggle
 * button per card, tracked here as `favoriteIds`. Once real routing
 * exists, this state (and Compare's compareIds) would move to a
 * shared context or be persisted to the backend instead of living
 * only in this page.
 */
export default function PropertySearch() {
  const [isLoading] = useState(false);
  const [error] = useState(null);

  const [filteredResults, setFilteredResults] = useState(mockProperties);
  const [displayedResults, setDisplayedResults] = useState(mockProperties);

  const [compareIds, setCompareIds] = useState([]);
  const [showCompare, setShowCompare] = useState(false);

  const [favoriteIds, setFavoriteIds] = useState([]);

  function handleFilterChange(filtered) {
    setFilteredResults(filtered);
    setDisplayedResults(filtered);
  }

  function handleSearchResults(results) {
    setDisplayedResults(results);
  }

  function toggleCompare(id) {
    setCompareIds((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    );
  }

  function toggleFavorite(id) {
    setFavoriteIds((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-600">
        Something went wrong loading properties. Please try again.
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">
          Find Your Property
        </h1>
        {favoriteIds.length > 0 && (
          <span className="text-sm text-gray-500">
            {favoriteIds.length} saved
          </span>
        )}
      </div>

      <div className="mb-6">
        <NaturalLanguageSearchBar
          properties={filteredResults}
          onResults={handleSearchResults}
        />
      </div>

      <div className="flex flex-col sm:flex-row gap-6">
        <FilterPanel
          properties={mockProperties}
          onFilterChange={handleFilterChange}
        />

        <div className="flex-1 space-y-4">
          {compareIds.length >= 2 && (
            <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
              <span className="text-sm text-blue-800">
                {compareIds.length} properties selected
              </span>
              <button
                onClick={() => setShowCompare((s) => !s)}
                className="text-sm font-medium text-blue-700 underline"
              >
                {showCompare ? "Hide Comparison" : "Compare Selected"}
              </button>
            </div>
          )}

          {showCompare && compareIds.length >= 2 && (
            <Compare
              propertyIds={compareIds}
              onClose={() => setShowCompare(false)}
            />
          )}

          {isLoading ? (
            <div className="text-center text-gray-500 py-12">
              Loading properties...
            </div>
          ) : displayedResults.length === 0 ? (
            <div className="text-center text-gray-500 py-12">
              No properties match your search. Try adjusting your filters.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {displayedResults.map((property) => {
                const isSelected = compareIds.includes(property.id);
                const isFavorited = favoriteIds.includes(property.id);
                return (
                  <div key={property.id} className="relative">
                    <div className="absolute top-2 right-2 z-10 flex gap-1.5">
                      <button
                        onClick={() => toggleFavorite(property.id)}
                        className="h-7 w-7 rounded-full bg-white shadow flex items-center justify-center"
                        title="Save to favorites"
                      >
                        <Heart
                          size={14}
                          className={
                            isFavorited
                              ? "fill-red-500 text-red-500"
                              : "text-gray-400"
                          }
                        />
                      </button>
                      <button
                        onClick={() => toggleCompare(property.id)}
                        className={`h-7 w-7 rounded-md border-2 flex items-center justify-center ${
                          isSelected
                            ? "bg-blue-600 border-blue-600"
                            : "bg-white border-gray-300"
                        }`}
                        title="Select for comparison"
                      >
                        {isSelected && (
                          <Check size={14} className="text-white" />
                        )}
                      </button>
                    </div>
                    <PropertyCard property={property} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
