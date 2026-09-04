import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Check, Heart } from "lucide-react";
import PropertyCard from "../components/PropertyCard";
import FilterPanel from "../components/FilterPanel";
import NaturalLanguageSearchBar from "../components/NaturalLanguageSearchBar";
import client from "../api/client";

export default function PropertySearch() {
  const navigate = useNavigate();

  const [allProperties, setAllProperties] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [filteredResults, setFilteredResults] = useState([]);
  const [displayedResults, setDisplayedResults] = useState([]);

  const [compareIds, setCompareIds] = useState([]);

  const [favoriteMap, setFavoriteMap] = useState({}); // property_id -> favorite_id

  useEffect(() => {
    async function loadProperties() {
      try {
        const res = await client.get("/properties");
        setAllProperties(res.data.properties);
        setFilteredResults(res.data.properties);
        setDisplayedResults(res.data.properties);
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    }
    loadProperties();

    async function loadFavorites() {
      try {
        const res = await client.get("/favorites");
        const map = {};
        res.data.properties.forEach((p) => {
          if (p.favorite_id) map[p.id] = p.favorite_id;
        });
        setFavoriteMap(map);
      } catch {
        // not logged in or no favorites yet — fine, just leave empty
      }
    }
    loadFavorites();
  }, []);

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

  async function toggleFavorite(id) {
    const existingFavoriteId = favoriteMap[id];
    if (existingFavoriteId) {
      try {
        await client.delete(`/favorites/${existingFavoriteId}`);
        setFavoriteMap((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
      } catch (err) {
        console.error("Failed to remove favorite", err);
      }
    } else {
      try {
        const res = await client.post("/favorites", { property_id: id });
        setFavoriteMap((prev) => ({ ...prev, [id]: res.data.id }));
      } catch (err) {
        console.error("Failed to add favorite", err);
      }
    }
  }

  function goToCompare() {
    navigate(`/compare?ids=${compareIds.join(",")}`);
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
        {Object.keys(favoriteMap).length > 0 && (
          <span className="text-sm text-gray-500">
            {Object.keys(favoriteMap).length} saved
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
          properties={allProperties}
          onFilterChange={handleFilterChange}
        />

        <div className="flex-1 space-y-4">
          {compareIds.length >= 2 && (
            <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
              <span className="text-sm text-blue-800">
                {compareIds.length} properties selected
              </span>
              <button
                onClick={goToCompare}
                className="text-sm font-medium text-blue-700 underline"
              >
                Compare Selected
              </button>
            </div>
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
                const isFavorited = Boolean(favoriteMap[property.id]);
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
                    <PropertyCard
                      property={property}
                      onClick={() => navigate(`/property/${property.id}`)}
                    />
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