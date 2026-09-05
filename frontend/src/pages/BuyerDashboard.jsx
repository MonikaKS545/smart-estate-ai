import { Construction } from "lucide-react";

function BuyerDashboard() {
  return (
    <div className="animate-fade-in-up flex flex-col items-center justify-center text-center py-24 px-6">
      <div className="w-14 h-14 rounded-full bg-ai/10 flex items-center justify-center mb-4">
        <Construction size={26} className="text-ai" />
      </div>
      <h2 className="font-serif text-2xl font-semibold text-ink mb-2">
        Buyer dashboard
      </h2>
      <p className="text-sage text-sm">
        This is coming soon. Check back shortly.
      </p>
    </div>
  );
}

export default BuyerDashboard;