import { AlertTriangle, Lightbulb, Radar, Route } from "lucide-react";

export function InsightCards({ responseCard, structuredResult, caseProfile }) {
  const cards = [];

  if (responseCard?.observation) {
    cards.push({
      title: "Observation",
      value: responseCard.observation,
      icon: Radar,
      tone: "cyan"
    });
  }

  if (responseCard?.interpretation) {
    cards.push({
      title: "Interpretation",
      value: responseCard.interpretation,
      icon: Lightbulb,
      tone: "amber"
    });
  }

  if (structuredResult?.alerts?.length) {
    cards.push({
      title: "High Alert",
      value: structuredResult.alerts[0],
      icon: AlertTriangle,
      tone: "rose"
    });
  } else if (caseProfile?.dataset_count > 1) {
    cards.push({
      title: "Cross Dataset",
      value: "Multiple datasets loaded for correlation.",
      icon: Route,
      tone: "emerald"
    });
  }

  if (cards.length === 0) return null;

  return (
    <section className="grid gap-3 md:grid-cols-3">
      {cards.slice(0, 3).map((card) => {
        const Icon = card.icon;
        const toneClass =
          card.tone === "amber"
            ? "bg-amber-400/10 text-amber-200"
            : card.tone === "rose"
              ? "bg-rose-400/10 text-rose-200"
              : card.tone === "emerald"
                ? "bg-emerald-400/10 text-emerald-200"
                : "bg-cyan-400/10 text-cyan-200";

        return (
          <div key={card.title} className="rounded-[24px] border border-white/10 bg-slate-900/80 p-4">
            <div className={`inline-flex rounded-2xl p-2 ${toneClass}`}>
              <Icon size={18} />
            </div>
            <p className="mt-4 text-xs uppercase tracking-[0.24em] text-slate-400">{card.title}</p>
            <p className="mt-2 text-sm leading-6 text-white">{card.value}</p>
          </div>
        );
      })}
    </section>
  );
}
