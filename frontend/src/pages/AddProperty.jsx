import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ImagePlus,
  X,
  ArrowLeft,
  Home,
  MapPin,
  Camera,
  IndianRupee,
} from "lucide-react";
import client from "../api/client";

const PROPERTY_TYPES = [
  "Apartment",
  "Villa",
  "Independent House",
  "Plot/Land",
  "Commercial Property",
  "Agricultural Land",
];

const FURNISHING_OPTIONS = ["Unfurnished", "Semi-Furnished", "Fully Furnished"];

const initialForm = {
  title: "",
  description: "",
  property_type: "",
  listing_type: "buy",
  price: "",
  area_sqft: "",
  bhk: "",
  bathrooms: "",
  floor: "",
  total_floors: "",
  property_age_years: "",
  furnishing: "",
  parking: false,
  latitude: "",
  longitude: "",
  address: "",
  city: "",
};

const inputClass =
  "w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all";
const labelClass = "block mb-1.5 text-sm font-medium text-gray-700";

const SECTION_THEMES = {
  blue: {
    iconBg: "bg-blue-50",
    iconColor: "text-blue-600",
    topBar: "bg-blue-500",
  },
  emerald: {
    iconBg: "bg-emerald-50",
    iconColor: "text-emerald-600",
    topBar: "bg-emerald-500",
  },
  amber: {
    iconBg: "bg-amber-50",
    iconColor: "text-amber-600",
    topBar: "bg-amber-500",
  },
};

