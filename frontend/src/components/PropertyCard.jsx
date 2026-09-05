import { MapPin, BedDouble, Bath, Square } from "lucide-react";

/**
 * Reusable property card.
 * Props:
 *  - property: the property object (see mockProperties shape)
 *  - onClick: optional handler, e.g. navigate to detail page
 *  - matchScore: optional number (0-100) to show a "Match" badge (used by recommendations/chat)
 */
export default function PropertyCard({ property, onClick, matchScore }) {
  const {
    title,
    price,
    area_sqft,
    bhk,
    bathrooms,
    address,
    images,
    status,
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
      className="cursor-pointer rounded-xl border border-line bg-white shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 overflow-hidden"
    >
      <div className="relative h-44 w-full bg-panel">
        {images && images.length > 0 ? (
          <img
            src={images[0]}
            alt={title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sage text-sm">
            No image available
          </div>
        )}

        <span
          className={`absolute top-2 left-2 text-xs font-medium px-2 py-1 rounded-full capitalize ${
            statusStyles[status] || "bg-gray-100 text-gray-800"
          }`}
        >
          {status}
        </span>

        {typeof matchScore === "number" && (
          <span className="absolute top-2 right-2 text-xs font-semibold px-2 py-1 rounded-full bg-ai text-white">
            {matchScore}% Match
          </span>
        )}
      </div>

      <div className="p-4 space-y-2">
        <h3 className="font-serif font-semibold text-ink line-clamp-1">{title}</h3>

        <p className="text-lg font-bold text-ink">{formattedPrice}</p>

        <p className="flex items-center gap-1 text-sm text-sage">
          <MapPin size={14} />
          <span className="line-clamp-1">{address}</span>
        </p>

        <div className="flex items-center gap-4 text-sm text-sage pt-1 border-t border-line mt-1 pt-2">
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