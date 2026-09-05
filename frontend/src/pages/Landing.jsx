import { Link } from "react-router-dom";
import { Search, ShieldCheck, TrendingUp } from "lucide-react";

function Landing() {
  return (
    <div className="animate-fade-in-up">
      <div className="bg-ink rounded-b-2xl md:rounded-2xl md:mx-6 md:mt-6 px-6 py-16 md:py-24 text-center relative overflow-hidden">
        <div className="absolute -top-10 -right-10 w-44 h-44 rounded-full bg-clay/10"></div>
        <div className="relative max-w-2xl mx-auto">
          <h1 className="font-serif text-3xl md:text-4xl font-semibold text-white mb-3">
            Find your next home in Bengaluru
          </h1>
          <p className="text-line text-base md:text-lg mb-8">
            AI-matched listings, verified documents, real prices.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link
              to="/search"
              className="inline-block bg-clay hover:bg-clay-dark text-ink font-semibold px-6 py-3 rounded-lg transition-colors"
            >
              Start searching
            </Link>
            <Link
              to="/chat"
              className="inline-block bg-transparent border border-white/30 hover:border-white text-white font-semibold px-6 py-3 rounded-lg transition-colors"
            >
              Ask the AI assistant
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-16 text-center">
        <h2 className="font-serif text-2xl font-semibold text-ink mb-2">
          Why SmartEstate AI
        </h2>
        <p className="text-sage text-sm mb-10">
          Built for how people actually search for homes
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          <div className="bg-white border border-line rounded-xl p-5 shadow-sm">
            <div className="w-10 h-10 rounded-lg bg-ai/10 flex items-center justify-center mb-3">
              <Search size={18} className="text-ai" />
            </div>
            <h3 className="font-semibold text-ink text-sm mb-1">AI-matched search</h3>
            <p className="text-sage text-xs">
              Describe what you want in plain language, get real matching listings back.
            </p>
          </div>

          <div className="bg-white border border-line rounded-xl p-5 shadow-sm">
            <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center mb-3">
              <ShieldCheck size={18} className="text-success" />
            </div>
            <h3 className="font-semibold text-ink text-sm mb-1">Verified documents</h3>
            <p className="text-sage text-xs">
              Every listing's paperwork is checked before it reaches you.
            </p>
          </div>

          <div className="bg-white border border-line rounded-xl p-5 shadow-sm">
            <div className="w-10 h-10 rounded-lg bg-alert/10 flex items-center justify-center mb-3">
              <TrendingUp size={18} className="text-alert" />
            </div>
            <h3 className="font-semibold text-ink text-sm mb-1">Fair price insight</h3>
            <p className="text-sage text-xs">
              See how a price compares to similar homes nearby before you decide.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Landing;