function Section({ title, subtitle, icon: Icon, color, children }) {
  const theme = SECTION_THEMES[color];
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <div className={`h-1.5 ${theme.topBar}`} />
      <div className="p-6 space-y-5">
        <div className="flex items-center gap-3">
          <div
            className={`h-10 w-10 rounded-lg ${theme.iconBg} flex items-center justify-center shrink-0`}
          >
            <Icon size={18} className={theme.iconColor} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{title}</h3>
            {subtitle && (
              <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}

export default function AddProperty() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [images, setImages] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files || []);
    const newImages = files.map((file) => ({
      file,
      previewUrl: URL.createObjectURL(file),
    }));
    setImages((prev) => [...prev, ...newImages]);
    e.target.value = "";
  };

  const removeImage = (index) => {
    setImages((prev) => {
      const updated = [...prev];
      URL.revokeObjectURL(updated[index].previewUrl);
      updated.splice(index, 1);
      return updated;
    });
  };

  const buildPayload = () => {
    const numericFields = [
      "price",
      "area_sqft",
      "bhk",
      "bathrooms",
      "floor",
      "total_floors",
      "property_age_years",
      "latitude",
      "longitude",
    ];

    const payload = { ...form };
    numericFields.forEach((field) => {
      if (payload[field] === "" || payload[field] === null) {
        delete payload[field];
      } else {
        payload[field] = Number(payload[field]);
      }
    });

    ["description", "property_type", "furnishing", "address", "city"].forEach(
      (field) => {
        if (payload[field] === "") delete payload[field];
      }
    );

    return payload;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.title.trim() || !form.price) {
      setError("Title and price are required.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = buildPayload();
      const { data: newProperty } = await client.post("/properties", payload);

      for (const img of images) {
        const formData = new FormData();
        formData.append("file", img.file);
        await client.post(`/properties/${newProperty.id}/images`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }

      navigate("/agent");
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Something went wrong while creating the property. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50">
      {/* Gradient header banner */}
      <div className="bg-gradient-to-r from-indigo-600 via-blue-600 to-blue-500 text-white">
        <div className="max-w-3xl mx-auto px-4 pt-6 pb-10">
          <Link
            to="/agent"
            className="inline-flex items-center gap-1.5 text-sm text-blue-100 hover:text-white mb-4"
          >
            <ArrowLeft size={15} />
            Back to dashboard
          </Link>
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-white/15 backdrop-blur flex items-center justify-center shrink-0">
              <Home size={22} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">List Your Property</h1>
              <p className="text-sm text-blue-100 mt-0.5">
                Reach verified buyers — reviewed before it goes live.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 -mt-6 pb-10">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-6 shadow-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <Section
            title="Basic Details"
            icon={IndianRupee}
            color="blue"
          >
            <div>
              <label className={labelClass}>Title *</label>
              <input
                type="text"
                name="title"
                value={form.title}
                onChange={handleChange}
                required
                placeholder="e.g. 3BHK Modern Apartment in Koramangala"
                className={inputClass}
              />
            </div>

            <div>
              <label className={labelClass}>Description</label>
              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                rows={4}
                placeholder="Describe the property — layout, condition, nearby landmarks..."
                className={inputClass}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Property Type</label>
                <select
                  name="property_type"
                  value={form.property_type}
                  onChange={handleChange}
                  className={inputClass}
                >
                  <option value="">Select type</option>
                  {PROPERTY_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className={labelClass}>Listing Type *</label>
                <select
                  name="listing_type"
                  value={form.listing_type}
                  onChange={handleChange}
                  required
                  className={inputClass}
                >
                  <option value="buy">Sale</option>
                  <option value="rent">Rent</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Price (₹) *</label>
                <input
                  type="number"
                  name="price"
                  value={form.price}
                  onChange={handleChange}
                  required
                  min="0"
                  placeholder="e.g. 9500000"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Area (sqft)</label>
                <input
                  type="number"
                  name="area_sqft"
                  value={form.area_sqft}
                  onChange={handleChange}
                  min="0"
                  className={inputClass}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Bedrooms (BHK)</label>
                <input
                  type="number"
                  name="bhk"
                  value={form.bhk}
                  onChange={handleChange}
                  min="0"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Bathrooms</label>
                <input
                  type="number"
                  name="bathrooms"
                  value={form.bathrooms}
                  onChange={handleChange}
                  min="0"
                  className={inputClass}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className={labelClass}>Floor</label>
                <input
                  type="number"
                  name="floor"
                  value={form.floor}
                  onChange={handleChange}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Total Floors</label>
                <input
                  type="number"
                  name="total_floors"
                  value={form.total_floors}
                  onChange={handleChange}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Property Age (yrs)</label>
                <input
                  type="number"
                  name="property_age_years"
                  value={form.property_age_years}
                  onChange={handleChange}
                  min="0"
                  className={inputClass}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 items-end">
              <div>
                <label className={labelClass}>Furnishing</label>
                <select
                  name="furnishing"
                  value={form.furnishing}
                  onChange={handleChange}
                  className={inputClass}
                >
                  <option value="">Select</option>
                  {FURNISHING_OPTIONS.map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-700 pb-2.5">
                <input
                  type="checkbox"
                  name="parking"
                  checked={form.parking}
                  onChange={handleChange}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                Parking available
              </label>
            </div>
          </Section>

          <Section title="Location" icon={MapPin} color="emerald">
            <div>
              <label className={labelClass}>Address</label>
              <input
                type="text"
                name="address"
                value={form.address}
                onChange={handleChange}
                className={inputClass}
              />
            </div>

            <div>
              <label className={labelClass}>City</label>
              <input
                type="text"
                name="city"
                value={form.city}
                onChange={handleChange}
                className={inputClass}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Latitude</label>
                <input
                  type="number"
                  step="any"
                  name="latitude"
                  value={form.latitude}
                  onChange={handleChange}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Longitude</label>
                <input
                  type="number"
                  step="any"
                  name="longitude"
                  value={form.longitude}
                  onChange={handleChange}
                  className={inputClass}
                />
              </div>
            </div>
          </Section>

          <Section
            title="Photos"
            subtitle="Add a few clear photos to help buyers picture the space."
            icon={Camera}
            color="amber"
          >
            <label
              htmlFor="image-upload"
              className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-amber-300 bg-amber-50/40 rounded-lg py-8 cursor-pointer hover:border-amber-400 hover:bg-amber-50 transition-colors"
            >
              <ImagePlus size={22} className="text-amber-500" />
              <span className="text-sm text-amber-700 font-medium">
                Click to upload photos
              </span>
              <input
                id="image-upload"
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageSelect}
                className="hidden"
              />
            </label>

            {images.length > 0 && (
              <div className="grid grid-cols-4 gap-3">
                {images.map((img, idx) => (
                  <div key={idx} className="relative group">
                    <img
                      src={img.previewUrl}
                      alt={`preview-${idx}`}
                      className="w-full h-24 object-cover rounded-lg border border-gray-200"
                    />
                    <button
                      type="button"
                      onClick={() => removeImage(idx)}
                      className="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-red-600 text-white flex items-center justify-center text-xs shadow-sm hover:bg-red-700"
                      title="Remove"
                    >
                      <X size={13} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Section>

          <div className="flex items-center gap-3 pt-2 pb-4">
            <button
              type="submit"
              disabled={submitting}
              className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-6 py-2.5 rounded-lg text-sm transition-all shadow-sm hover:shadow-md"
            >
              {submitting ? "Submitting..." : "Submit Property"}
            </button>
            <Link
              to="/agent"
              className="text-sm text-gray-500 hover:text-gray-900 px-4 py-2.5"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}