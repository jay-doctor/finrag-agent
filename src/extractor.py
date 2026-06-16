import os
import random
import logging
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from src.prompt_templates import EXTRACTION_PROMPT
from src.utils import extract_json_from_response

logging.basicConfig(level=logging.INFO)

def get_llm():
    # Try OpenAI first
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
        except Exception as e:
            logging.warning(f"OpenAI failed: {e}. Falling back to Groq.")
    
    # Fallback to Groq
    keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
    ]
    valid_keys = [k for k in keys if k]
    if not valid_keys:
        raise ValueError("No API keys found")
    api_key = random.choice(valid_keys)
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=api_key)

def get_queries(company, report_type):
    """Return report-type specific queries."""
    if report_type == "Quarterly 2025":
        # Quarterly-specific queries
        if company in ["BMW", "Mercedes"]:
            return [
                f"{company} interim report Q1 2026 revenue EBIT",
                f"{company} quarterly results 2026 income statement",
                f"{company} Q1 2026 financial summary revenue",
                f"{company} first quarter 2026 earnings EBIT"
            ]
        else:  # Volkswagen
            return [
                f"{company} Quartalsbericht Q1 2026 Umsatzerlöse",
                f"{company} Zwischenbericht 2026 Operatives Ergebnis",
                f"{company} Q1 2026 Konzernabschluss Umsatzerlöse",
                f"{company} erste drei Monate 2026 Ergebnis"
            ]
    else:  # Full Year
        if company in ["BMW", "Mercedes"]:
            return [
                f"{company} consolidated statement of income revenue 2025",
                f"{company} profit and loss statement EBIT 2025",
                f"{company} annual report financial summary revenue EBIT",
                f"{company} income statement consolidated results",
                f"{company} key financial figures revenue operating result"
            ]
        else:  # Volkswagen
            return [
                f"{company} Konzern-Gewinn- und Verlustrechnung Umsatzerlöse 2025",
                f"{company} Konzernabschluss Operatives Ergebnis 2025",
                f"{company} Geschäftsbericht Finanzkennzahlen Umsatzerlöse",
                f"{company} Bilanz Gewinn- und Verlustrechnung Konzern",
                f"{company} Konzernlagebericht Ertragslage Umsatzerlöse"
            ]

def extract_for_company_retriever(company, report_type, retriever, llm, cache, cache_key):
    if cache_key in cache:
        return cache[cache_key]
    
    queries = get_queries(company, report_type)
    
    all_docs = []
    for query in queries:
        # ✅ Fix: use $and to combine multiple metadata filters
        docs = retriever.invoke(query, filter={"$and": [{"company": company}, {"report_type": report_type}]})
        all_docs.extend(docs)
    
    unique_chunks = []
    seen = set()
    for doc in all_docs:
        chunk_hash = hash(doc.page_content[:200])
        if chunk_hash not in seen:
            unique_chunks.append(doc)
            seen.add(chunk_hash)

    logging.info(f"Retrieved {len(unique_chunks)} unique chunks for {company} {report_type}")
    
    context = "\n---\n".join([d.page_content for d in unique_chunks[:10]])
    
    prompt = PromptTemplate(template=EXTRACTION_PROMPT, input_variables=["company", "report_type", "context"])
    response = llm.invoke(prompt.format(company=company, report_type=report_type, context=context))
    
    data = extract_json_from_response(response.content)
    if not data:
        data = {"error": "parse_failed"}
    
    cache[cache_key] = data
    return data