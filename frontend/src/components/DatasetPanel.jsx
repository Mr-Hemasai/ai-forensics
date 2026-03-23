import { DatabaseZap, FileSpreadsheet, MapPinned, UploadCloud } from "lucide-react";

function SemanticBadge({ label, tone = "cyan" }) {
  const toneClass =
    tone === "amber"
      ? "bg-amber-400/10 text-amber-200"
      : tone === "emerald"
        ? "bg-emerald-400/10 text-emerald-200"
        : "bg-cyan-400/10 text-cyan-200";

  return <span className={`rounded-full px-2 py-1 text-xs ${toneClass}`}>{label}</span>;
}

export function DatasetPanel({ activeCase, onUpload, uploading }) {
  return (
    <section className="rounded-[28px] border border-white/10 bg-slate-900/80 p-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Datasets</p>
          <h2 className="mt-1 font-display text-xl text-white">{activeCase?.case_name || "Select a case"}</h2>
          {activeCase?.case_profile?.semantic_inventory ? (
            <p className="mt-2 text-sm text-slate-400">
              Detected semantics: {Object.keys(activeCase.case_profile.semantic_inventory).slice(0, 6).join(", ")}
            </p>
          ) : null}
        </div>
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-amber-400/40 bg-amber-400/10 px-4 py-3 text-sm text-amber-200 transition hover:bg-amber-400/20">
          <UploadCloud size={16} />
          {uploading ? "Uploading..." : "Upload CSV / Excel"}
          <input
            type="file"
            multiple
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(event) => onUpload(Array.from(event.target.files || []))}
            disabled={!activeCase || uploading}
          />
        </label>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {activeCase?.datasets?.length ? (
          activeCase.datasets.map((dataset) => (
            <div key={dataset.file_name} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-start gap-3">
                <div className="rounded-xl bg-cyan-400/10 p-2 text-cyan-300">
                  <FileSpreadsheet size={18} />
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-white">{dataset.file_name}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    {dataset.rows} rows • {dataset.columns.length} columns
                  </p>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {dataset.column_profiles.slice(0, 4).map((profile) => (
                  <SemanticBadge
                    key={`${dataset.file_name}-${profile.column}`}
                    label={`${profile.column}: ${profile.semantic_type}`}
                    tone={profile.category === "location" ? "amber" : profile.category === "entity" ? "emerald" : "cyan"}
                  />
                ))}
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl bg-slate-950/80 p-3">
                  <div className="flex items-center gap-2 text-cyan-200">
                    <DatabaseZap size={14} />
                    <p className="text-xs uppercase tracking-[0.18em]">Semantic Map</p>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">
                    Entity: {dataset.entity_columns.length} • Time: {dataset.time_columns.length} • Location: {dataset.location_columns.length}
                  </p>
                </div>
                <div className="rounded-2xl bg-slate-950/80 p-3">
                  <div className="flex items-center gap-2 text-amber-200">
                    <MapPinned size={14} />
                    <p className="text-xs uppercase tracking-[0.18em]">Preview</p>
                  </div>
                  <p className="mt-2 line-clamp-3 text-xs text-slate-400">
                    {dataset.preview_rows?.length
                      ? Object.entries(dataset.preview_rows[0])
                          .slice(0, 3)
                          .map(([key, value]) => `${key}: ${value}`)
                          .join(" | ")
                      : "No preview available"}
                  </p>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-400">
            Upload CDR, Tower Dump, IPDR, or any structured telecom/digital dataset for this case.
          </div>
        )}
      </div>
    </section>
  );
}
