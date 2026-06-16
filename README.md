# 📊 Financial Report Extractor

An AI-powered agent that extracts key financial metrics from corporate annual and quarterly reports (PDFs) using RAG (Retrieval-Augmented Generation) with LangChain, ChromaDB, and GPT-4o.

🔗 **Live Demo:** [finrag-agent.streamlit.app](https://finrag-agent.streamlit.app)

---

## Table of Contents

- [Features](#-features)
- [Extracted Metrics](#-extracted-metrics)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)

---

## ✨ Features

- **PDF Processing** — Automatically loads and chunks PDF reports, with OCR fallback for scanned documents
- **Multi-Language Support** — Handles English and German reports (BMW, Mercedes, Volkswagen)
- **RAG Pipeline** — Retrieves relevant chunks via vector search, then extracts structured data with an LLM
- **Metadata Filtering** — Ensures company-specific retrieval with no cross-company contamination
- **Flexible LLM Backend** — Uses OpenAI by default, with automatic fallback to Groq (free tier)
- **Interactive UI** — Streamlit web interface with file upload, sample data, and downloadable results
- **Persistent Storage** — Caches embeddings and LLM responses for faster re-runs

---

## 📈 Extracted Metrics

| Metric | Description |
|---|---|
| Revenue | Total revenue (million EUR) |
| EBIT | Operating result (million EUR) |
| Operating Margin | EBIT / Revenue (%) |
| Cash Metric | Free Cash Flow or Net Cash Flow |
| Net Liquidity | Net debt / cash position |
| Return on Capital | ROCE, ROIC, or RoI (%) |
| Cost of Capital | WACC or hurdle rate (if disclosed) |
| EPS | Earnings per share (EUR) |
| Dividend per Share | Dividend per share (EUR) |
| Market Cap at €100/share | Market capitalization at a €100 share price |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                       Streamlit UI                       │
│        Upload PDFs → Configure → View / Download         │
└──────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                  PDF Loader & Chunker                    │
│  • Extracts text via pdfplumber (+ OCR fallback)         │
│  • Splits into chunks (3 000 chars, 300 overlap)         │
│  • Assigns metadata (company, report_type)               │
└──────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                 Vector Store (ChromaDB)                  │
│  • Embeds chunks with OpenAI Embeddings                  │
│  • Stores vectors + metadata for retrieval               │
│  • Supports metadata filtering (company + report_type)   │
└──────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                        Retriever                         │
│  • Multi-query retrieval (5 queries per report)          │
│  • Metadata filter: correct company + report type only   │
│  • Returns top-k relevant chunks (default k = 20)        │
└──────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                    LLM (OpenAI / Groq)                   │
│  • Extracts metrics from retrieved chunks                │
│  • Returns structured JSON                               │
│  • Handles German & English financial terms              │
└──────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   Output Table (Markdown)                │
│  • Formatted table with all metrics                      │
│  • Substitution notes for replaced metric names          │
│  • Downloadable as Markdown                              │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| PDF Processing | `pdfplumber` + `pytesseract` (OCR) |
| Chunking | `RecursiveCharacterTextSplitter` |
| Embeddings | `OpenAIEmbeddings` (fallback: HuggingFace) |
| Vector Store | `ChromaDB` (persistent) |
| Retrieval | Multi-query with metadata filtering |
| LLM | `GPT-4o-mini` (fallback: Groq Llama 3.3 70B) |
| UI | `Streamlit` |
| Language | Python 3.10+ |
| Cache | `pickle` (LLM responses) |

---

## 📁 Project Structure

```
finrag-agent/
├── data/
│   └── reports/              # PDF reports (auto-loaded)
├── output/                   # Generated tables & substitution logs
├── src/
│   ├── __init__.py
│   ├── extractor.py          # LLM extraction logic
│   ├── pdf_loader.py         # PDF loading & chunking
│   ├── prompt_templates.py   # Extraction prompt definitions
│   ├── utils.py              # Caching & helper utilities
│   └── vector_store.py       # ChromaDB & embeddings
├── tests/
│   └── test_extractor.py
├── .env.example              # Environment variable template
├── .gitignore
├── main.py                   # CLI entry point
├── ui.py                     # Streamlit UI entry point
├── README.md
└── requirements.txt
```

---

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/finrag-agent.git
cd finrag-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-proj-xxxxx
GROQ_API_KEY_1=gsk_xxxxx
GROQ_API_KEY_2=gsk_xxxxx
```

### 5. Install Tesseract (for OCR)

**Windows** — Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

**macOS**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu / Debian**
```bash
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu
```

---

## 🚀 Usage

### CLI Mode

```bash
python main.py
```

This will:
- Extract metrics for all configured companies and report types
- Save the results table to `output/table_<timestamp>.md`
- Save substitution notes to `output/substitutions_<timestamp>.txt`
- Cache embeddings in `chroma_db/` and LLM responses in `extraction_cache.pkl`

### Streamlit UI (Recommended)

```bash
streamlit run ui.py
```

1. Open [http://localhost:8501](http://localhost:8501) in your browser
2. Upload PDFs or use sample files from `data/reports/`
3. Configure companies, report types, and retrieval settings
4. Click **Extract Metrics** to view and download results

---

## ⚙️ Configuration

| Setting | File | Description |
|---|---|---|
| `QUARTERLY_ONLY` | `main.py` | Set `True` to extract quarterly reports only |
| `COMPANIES` | `main.py` / `ui.py` | List of companies to process |
| `REPORT_TYPES` | `main.py` / `ui.py` | e.g. `["Full Year 2025", "Quarterly 2025"]` |
| `k` | `vector_store.py` | Number of chunks to retrieve (default: `20`) |
| `chunk_size` | `pdf_loader.py` | Chunk size in characters (default: `3000`) |
| `model` | `extractor.py` | `gpt-4o-mini` or `gpt-4o` |