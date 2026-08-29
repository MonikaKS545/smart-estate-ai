import { useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { createMapMarkerIcon } from "../components/MapMarker";
import PropertyCard from "../components/PropertyCard";
import mockProperties from "../mocks/mockProperties";

/**
 * MapView page.
 *
 * Note on "click to detail": Part 1's router isn't set up yet, so
 * clicking a marker's "View Details" button can't literally navigate.
 * Instead it sets `selectedProperty` in local state, which renders a
 * PropertyCard below the map. Once routing exists, swap that click
 * handler for `navigate(`/property/${id}`)` — one line change.
 */
export default function MapView() {
  const [selectedProperty, setSelectedProperty] = useState(null);
  const isLoading = false;
  const error = null;

  // Center the map on the average of all property coordinates.
  const avgLat =
    mockProperties.reduce((sum, p) => sum + p.latitude, 0) /
    mockProperties.length;
  const avgLng =
    mockProperties.reduce((sum, p) => sum + p.longitude, 0) /
    mockProperties.length;

  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading map...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-600">
        Couldn't load the map. Please try again.
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Map View</h1>

      <div className="h-[500px] w-full rounded-xl overflow-hidden border border-gray-200">
        <MapContainer
          center={[avgLat, avgLng]}
          zoom={12}
          scrollWheelZoom={true}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {mockProperties.map((property) => (
            <Marker
              key={property.id}
              position={[property.latitude, property.longitude]}
              icon={createMapMarkerIcon(property.status)}
            >
              <Popup>
                <div className="space-y-1">
                  <p className="font-semibold">{property.title}</p>
                  <p className="text-sm text-gray-600">
                    ₹{(property.price / 100000).toFixed(0)} L · {property.bhk} BHK
                  </p>
                  <button
                    onClick={() => setSelectedProperty(property)}
                    className="text-sm text-blue-600 font-medium underline"
                  >
                    View Details
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {selectedProperty && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">
            Selected Property
          </h3>
          <div className="max-w-sm">
            <PropertyCard property={selectedProperty} />
          </div>
        </div>
      )}
    </div>
  );
}