# Frontend

React + Vite + Tailwind frontend for the forensic investigation workspace.

## Current UI Model

The UI is a fixed-screen 3-panel app:

- left sidebar: cases and observation box
- center panel: chat-first investigation flow
- right sidebar: uploads, visualizations, query history, report action

The page itself does not scroll. Internal panel sections scroll independently.

## Main Features

- create and switch isolated cases
- upload multiple datasets per case
- chat with the backend analysis engine
- fixed chat input at the bottom
- smart suggestion chips in a single horizontal scrolling line
- replay prior queries
- show only the last two relevant visualizations
- remove uploaded datasets
- generate DOCX reports

## Main Files

- [src/App.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/App.jsx)
- [src/components/CaseSidebar.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/components/CaseSidebar.jsx)
- [src/components/ChatPanel.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/components/ChatPanel.jsx)
- [src/components/RightPanel.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/components/RightPanel.jsx)
- [src/components/VisualizationPanel.jsx](/Users/hemasai/Documents/AIFOrnsic/frontend/src/components/VisualizationPanel.jsx)
- [src/lib/api.js](/Users/hemasai/Documents/AIFOrnsic/frontend/src/lib/api.js)

## Run

```bash
cd /Users/hemasai/Documents/AIFOrnsic/frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

## Notes

- the UI expects the backend to be running at `http://localhost:8000` unless overridden
- response cards, suggestions, and visualization blocks are driven by backend query output
- the frontend is intentionally lightweight and demo-focused
