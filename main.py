import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pdf_loader import load_pdfs
from src.vector_store import create_vectorstore, get_retriever
from src.extractor import get_llm, extract_for_company_retriever
from src.utils import load_cache, save_cache
import pandas as pd

PDF_FOLDER = "data/reports"

# 🔥 CONFIGURATION – change these to test different scenarios
QUARTERLY_ONLY = True          # True = only quarterly, False = all reports
COMPANIES = ["BMW", "Mercedes", "Volkswagen"]  # or ["Mercedes"] to test one

if QUARTERLY_ONLY:
    REPORT_TYPES = ["Quarterly 2025"]
else:
    REPORT_TYPES = ["Full Year 2025", "Quarterly 2025"]

def save_chunks(chunks, filename="chunks.json"):
    data = []
    for i, chunk in enumerate(chunks):
        data.append({
            "id": i,
            "text": chunk[:500] + "..." if len(chunk) > 500 else chunk
        })
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(chunks)} chunks to {filename}")

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("Loading PDFs...")
    docs = load_pdfs(PDF_FOLDER)
    print(f"Loaded {len(docs)} chunks")

    save_chunks([d.page_content for d in docs], "chunks.json")
    
    print("Creating vectorstore...")
    vectorstore = create_vectorstore(docs)
    retriever = get_retriever(vectorstore, k=20)
    
    llm = get_llm()
    cache = load_cache()
    
    results = {}
    for company in COMPANIES:
        results[company] = {}
        for rtype in REPORT_TYPES:
            key = f"{company}_{rtype}"
            print(f"Extracting: {company} - {rtype}")
            results[company][rtype] = extract_for_company_retriever(
                company, rtype, retriever, llm, cache, key
            )
            save_cache(cache)
    
    # Build table
    metrics = ["Revenue", "EBIT", "Operating_margin", "Cash_metric", "Net_liquidity", 
               "Return_on_capital", "Cost_of_capital", "EPS", "Dividend_per_share", "Market_cap_at_100EUR"]
    
    # Determine columns based on which report types were run
    if QUARTERLY_ONLY:
        columns = [f"{c} Q" for c in COMPANIES]
    else:
        columns = [f"{c} FY" for c in COMPANIES] + [f"{c} Q" for c in COMPANIES]
    
    table_data = {col: [] for col in columns}
    
    for metric in metrics:
        for company in COMPANIES:
            fy_data = results[company].get("Full Year 2025", {})
            q_data = results[company].get("Quarterly 2025", {})
            
            if metric == "Operating_margin":
                fy_rev = fy_data.get("Revenue", "Not Reported")
                fy_ebit = fy_data.get("EBIT", "Not Reported")
                q_rev = q_data.get("Revenue", "Not Reported")
                q_ebit = q_data.get("EBIT", "Not Reported")
                
                try:
                    if fy_rev != "Not Reported" and fy_ebit != "Not Reported":
                        fy_rev_num = float(str(fy_rev).replace(",", "").split()[0])
                        fy_ebit_num = float(str(fy_ebit).replace(",", "").split()[0])
                        fy_margin = f"{(fy_ebit_num/fy_rev_num)*100:.1f}%"
                    else:
                        fy_margin = "Not Reported"
                except:
                    fy_margin = "Not Reported"
                
                try:
                    if q_rev != "Not Reported" and q_ebit != "Not Reported":
                        q_rev_num = float(str(q_rev).replace(",", "").split()[0])
                        q_ebit_num = float(str(q_ebit).replace(",", "").split()[0])
                        q_margin = f"{(q_ebit_num/q_rev_num)*100:.1f}%"
                    else:
                        q_margin = "Not Reported"
                except:
                    q_margin = "Not Reported"
                
                if QUARTERLY_ONLY:
                    table_data[f"{company} Q"].append(q_margin)
                else:
                    table_data[f"{company} FY"].append(fy_margin)
                    table_data[f"{company} Q"].append(q_margin)
            else:
                fy = fy_data.get(metric, "Not Reported")
                q = q_data.get(metric, "Not Reported")
                if QUARTERLY_ONLY:
                    table_data[f"{company} Q"].append(q)
                else:
                    table_data[f"{company} FY"].append(fy)
                    table_data[f"{company} Q"].append(q)
    
    df = pd.DataFrame(table_data, index=metrics)
    markdown = df.to_markdown()

    os.makedirs("output", exist_ok=True)
    
    # Save with timestamp
    with open(f"output/table_{timestamp}.md", "w") as f:
        f.write(markdown)
    print(f"✅ Table saved: output/table_{timestamp}.md")
    
    # Save latest
    with open("output/table_latest.md", "w") as f:
        f.write(markdown)
    
    # Substitutions
    subs = []
    for company in COMPANIES:
        for rtype in REPORT_TYPES:
            s = results[company].get(rtype, {}).get("substitutions", "")
            if s and s != "None":
                subs.append(f"{company} {rtype}: {s}")
    
    with open(f"output/substitutions_{timestamp}.txt", "w") as f:
        f.write("\n".join(subs))
    print(f"✅ Substitutions saved: output/substitutions_{timestamp}.txt")
    
    with open("output/substitutions_latest.txt", "w") as f:
        f.write("\n".join(subs))
    
    try:
        df.to_excel("output/table.xlsx")
        print("✅ Excel saved: output/table.xlsx")
    except:
        print("⚠️ Excel export skipped (openpyxl not installed)")
    
    print(f"\n✅ Done! Run timestamp: {timestamp}")
    print("\n" + "="*80)
    print(markdown)
    print("="*80)

if __name__ == "__main__":
    main()