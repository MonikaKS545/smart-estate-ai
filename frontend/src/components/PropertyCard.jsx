import { MapPin, BedDouble, Bath, Square } from "lucide-react";
import TrustScoreBadge from "./TrustScoreBadge";

/**
 * Reusable property card with integrated Trust Score Badge & Popover.
 * Props:
 *  - property: the property object (with optional trust_signals / trust_score)
 *  - onClick: optional handler, e.g. navigate to detail page
 *  - matchScore: optional number (0-100) to show a "Match" badge
 */
export default function PropertyCard({ property, onClick, matchScore }) {
  const {
    id,
    title,
    price,
    area_sqft,
    bhk,
    bathrooms,
    address,
    images,
    status,
    trust_signals,
    trust_score,
  } = property;

  const formattedPrice = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(price);

  const statusStyles = {
    available: "bg-green-100 text-green-800",
    approved: "bg-green-100 text-green-800",
    sold: "bg-red-100 text-red-800",
    pending: "bg-yellow-100 text-yellow-800",
  };

  return (
    <div
      onClick={onClick}
      className="group relative cursor-pointer rounded-xl border border-line bg-white shadow-xs hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
    >
      <div className="relative h-44 w-full bg-panel rounded-t-xl overflow-hidden">
        {images && images.length > 0 ? (
          <img
            src={images[0]}
            alt={title}
            className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sage text-sm">
            No image available
          </div>
        )}

        <span
          className={`absolute top-2 left-2 text-xs font-medium px-2 py-1 rounded-full capitalize shadow-xs ${
            statusStyles[status] || "bg-gray-100 text-gray-800"
          }`}
        >
          {status}
        </span>

        {typeof matchScore === "number" && (
          <span className="absolute top-2 right-2 text-xs font-semibold px-2 py-1 rounded-full bg-ai text-white shadow-xs">
            {matchScore}% Match
          </span>
        )}
      </div>

      <div className="p-4 space-y-2">
        <h3 className="font-serif font-semibold text-ink line-clamp-1" title={title}>
          {title}
        </h3>

        <div className="flex items-center justify-between gap-2 pt-0.5">
          <p className="text-lg font-bold text-ink">{formattedPrice}</p>
          <TrustScoreBadge
            signals={trust_signals}
            score={trust_score}
            propertyId={id}
          />
        </div>

        <p className="flex items-center gap-1 text-sm text-sage">
          <MapPin size={14} className="shrink-0" />
          <span className="line-clamp-1">{address}</span>
        </p>

        <div className="flex items-center gap-4 text-sm text-sage border-t border-line mt-1 pt-2">
          <span className="flex items-center gap-1">
            <BedDouble size={14} />
            {bhk} BHK
          </span>
          <span className="flex items-center gap-1">
            <Bath size={14} />
            {bathrooms}
          </span>
          <span className="flex items-center gap-1">
            <Square size={14} />
            {area_sqft} sqft
          </span>
        </div>
      </div>
    </div>
  );
}