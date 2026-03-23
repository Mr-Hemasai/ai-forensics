import { useEffect, useMemo, useState } from "react";
import { AlertCircle } from "lucide-react";
import { CaseSidebar } from "./components/CaseSidebar";
import { ChatPanel } from "./components/ChatPanel";
import { RightPanel } from "./components/RightPanel";
import {
  createCase,
  downloadReport,
  fetchCaseDetail,
  fetchCases,
  fetchTimeline,
  removeDataset,
  sendQuery,
  uploadFiles
} from "./lib/api";

function buildVisualizationEntry(response, timelineEvents) {
  const structured = response.structured_result || {};
  const hasVisuals =
    structured.visualizations?.frequency_chart?.length ||
    structured.relationships?.length ||
    structured.relationship_snapshot?.length ||
    structured.common_entities?.length ||
    structured.cross_dataset_snapshot?.length ||
    structured.alerts?.length;

  if (!hasVisuals) return null;

  return {
    id: `${response.intent}-${Date.now()}`,
    title: response.response_card?.title || response.intent,
    intent: response.intent,
    structuredResult: structured
  };
}

function App() {
  const [cases, setCases] = useState([]);
  const [activeCaseId, setActiveCaseId] = useState("");
  const [newCaseName, setNewCaseName] = useState("");
  const [showNewCaseForm, setShowNewCaseForm] = useState(false);
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [lastStructuredResult, setLastStructuredResult] = useState(null);
  const [lastResponseCard, setLastResponseCard] = useState(null);
  const [lastIntent, setLastIntent] = useState("overview");
  const [suggestions, setSuggestions] = useState([]);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [reporting, setReporting] = useState(false);
  const [error, setError] = useState("");
  const [caseDetails, setCaseDetails] = useState({});
  const [observationsByCase, setObservationsByCase] = useState({});
  const [visualHistoryByCase, setVisualHistoryByCase] = useState({});

  const activeCase = useMemo(
    () => caseDetails[activeCaseId] || cases.find((item) => item.case_id === activeCaseId) || null,
    [caseDetails, cases, activeCaseId]
  );

  const activeObservationItems = observationsByCase[activeCaseId] || [];
  const activeVisualHistory = visualHistoryByCase[activeCaseId] || [];

  async function loadCaseDetail(caseId) {
    if (!caseId) return;
    const detail = await fetchCaseDetail(caseId);
    setCaseDetails((current) => ({ ...current, [caseId]: detail }));
    setChatHistory(detail.chat_history || []);
    setSuggestions(detail.case_profile?.suggestions || []);
    setObservationsByCase((current) => ({ ...current, [caseId]: detail.observation_items || [] }));
    const timeline = await fetchTimeline(caseId);
    setTimelineEvents(timeline.events || []);
    setLastStructuredResult(null);
    setLastResponseCard(null);
    setLastIntent("overview");
  }

  async function refreshCases(preferredCaseId) {
    try {
      const data = await fetchCases();
      setCases(data);
      if (data.length === 0) {
        setActiveCaseId("");
        setChatHistory([]);
        setLastStructuredResult(null);
        setLastResponseCard(null);
        setLastIntent("overview");
        setSuggestions([]);
        setTimelineEvents([]);
        setCaseDetails({});
        return;
      }

      const nextCaseId =
        preferredCaseId && data.some((item) => item.case_id === preferredCaseId)
          ? preferredCaseId
          : activeCaseId && data.some((item) => item.case_id === activeCaseId)
            ? activeCaseId
            : data[0].case_id;

      setActiveCaseId(nextCaseId);
      await loadCaseDetail(nextCaseId);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refreshCases();
  }, []);

  async function handleCreateCase() {
    if (!newCaseName.trim()) return;
    try {
      setError("");
      const response = await createCase(newCaseName.trim());
      setNewCaseName("");
      setShowNewCaseForm(false);
      setObservationsByCase((current) => ({ ...current, [response.case_id]: [] }));
      setVisualHistoryByCase((current) => ({ ...current, [response.case_id]: [] }));
      await refreshCases(response.case_id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpload(files) {
    if (!activeCaseId || files.length === 0) return;
    try {
      setUploading(true);
      setError("");
      await uploadFiles(activeCaseId, files);
      await refreshCases(activeCaseId);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleRemoveDataset(fileName) {
    if (!activeCaseId) return;
    try {
      setError("");
      await removeDataset(activeCaseId, fileName);
      await refreshCases(activeCaseId);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleGenerateReport() {
    if (!activeCaseId) return;
    try {
      setReporting(true);
      setError("");
      const blob = await downloadReport(activeCaseId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${activeCase?.case_name || "case"}_report.docx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setReporting(false);
    }
  }

  async function handleSend(input) {
    const message = input.trim();
    if (!message || !activeCaseId) return;

    const nextHistory = [...chatHistory, { role: "user", content: message }];
    setChatHistory(nextHistory);
    setQuery("");
    setLoading(true);
    setError("");

    try {
      const response = await sendQuery(activeCaseId, message);
      setChatHistory(response.chat_history);
      setLastStructuredResult(response.structured_result);
      setLastResponseCard(response.response_card);
      setLastIntent(response.intent);
      setSuggestions(response.suggestions || response.case_profile?.suggestions || []);
      const timeline = await fetchTimeline(activeCaseId);
      const detailTimeline = timeline.events || [];
      setTimelineEvents(detailTimeline);
      setObservationsByCase((current) => ({
        ...current,
        [activeCaseId]: response.observation_items || current[activeCaseId] || []
      }));

      const visualEntry = buildVisualizationEntry(response, detailTimeline);
      if (visualEntry) {
        setVisualHistoryByCase((current) => ({
          ...current,
          [activeCaseId]: [...(current[activeCaseId] || []), visualEntry].slice(-2)
        }));
      }

      setCaseDetails((current) => ({
        ...current,
        [activeCaseId]: {
          ...(current[activeCaseId] || {}),
          chat_history: response.chat_history,
          case_profile: response.case_profile
        }
      }));
    } catch (err) {
      setChatHistory((current) => current.filter((item, index) => !(index === current.length - 1 && item.content === message)));
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const queryHistory = [...new Set(chatHistory.filter((item) => item.role === "user").map((item) => item.content))].reverse();
  const placeholder = suggestions[0]
    ? `Try: ${suggestions[0]}`
    : "Ask about top entities, night activity, common entities, or connections.";

  return (
    <div className="h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.15),_transparent_22%),radial-gradient(circle_at_top_right,_rgba(245,158,11,0.12),_transparent_30%),linear-gradient(160deg,_#020617,_#0f172a_55%,_#111827)] px-3 py-4 font-body text-white md:px-4 lg:px-5">
      <div className="mx-auto grid h-full max-w-[1800px] gap-4 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)_370px] xl:grid-cols-[320px_minmax(0,1fr)_400px]">
        <CaseSidebar
          activeCase={activeCase}
          cases={cases}
          activeCaseId={activeCaseId}
          showNewCaseForm={showNewCaseForm}
          onToggleNewCase={() => setShowNewCaseForm((current) => !current)}
          newCaseName={newCaseName}
          onNewCaseNameChange={setNewCaseName}
          onCreateCase={handleCreateCase}
          observationItems={activeObservationItems}
          onSelectCase={async (caseId) => {
            setActiveCaseId(caseId);
            try {
              setError("");
              await loadCaseDetail(caseId);
            } catch (err) {
              setError(err.message);
            }
          }}
        />

        <main className="flex min-h-0 flex-col gap-4 lg:overflow-hidden">
          {error ? (
            <div className="flex items-center gap-3 rounded-2xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">
              <AlertCircle size={18} />
              {error}
            </div>
          ) : null}

          <div className="min-h-0 flex-1 lg:overflow-hidden">
            <ChatPanel
              activeCase={activeCase}
              chatHistory={chatHistory}
              query={query}
              onQueryChange={setQuery}
              onSend={handleSend}
              loading={loading}
              suggestions={suggestions}
              onSuggestionClick={(suggestion) => handleSend(suggestion)}
              placeholder={placeholder}
            />
          </div>
        </main>

        <RightPanel
          activeCase={activeCase}
          uploading={uploading}
          onUpload={handleUpload}
          onRemoveDataset={handleRemoveDataset}
          visualHistory={activeVisualHistory}
          queryHistory={queryHistory}
          onReplayQuery={handleSend}
          onEntitySelect={() => {}}
          onGenerateReport={handleGenerateReport}
          reporting={reporting}
        />
      </div>
    </div>
  );
}

export default App;
