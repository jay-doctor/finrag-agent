EXTRACTION_PROMPT = """
Extract financial metrics from provided text only.

RULES:
- Use ONLY the text below. No external knowledge.
- Do NOT use data from other companies. Only use data explicitly linked to {company}.
- If a metric is not found, output "Not Reported".
- Never invent numbers.
- Output ONLY the JSON – no extra text.
- For each metric, extract ONLY ONE value (not multiple).
- If multiple values exist, pick the most recent/full-year figure.

The text may be in English or German. Use these translations:
- Revenue = Umsatzerlöse
- EBIT = Operatives Ergebnis (or EBIT)
- Operating margin = Operative Umsatzrendite (or EBIT/Revenue)
- Cash metric = Free Cash Flow, Net Cash Flow, Netto-Cashflow
- Net liquidity = Nettoliquidität (or net debt)
- Return on capital = Kapitalrendite (RoI, ROCE, ROIC)
- Cost of capital = Kapitalkosten (or hurdle concept, WACC)
- EPS = Ergebnis je Aktie
- Dividend per share = Dividende je Aktie

Company: {company} | Report type: {report_type}

Extract these metrics:
1. Revenue (million EUR if possible)
2. EBIT (million EUR)
3. Operating margin (percentage, calculated if needed)
4. Cash metric (e.g., Free Cash Flow, Net Cash Flow)
5. Net liquidity (e.g., net cash/debt position)
6. Return on capital (percentage)
7. Cost of capital (only if explicitly disclosed, else "Not Disclosed")
8. EPS (EUR)
9. Dividend per share (EUR)
10. Market cap if share price = 100 EUR/share (calculate from outstanding shares if available, else "Not Reported")

For each metric, output a single numeric value with unit (e.g., "132,214 million euros"). Do NOT list multiple numbers.

Text:
{context}

OUTPUT JSON ONLY:
{{
  "company": "{company}",
  "report_type": "{report_type}",
  "Revenue": "value or Not Reported",
  "EBIT": "value or Not Reported",
  "Operating_margin": "value% or Not Reported",
  "Cash_metric": "value or Not Reported",
  "Net_liquidity": "value or Not Reported",
  "Return_on_capital": "value or Not Reported",
  "Cost_of_capital": "value or Not Reported",
  "EPS": "value or Not Reported",
  "Dividend_per_share": "value or Not Reported",
  "Market_cap_at_100EUR": "value or Not Reported",
  "substitutions": "explain any replaced metric name, else 'None'"
}}
"""