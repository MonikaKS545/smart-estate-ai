import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { createMapMarkerIcon } from "../components/MapMarker";
import PropertyCard from "../components/PropertyCard";
import client from "../api/client";

export default function MapView() {
  const navigate = useNavigate();

  const [properties, setProperties] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadProperties() {
      try {
        const res = await client.get("/properties");
        // Only properties with real coordinates AND not rejected
        // should appear on the public map.
        const withCoords = res.data.properties.filter(
          (p) =>
            p.latitude != null &&
            p.longitude != null &&
            p.status !== "rejected"
        );
        setProperties(withCoords);
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    }
    loadProperties();
  }, []);

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

  if (properties.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        No properties with location data yet.
      </div>
    );
  }

  const avgLat =
    properties.reduce((sum, p) => sum + p.latitude, 0) / properties.length;
  const avgLng =
    properties.reduce((sum, p) => sum + p.longitude, 0) / properties.length;

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
          {properties.map((property) => (
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
            <PropertyCard
              property={selectedProperty}
              onClick={() => navigate(`/property/${selectedProperty.id}`)}
            />
          </div>
        </div>
      )}
    </div>
  );
}