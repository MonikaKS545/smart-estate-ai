import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";

/**
 * Color-coded trust/fraud score badge.
 * Bands per spec: 80-100 green, 60-79 yellow, 0-59 red.
 *
 * Props:
 *  - score: number 0-100 (trust_score from the fraud shape)
 *  - riskLevel: optional "low"|"medium"|"high" — if provided, used for
 *    the label text; otherwise derived from score.
 */
export default function TrustScoreBadge({ score, riskLevel }) {
  let band;
  if (score >= 80) band = "green";
  else if (score >= 60) band = "yellow";
  else band = "red";

  const styles = {
    green: {
      bg: "bg-green-100",
      text: "text-green-800",
      Icon: ShieldCheck,
      label: "Low Risk",
    },
    yellow: {
      bg: "bg-yellow-100",
      text: "text-yellow-800",
      Icon: ShieldAlert,
      label: "Medium Risk",
    },
    red: {
      bg: "bg-red-100",
      text: "text-red-800",
      Icon: ShieldX,
      label: "High Risk",
    },
  };

  const { bg, text, Icon, label } = styles[band];
  const displayLabel = riskLevel
    ? riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1) + " Risk"
    : label;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${bg} ${text}`}
    >
      <Icon size={14} />
      Trust Score: {score} · {displayLabel}
    </span>
  );
}