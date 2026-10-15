import { useState } from "react";
import { MapPin, BedDouble, Bath, Square, Phone } from "lucide-react";
import TrustScoreBadge from "../components/TrustScoreBadge";
import AnalysisPanel from "../components/AnalysisPanel";
import PropertyCard from "../components/PropertyCard";
import mockProperties from "../mocks/mockProperties";
import mockAnalysis from "../mocks/mockAnalysis";
import mockRecommendations from "../mocks/mockRecommendations";

/**
 * PropertyDetail page.
 *
 * Note on fraud/trust data: the spec's `fraud` shape ({ trust_score,
 * risk_level, reasons }) is separate from `analysis`, but the mocks/
 * folder (per the spec's own file list) has no mockFraud.js. We reuse
 * `fraud_score` from the analysis object to drive TrustScoreBadge
 * instead of inventing an extra mock file — swap this for a real
 * fraud endpoint call later, it's a one-line change.
 *
 * Note on routing: Part 1's router isn't set up yet, so `propertyId`
 * is a plain prop for now (defaults to the first mock property).
 * Once real routing exists, this becomes `const { id } = useParams()`.
 */
export default function PropertyDetail({ propertyId = 1 }) {
  const [activeImage, setActiveImage] = useState(0);

  const isLoading = false;
  const error = null;

  const property = mockProperties.find((p) => p.id === propertyId);
  const analysis = mockAnalysis[propertyId];
  const similar = mockRecommendations[propertyId] || [];

  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-600">
        Couldn't load this property. Please try again.
      </div>
    );
  }

  if (!property) {
    return (
      <div className="p-8 text-center text-gray-500">
        Property not found.
      </div>
    );
  }

  const formattedPrice = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(property.price);

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Image gallery */}
      <div>
        <div className="h-80 w-full bg-gray-100 rounded-xl overflow-hidden">
          <img
            src={property.images[activeImage]}
            alt={property.title}
            className="h-full w-full object-cover"
          />
        </div>
        {property.images.length > 1 && (
          <div className="flex gap-2 mt-2">
            {property.images.map((img, i) => (
              <button
                key={i}
                onClick={() => setActiveImage(i)}
                className={`h-16 w-16 rounded-lg overflow-hidden border-2 ${
                  i === activeImage ? "border-blue-600" : "border-transparent"
                }`}
              >
                <img
                  src={img}
                  alt={`${property.title} ${i + 1}`}
                  className="h-full w-full object-cover"
                />
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: main details */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {property.title}
            </h1>
            <p className="flex items-center gap-1 text-gray-500 mt-1">
              <MapPin size={16} />
              {property.address}
            </p>
          </div>

          <p className="text-3xl font-bold text-gray-900">
            {formattedPrice}
          </p>

          <div className="flex items-center gap-6 text-gray-700 border-y border-gray-100 py-3">
            <span className="flex items-center gap-1.5">
              <BedDouble size={18} />
              {property.bhk} BHK
            </span>
            <span className="flex items-center gap-1.5">
              <Bath size={18} />
              {property.bathrooms} Bath
            </span>
            <span className="flex items-center gap-1.5">
              <Square size={18} />
              {property.area_sqft} sqft
            </span>
          </div>

          {analysis && (
            <TrustScoreBadge score={analysis.fraud_score} />
          )}

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Amenities</h3>
            <div className="flex flex-wrap gap-2">
              {property.amenities.map((a) => (
                <span
                  key={a}
                  className="px-3 py-1 rounded-full bg-gray-100 text-sm text-gray-700"
                >
                  {a}
                </span>
              ))}
            </div>
          </div>

          <AnalysisPanel analysis={analysis} />
        </div>

        {/* Right: contact seller */}
        <div className="space-y-4">
          <div className="p-4 border border-gray-200 rounded-xl bg-white space-y-3">
            <h3 className="font-semibold text-gray-900">Contact Seller</h3>
            <button className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700">
              <Phone size={16} />
              Contact Seller
            </button>
            <p className="text-xs text-gray-400 text-center">
              Contact details are shared once you reach out.
            </p>
          </div>
        </div>
      </div>

      {/* Similar properties */}
      {similar.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">
            Similar Properties
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {similar.map((rec) => {
              const simProperty = mockProperties.find(
                (p) => p.id === rec.property_id
              );
              if (!simProperty) return null;
              return (
                <PropertyCard
                  key={rec.property_id}
                  property={simProperty}
                  matchScore={rec.match_score}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}