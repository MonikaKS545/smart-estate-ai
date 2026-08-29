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
    sold: "bg-red-100 text-red-800",
    pending: "bg-yellow-100 text-yellow-800",
  };

  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow overflow-hidden"
    >
      <div className="relative h-44 w-full bg-gray-100">
        {images && images.length > 0 ? (
          <img
            src={images[0]}
            alt={title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-gray-400 text-sm">
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
          <span className="absolute top-2 right-2 text-xs font-semibold px-2 py-1 rounded-full bg-blue-600 text-white">
            {matchScore}% Match
          </span>
        )}
      </div>

      <div className="p-4 space-y-2">
        <h3 className="font-semibold text-gray-900 line-clamp-1">{title}</h3>

        <p className="text-lg font-bold text-gray-900">{formattedPrice}</p>

        <p className="flex items-center gap-1 text-sm text-gray-500">
          <MapPin size={14} />
          <span className="line-clamp-1">{address}</span>
        </p>

        <div className="flex items-center gap-4 text-sm text-gray-600 pt-1">
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
