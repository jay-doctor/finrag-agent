# 📊 Financial Report Extractor

An AI-powered agent that extracts key financial metrics from corporate annual and quarterly reports (PDFs) using RAG (Retrieval-Augmented Generation) with LangChain, ChromaDB, and GPT-4o.

**Live Demo:** [https://finrag-agent.streamlit.app](https://finrag-agent.streamlit.app)

---

## 🚀 Features

- **PDF Processing:** Automatically loads and chunks PDF reports (supports both text-based and scanned PDFs with OCR fallback)
- **Multi-Language Support:** Handles English and German reports (BMW, Mercedes, Volkswagen)
- **RAG Pipeline:** Retrieves relevant chunks using vector search, then extracts structured data with LLM
- **Metadata Filtering:** Ensures company-specific retrieval – no cross-company contamination
- **Flexible LLM Backend:** Uses OpenAI by default, with automatic fallback to Groq (free)
- **Interactive UI:** Streamlit web interface with file upload, sample data, and downloadable results
- **Persistent Storage:** Caches embeddings and LLM responses for faster re-runs

---

## 📊 Extracted Metrics

| Metric | Description |
|--------|-------------|
| Revenue | Total revenue (million EUR) |
| EBIT | Operating result (million EUR) |
| Operating Margin | EBIT / Revenue (%) |
| Cash Metric | Free Cash Flow, Net Cash Flow |
| Net Liquidity | Net debt / cash position |
| Return on Capital | ROCE, ROIC, or RoI (%) |
| Cost of Capital | WACC or hurdle rate (if disclosed) |
| EPS | Earnings per share (EUR) |
| Dividend per Share | Dividend per share (EUR) |
| Market Cap at €100/share | Market capitalization if share price = €100 |

---

## 🏗️ Architecture
┌─────────────────────────────────────────────────────────────────┐
│ Streamlit UI │
│ (Upload PDFs → Configure settings → View/Download results) │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ PDF Loader & Chunker │
│ • Extracts text (pdfplumber + OCR fallback) │
│ • Splits into chunks (3000 chars, 300 overlap) │
│ • Assigns metadata (company, report_type) │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ Vector Store (ChromaDB) │
│ • Embeds chunks with OpenAI embeddings │
│ • Stores vectors + metadata for retrieval │
│ • Supports metadata filtering (company + report_type) │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ Retriever │
│ • Multi-query retrieval (5 queries per report) │
│ • Metadata filter: ensures only correct company + report type │
│ • Returns top-k relevant chunks (k=20) │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ LLM (OpenAI / Groq) │
│ • Extracts metrics from retrieved chunks │
│ • Returns structured JSON │
│ • Handles German & English terms │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ Output Table (Markdown) │
│ • Formatted table with all metrics │
│ • Substitution notes for replaced metric names │
│ • Downloadable as markdown │
└─────────────────────────────────────────────────────────────────┘


---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| PDF Processing | `pdfplumber` + `pytesseract` (OCR) |
| Chunking | `RecursiveCharacterTextSplitter` |
| Embeddings | `OpenAIEmbeddings` (fallback: HuggingFace) |
| Vector Store | `ChromaDB` (persistent) |
| Retrieval | Multi-query with metadata filtering |
| LLM | `OpenAI GPT-4o-mini` (fallback: Groq Llama 3.3 70B) |
| UI | `Streamlit` |
| Language | `Python 3.10+` |
| Cache | `pickle` (LLM responses) |

---

## 📁 Project Structure
finrag-agent/
├── data/
│ └── reports/ ← PDF reports (auto-loaded)
├── output/ ← Generated tables & substitutions
├── src/
│ ├── init.py
│ ├── extractor.py ← LLM extraction logic
│ ├── pdf_loader.py ← PDF loading & chunking
│ ├── prompt_templates.py ← Extraction prompt
│ ├── utils.py ← Caching & helpers
│ └── vector_store.py ← ChromaDB & embeddings
├── tests/
│ └── test_extractor.py
├── .env.example ← Environment variables template
├── .gitignore
├── main.py ← CLI entry point
├── ui.py ← Streamlit UI entry point
├── README.md
└── requirements.txt


---

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/finrag-agent.git
cd finrag-agent

2. Create virtual environment
bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

3. Install dependencies
bash
pip install -r requirements.txt

4. Set up environment variables
bash
cp .env.example .env
Add your API keys to .env:

text
OPENAI_API_KEY=sk-proj-xxxxx
GROQ_API_KEY_1=gsk_xxxxx
GROQ_API_KEY_2=gsk_xxxxx

5. Install Tesseract (for OCR)
Windows: Download from GitHub UB-Mannheim/tesseract

Mac:

bash
brew install tesseract tesseract-lang
Ubuntu/Debian:
bash
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu

🚀 Usage
CLI Mode
bash
python main.py
Extracts all companies and report types
Saves table to output/table_<timestamp>.md
Saves substitutions to output/substitutions_<timestamp>.txt
Caches embeddings in chroma_db/ and LLM responses in extraction_cache.pkl

Streamlit UI (Recommended for Demos)
bash
streamlit run ui.py
Open http://localhost:8501
Upload PDFs or use sample files from data/reports/
Configure companies, report types, and k value
Click "Extract Metrics" – view and download results

Configuration Options
Setting	Location	Description
QUARTERLY_ONLY	main.py	Set True to extract only quarterly reports
COMPANIES	main.py / ui.py	List of companies to process
REPORT_TYPES	main.py / ui.py	["Full Year 2025", "Quarterly 2025"]
k (retrieval)	vector_store.py	Number of chunks to retrieve (default: 20)
chunk_size	pdf_loader.py	Chunk size in characters (default: 3000)
Model	extractor.py	gpt-4o-mini or gpt-4o

