import os
import sys
import json
import tempfile
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_loader import load_pdfs
from src.vector_store import create_vectorstore, get_retriever
from src.extractor import get_llm, extract_for_company_retriever
from src.utils import load_cache, save_cache

st.set_page_config(
    page_title="Financial Report Extractor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Financial Report Extractor")
st.markdown("Upload financial reports (PDFs) to extract key metrics like Revenue, EBIT, and more.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    companies = st.multiselect(
        "Companies to extract",
        ["BMW", "Mercedes", "Volkswagen"],
        default=["BMW", "Mercedes", "Volkswagen"]
    )
    report_types = st.multiselect(
        "Report types",
        ["Full Year 2025", "Quarterly 2025"],
        default=["Full Year 2025", "Quarterly 2025"]
    )
    k_value = st.slider("Number of chunks to retrieve (k)", 5, 30, 20)
    use_openai = st.checkbox("Use OpenAI (requires API key)", value=True)
    run_button = st.button("🚀 Extract Metrics", type="primary", use_container_width=True)

# ---- MAIN AREA ----
uploaded_files = st.file_uploader(
    "Upload PDF files (optional – skip to use sample files)",
    type=["pdf"],
    accept_multiple_files=True,
    help="Upload your own PDFs, or use the sample files already loaded from data/reports/"
)

# ---- AUTO-LOAD SAMPLE FILES FROM data/reports/ ----
sample_files_loaded = False
sample_file_names = []

if os.path.exists("data/reports"):
    sample_files = [f for f in os.listdir("data/reports") if f.endswith(".pdf")]
    if sample_files:
        sample_files_loaded = True
        sample_file_names = sample_files
        st.info(f"📂 Found {len(sample_files)} sample files in data/reports/")
        for f in sample_files:
            st.write(f"   ✅ {f}")

# ---- DETERMINE WHICH FILES TO USE ----
# If user uploaded files, use those. Otherwise, use sample files.
if uploaded_files:
    use_uploaded = True
    st.success(f"✅ {len(uploaded_files)} files uploaded (using these instead of sample files)")
elif sample_files_loaded:
    use_uploaded = False
    st.success(f"✅ Using {len(sample_files)} sample files from data/reports/ – click Extract Metrics")
else:
    use_uploaded = False
    st.warning("⚠️ No PDFs found. Please upload files or place them in data/reports/")

# ---- EXTRACTION LOGIC ----
if run_button:
    if not uploaded_files and not sample_files_loaded:
        st.error("❌ No PDFs available. Please upload files or add them to data/reports/")
    else:
        with st.spinner("Processing PDFs and extracting metrics..."):
            try:
                # Get files to process
                if uploaded_files:
                    # Use uploaded files
                    with tempfile.TemporaryDirectory() as tmpdir:
                        for file in uploaded_files:
                            file_path = os.path.join(tmpdir, file.name)
                            with open(file_path, "wb") as f:
                                f.write(file.getbuffer())
                        docs = load_pdfs(tmpdir)
                else:
                    # Use sample files from data/reports/
                    docs = load_pdfs("data/reports")
                
                st.info(f"📄 Loaded {len(docs)} chunks")
                
                # ---- Embeddings ----
                if use_openai:
                    vectorstore = create_vectorstore(docs)
                else:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    from langchain_community.vectorstores import Chroma
                    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                    vectorstore = Chroma.from_documents(docs, embeddings, persist_directory="./chroma_db")
                
                retriever = get_retriever(vectorstore, k=k_value)
                llm = get_llm()
                cache = load_cache()
                
                # ---- Extract ----
                results = {}
                progress_bar = st.progress(0)
                total_runs = len(companies) * len(report_types)
                run_count = 0
                
                for company in companies:
                    results[company] = {}
                    for rtype in report_types:
                        key = f"{company}_{rtype}"
                        results[company][rtype] = extract_for_company_retriever(
                            company, rtype, retriever, llm, cache, key
                        )
                        save_cache(cache)
                        run_count += 1
                        progress_bar.progress(run_count / total_runs)
                
                # ---- Table ----
                metrics = ["Revenue", "EBIT", "Operating_margin", "Cash_metric", 
                           "Net_liquidity", "Return_on_capital", "Cost_of_capital", 
                           "EPS", "Dividend_per_share", "Market_cap_at_100EUR"]
                
                columns = []
                for company in companies:
                    for rtype in report_types:
                        suffix = "FY" if "Full Year" in rtype else "Q"
                        columns.append(f"{company} {suffix}")
                
                table_data = {col: [] for col in columns}
                
                for metric in metrics:
                    col_idx = 0
                    for company in companies:
                        for rtype in report_types:
                            data = results[company].get(rtype, {})
                            val = data.get(metric, "Not Reported")
                            
                            if metric == "Operating_margin":
                                rev = data.get("Revenue", "Not Reported")
                                ebit = data.get("EBIT", "Not Reported")
                                if rev != "Not Reported" and ebit != "Not Reported":
                                    try:
                                        rev_num = float(str(rev).replace(",", "").split()[0])
                                        ebit_num = float(str(ebit).replace(",", "").split()[0])
                                        val = f"{(ebit_num/rev_num)*100:.1f}%"
                                    except:
                                        val = "Not Reported"
                                else:
                                    val = "Not Reported"
                            
                            table_data[columns[col_idx]].append(val)
                            col_idx += 1
                
                df = pd.DataFrame(table_data, index=metrics)
                
                st.subheader("📊 Extracted Metrics")
                st.dataframe(df, use_container_width=True)
                
                st.download_button(
                    "📥 Download as Markdown",
                    df.to_markdown(),
                    file_name=f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
                
                subs = []
                for company in companies:
                    for rtype in report_types:
                        s = results[company].get(rtype, {}).get("substitutions", "")
                        if s and s != "None":
                            subs.append(f"{company} {rtype}: {s}")
                
                if subs:
                    st.subheader("📝 Substitution Notes")
                    for s in subs:
                        st.write(f"- {s}")
                
                st.success("✅ Extraction complete!")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.exception(e)

st.divider()
st.caption("Built with LangChain, Chroma, and Streamlit | Powered by OpenAI")