"""Prompt templates for all LLM extraction tasks."""

CLASSIFY_DOCUMENT = """Analyze this engineering document and classify it into exactly ONE of these types:
- manual (operation/maintenance manual)
- pid (P&ID, piping and instrumentation diagram)
- spec (technical specification)
- logbook (operational logbook entry)
- drawing (technical drawing, schematic)
- report (incident report, RCA, inspection report)
- other

Return ONLY the type keyword, nothing else.

Document text (first 2000 chars):
{text}"""

EXTRACT_PROJECT_NAME = """From the following engineering document text, extract the project name or plant/station name.
Return ONLY the project name. If not found, return "Unknown".

Document text:
{text}"""

STRUCTURED_SUMMARY = """Analyze this engineering document and provide a structured summary in JSON format.
Return ONLY valid JSON with these exact keys:

{{
  "short_summary": "1-2 sentence overview",
  "purpose": "What is the document's purpose",
  "tech_summary": "Key technical findings, parameters, or specifications",
  "location": "Project location or plant site (if mentioned, else null)",
  "doc_date": "Document date in YYYY-MM-DD format (if found, else null)",
  "station": "Power station name (if mentioned, else null)",
  "unit": "Unit number or identifier (if mentioned, else null)"
}}

Document text:
{text}"""

EXTRACT_ENTITIES = """Extract engineering entities from this text. Return ONLY valid JSON array.
Each entity should have: {{"type": "equipment|instrument|valve|line|parameter", "name": "tag/identifier", "context": "brief context"}}

Focus on:
- Equipment tags (e.g., P-1101, TG-01, FAN-A, PUMP-B)
- Instrument tags (e.g., PT-201, TT-xxx, FT-100)
- Valve tags (e.g., XV-104, PRV-204, MOV-001)
- Line identifiers (e.g., 6"-LP-001, MAIN FEED LINE)
- Key parameters (pressure: X bar, temperature: Y°C, vibration: Z µm)

Text:
{text}"""

EXTRACT_DRAWING_TAGS = """Analyze this engineering drawing/P&ID image.
Extract all visible tags, labels, and equipment identifiers.

Return ONLY valid JSON array:
[{{"tag": "TAG-NAME", "label": "description if visible", "estimated_location": "top-left|top-right|center|bottom-left|bottom-right"}}]

If no tags are found, return an empty array: []"""

CHAT_SYSTEM_PROMPT = """You are DOCS.ai, an engineering document assistant for a power generation company.

RULES:
1. Answer ONLY based on the provided context/evidence. Never fabricate facts.
2. Always cite your sources with document filename and page number.
3. If the information is not found in the context, say "I could not find this information in the repository" and suggest related topics.
4. For engineering values (pressures, temperatures, vibration levels), quote them exactly as found.
5. Be concise but thorough in technical explanations.
6. When mentioning equipment tags, quote them exactly (e.g., PRV-204, PT-201).

Context from the document repository will be provided with each query."""

CHAT_RAG_PROMPT = """Based on the following retrieved evidence, answer the user's question.

EVIDENCE:
{evidence}

USER QUESTION: {query}

Provide:
1. A direct answer
2. Key findings (bullet points if applicable)
3. Source citations in format [Document: filename, Page: N]

If the evidence doesn't contain enough information to answer, say so clearly."""
