import PropertyCard from "../components/PropertyCard";
import mockProperties from "../mocks/mockProperties";

/**
 * Favorites ("My Properties") page.
 *
 * Props:
 *  - propertyIds: array of favorited property ids. Defaults to a
 *    small demo set so this page is testable standalone; in practice
 *    PropertySearch.jsx will pass down the user's real selections
 *    (heart-toggle state, same lifted-state pattern as Compare).
 *  - onRemove: optional handler called with a property id when the
 *    user clicks "Remove" on a saved property.
 */
export default function Favorites({ propertyIds = [1, 5, 9], onRemove }) {
  const isLoading = false;
  const error = null;

  const properties = propertyIds
    .map((id) => mockProperties.find((p) => p.id === id))
    .filter(Boolean);

  if (isLoading) {
    return (
      <div className="p-8 text-center text-gray-500">
        Loading your saved properties...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-600">
        Couldn't load your favorites. Please try again.
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Properties</h1>

      {properties.length === 0 ? (
        <div className="text-center text-gray-500 py-12 border border-gray-200 rounded-xl">
          You haven't saved any properties yet. Browse listings and tap the
          heart icon to save one here.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {properties.map((property) => (
            <div key={property.id} className="space-y-2">
              <PropertyCard property={property} />
              {onRemove && (
                <button
                  onClick={() => onRemove(property.id)}
                  className="w-full text-sm text-red-600 hover:text-red-700 font-medium"
                >
                  Remove from Favorites
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}