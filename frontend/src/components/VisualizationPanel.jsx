function SectionTitle({ label, title }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <h3 className="mt-1 font-display text-base text-white">{title}</h3>
    </div>
  );
}

function EmptyBlock({ text }) {
  return <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-400">{text}</div>;
}

function FrequencyChart({ items = [], onEntitySelect }) {
  if (!items.length) return null;
  const maxValue = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className="rounded-[22px] border border-white/10 bg-slate-950/70 p-4">
      <SectionTitle label="Visualization" title="Top Entities" />
      <div className="mt-4 space-y-3">
        {items.slice(0, 6).map((item) => (
          <button key={item.label} onClick={() => onEntitySelect?.(item.label)} className="block w-full text-left">
            <div className="mb-1 flex items-center justify-between gap-3 text-xs text-slate-300">
              <span className="truncate hover:text-cyan-200">{item.label}</span>
              <span>{item.value}</span>
            </div>
            <div className="h-2 rounded-full bg-white/5">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-cyan-400 to-emerald-300 transition-all"
                style={{ width: `${(item.value / maxValue) * 100}%` }}
              />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function CrossDatasetTable({ items = [], onEntitySelect }) {
  if (!items.length) return null;
  return (
    <div className="rounded-[22px] border border-white/10 bg-slate-950/70 p-4">
      <SectionTitle label="Cross Dataset" title="Common Entities" />
      <div className="mt-4 overflow-hidden rounded-2xl border border-white/10">
        {items.slice(0, 6).map((item) => (
          <button
            key={item.value}
            onClick={() => onEntitySelect?.(item.value)}
            className="flex w-full items-start justify-between gap-3 border-b border-white/10 bg-white/5 px-3 py-3 text-left last:border-b-0 hover:bg-white/10"
          >
            <div>
              <p className="text-sm text-white">{item.value}</p>
              <p className="mt-1 text-xs text-slate-400">{item.files.join(", ")}</p>
            </div>
            <span className="rounded-full bg-cyan-400/10 px-2 py-1 text-xs text-cyan-200">{item.file_count} files</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function RelationshipTable({ items = [], onEntitySelect }) {
  if (!items.length) return null;
  const first = items.find((item) => item.pairs?.length);
  if (!first) return null;
  return (
    <div className="rounded-[22px] border border-white/10 bg-slate-950/70 p-4">
      <SectionTitle label="Relationships" title="Connection Table" />
      <div className="mt-4 space-y-2">
        {first.pairs.slice(0, 6).map((pair, index) => (
          <div key={`${pair.source}-${pair.target}-${index}`} className="rounded-2xl bg-white/5 px-3 py-3 text-sm text-slate-200">
            <button className="hover:text-cyan-200" onClick={() => onEntitySelect?.(pair.source)}>{pair.source}</button>
            <span className="mx-2 text-cyan-300">↔</span>
            <button className="hover:text-cyan-200" onClick={() => onEntitySelect?.(pair.target)}>{pair.target}</button>
            <span className="ml-2 text-xs text-slate-400">({pair.count})</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SuspiciousList({ structuredResult, onEntitySelect }) {
  const items = structuredResult?.frequency_snapshot || structuredResult?.top_entities || [];
  const alerts = structuredResult?.alerts || [];
  if (!items.length && !alerts.length) return null;
  return (
    <div className="rounded-[22px] border border-white/10 bg-slate-950/70 p-4">
      <SectionTitle label="Suspicious View" title="Top Suspicious Entities" />
      <div className="mt-4 space-y-2">
        {items.slice(0, 5).map((item) => (
          <button
            key={item.value}
            onClick={() => onEntitySelect?.(item.value)}
            className="flex w-full items-center justify-between rounded-2xl bg-rose-400/10 px-3 py-3 text-left text-sm text-rose-100"
          >
            <span>{item.value}</span>
            <span>{item.count}</span>
          </button>
        ))}
        {alerts.slice(0, 3).map((alert) => (
          <p key={alert} className="rounded-2xl bg-white/5 px-3 py-3 text-sm text-slate-300">{alert}</p>
        ))}
      </div>
    </div>
  );
}

export function VisualizationPanel({ intent, structuredResult, onEntitySelect }) {
  if (!structuredResult) {
    return <EmptyBlock text="Run a query to populate charts, tables, and investigation visuals." />;
  }

  const visuals = structuredResult?.visualizations || {};
  const blocks = [];

  if (intent === "frequency" || visuals.frequency_chart?.length) {
    blocks.push(<FrequencyChart key="frequency" items={visuals.frequency_chart || []} onEntitySelect={onEntitySelect} />);
  }
  if (intent === "cross_dataset" || structuredResult?.common_entities?.length) {
    blocks.push(
      <CrossDatasetTable key="cross" items={structuredResult?.common_entities || structuredResult?.cross_dataset_snapshot || []} onEntitySelect={onEntitySelect} />
    );
  }
  if (intent === "relationship" || structuredResult?.relationships?.length || structuredResult?.relationship_snapshot?.length) {
    blocks.push(
      <RelationshipTable
        key="relationships"
        items={structuredResult?.relationships || structuredResult?.relationship_snapshot || []}
        onEntitySelect={onEntitySelect}
      />
    );
  }
  if (intent === "anomaly" || structuredResult?.alerts?.length) {
    blocks.push(<SuspiciousList key="suspicious" structuredResult={structuredResult} onEntitySelect={onEntitySelect} />);
  }

  if (!blocks.length) {
    return <EmptyBlock text="No relevant visualization is available for the latest analysis." />;
  }

  return <div className="space-y-3">{blocks}</div>;
}
