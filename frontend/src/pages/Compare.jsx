import ComparisonTable from "../components/ComparisonTable";
import mockProperties from "../mocks/mockProperties";

/**
 * Compare page.
 *
 * Props:
 *  - propertyIds: array of property ids to compare (2+ expected).
 *    Passed down from PropertySearch's checkbox selection.
 *  - onClose: optional handler to dismiss/collapse this view (used
 *    when rendered inline on PropertySearch).
 */
export default function Compare({ propertyIds = [], onClose }) {
  const properties = propertyIds
    .map((id) => mockProperties.find((p) => p.id === id))
    .filter(Boolean);

  if (properties.length < 2) {
    return (
      <div className="p-6 text-center text-gray-500 border border-gray-200 rounded-xl">
        Select at least 2 properties to compare.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">
          Comparing {properties.length} Properties
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Close
          </button>
        )}
      </div>
      <ComparisonTable properties={properties} />
    </div>
  );
}