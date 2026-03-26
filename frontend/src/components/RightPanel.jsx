import { Download, ExternalLink, FileClock, FolderSearch2, Trash2, UploadCloud } from "lucide-react";
import { VisualizationPanel } from "./VisualizationPanel";


const SAMPLE_DATASET_URL = "https://drive.google.com/drive/folders/1fYdddOF-W7Y0sSUzf98Y6wlPjJ8mknJe?usp=sharing";

function Section({ title, children, footer }) {
  return (
    <section className="rounded-[24px] border border-white/10 bg-slate-900/85 p-4">
      <p className="text-[11px] uppercase tracking-[0.24em] text-slate-400">{title}</p>
      <div className="mt-4">{children}</div>
      {footer ? <div className="mt-4">{footer}</div> : null}
    </section>
  );
}

function DatasetList({ activeCase, onRemoveDataset }) {
  if (!activeCase?.datasets?.length) {
    return <p className="text-sm text-slate-400">No datasets uploaded for this case yet.</p>;
  }

  return (
    <div className="space-y-3">
      {activeCase.datasets.map((dataset) => (
        <div key={dataset.file_name} className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm text-white">{dataset.file_name}</p>
              <p className="mt-1 text-xs text-slate-400">{dataset.dataset_type_guess} • {dataset.rows} rows • {dataset.columns.length} cols</p>
            </div>
            <button
              onClick={() => onRemoveDataset(dataset.file_name)}
              className="rounded-xl border border-white/10 p-2 text-slate-400 transition hover:bg-white/5 hover:text-rose-200"
              title="Remove dataset"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function QueryHistory({ items, onReplay }) {
  if (!items.length) {
    return <p className="text-sm text-slate-400">Run a few questions and they will appear here.</p>;
  }

  return (
    <div className="space-y-2">
      {items.slice(0, 8).map((item, index) => (
        <button
          key={`${item}-${index}`}
          onClick={() => onReplay(item)}
          className="block w-full rounded-2xl bg-white/5 px-3 py-3 text-left text-sm text-slate-200 hover:bg-white/10"
        >
          {item}
        </button>
      ))}
    </div>
  );
}

export function RightPanel({
  activeCase,
  uploading,
  onUpload,
  onRemoveDataset,
  visualHistory,
  queryHistory,
  onReplayQuery,
  onEntitySelect,
  onGenerateReport,
  reporting
}) {
  return (
    <aside className="flex h-full min-h-0 flex-col gap-4 overflow-hidden">
      <Section
        title="Upload"
        footer={
          <button
            onClick={onGenerateReport}
            disabled={!activeCase || reporting}
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-amber-400 px-4 py-3 text-sm font-medium text-slate-950 transition hover:bg-amber-300 disabled:opacity-50"
          >
            <Download size={16} />
            {reporting ? "Generating Report..." : "Generate Report"}
          </button>
        }
      >
        <div className="space-y-3">
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-100 hover:bg-cyan-400/20">
            <UploadCloud size={16} />
            {uploading ? "Uploading..." : "Upload Datasets"}
            <input
              type="file"
              multiple
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={(event) => onUpload(Array.from(event.target.files || []))}
              disabled={!activeCase || uploading}
            />
          </label>

          <a
            href={SAMPLE_DATASET_URL}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200 transition hover:bg-white/10"
          >
            <span>Download Sample Datasets</span>
            <ExternalLink size={15} className="text-slate-400" />
          </a>
        </div>
      </Section>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
        <Section title="Datasets">
          <DatasetList activeCase={activeCase} onRemoveDataset={onRemoveDataset} />
        </Section>

        {visualHistory?.length ? (
          <Section title="Visualizations">
            <div className="space-y-3">
              {visualHistory.map((entry) => (
                <div key={entry.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                  <p className="mb-3 text-xs uppercase tracking-[0.18em] text-slate-400">{entry.title}</p>
                  <VisualizationPanel
                    intent={entry.intent}
                    structuredResult={entry.structuredResult}
                    onEntitySelect={onEntitySelect}
                  />
                </div>
              ))}
            </div>
          </Section>
        ) : null}

        <Section title="Query History">
          <QueryHistory items={queryHistory} onReplay={onReplayQuery} />
        </Section>
      </div>
    </aside>
  );
}
