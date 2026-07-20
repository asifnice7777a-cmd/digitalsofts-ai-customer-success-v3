# import re
# from typing import Dict


# SALES_KEYWORDS = ["price", "pricing", "cost", "quote", "package", "plan", "service", "offer", "buy", "purchase"]
# TECH_KEYWORDS = ["technology", "technologies", "stack", "architecture", "api", "integration", "technical", "cloud",
#                   "erp", "ai model", "database", "security", "postgresql", "mongodb", "mysql", "sql", "nosql", "db"]
# DOC_KEYWORDS = ["proposal", "document", "summary", "summarize", "report", "contract", "agreement"]
# MEETING_KEYWORDS = ["meeting", "call", "schedule", "demo", "appointment", "book a slot", "discuss"]


# NAME_PATTERN = re.compile(r"(?:my name is|i am|i'm)\s+([A-Z][a-zA-Z]+(?:[ \t]+[A-Z][a-zA-Z]+)?)", re.IGNORECASE)
# COMPANY_PATTERN = re.compile(r"(?:from|at|company is|represent|company:?)\s+([A-Z][a-zA-Z0-9&. ]{1,30})", re.IGNORECASE)
# BUDGET_PATTERN = re.compile(r"\$\s?\d{2,3}(?:,\d{3})*|\b\d+\s?k\b|\b\d+\s?thousand\b", re.IGNORECASE)
# TIMELINE_PATTERN = re.compile(r"(\d+\s?(?:weeks?|months?|days?))", re.IGNORECASE)
# EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
# MEETING_DATE_PATTERN = re.compile(
#     r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow|next week"
#     r"|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}"
#     r"|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
#     re.IGNORECASE,
# )
# MEETING_TIME_PATTERN = re.compile(
#     r"\b(\d{1,2}(?::\d{2})?\s?(?:am|pm)|morning|afternoon|evening)\b", re.IGNORECASE
# )
# PURPOSE_PATTERN = re.compile(r"purpose\s*:?\s*([^\n]+)", re.IGNORECASE)
# TECH_TERMS = ["python", "fastapi", "react", "node", "aws", "azure", "gcp", "java", "django", "flask", "sap",
#               "salesforce", "kubernetes", "ai", "machine learning"]

# # Each project type is matched against several natural phrasings, not just
# # one exact string, so e.g. "AI chatbot" and "ERP system" are both recognized
# # as their respective category. Checked in this order; the first category
# # with any matching keyword wins.
# PROJECT_TYPE_KEYWORDS = {
#     "AI solution": [
#         "ai chatbot", "chatbot", "ai model", "ai solution", "ai system",
#         "artificial intelligence", "machine learning",
#     ],
#     "web development": [
#         "web development", "website", "web app", "web application",
#     ],
#     "mobile app": [
#         "mobile app", "mobile application", "android app", "ios app",
#     ],
#     "ERP": [
#         "erp system", "erp",
#     ],
#     "cloud migration": [
#         "cloud migration", "migrate to the cloud", "move to the cloud",
#     ],
#     "custom software": [
#         "custom software", "custom application", "custom solution",
#     ],
# }

# QUESTION_STARTERS = {
#     "what", "which", "who", "whom", "whose", "where", "when", "why", "how",
#     "do", "does", "did", "is", "are", "am", "can", "could", "would", "will", "should",
# }




# def route_request(message: str) -> str:
#     text = message.lower()
#     if any(k in text for k in MEETING_KEYWORDS):
#         return "meeting"
#     if any(k in text for k in DOC_KEYWORDS):
#         return "documentation"
#     if any(k in text for k in TECH_KEYWORDS):
#         return "technical"
#     if any(k in text for k in SALES_KEYWORDS):
#         return "sales"

#     # No explicit topic keywords matched. Before defaulting to "sales", check
#     # whether this message looks like it's answering a Meeting Agent question
#     # (supplying a date, time, or email) rather than starting a new topic.
#     # This is a content-based heuristic only — route_request has no access to
#     # session state or the previously active agent, so this cannot guarantee
#     # true multi-turn continuity, only infer it from the message shape.
#     if MEETING_DATE_PATTERN.search(text) or MEETING_TIME_PATTERN.search(text) or EMAIL_PATTERN.search(message):
#         return "meeting"

#     return "sales"




# def extract_profile_fields(message: str) -> Dict[str, str]:
#     fields: Dict[str, str] = {}

#     if not _is_declarative(message):
#         return fields

#     text = message.lower()


#     name_match = NAME_PATTERN.search(message)
#     if name_match:
#         fields["client_name"] = name_match.group(1).strip()


#     company_match = COMPANY_PATTERN.search(message)
#     if company_match:
#         fields["company"] = company_match.group(1).strip()


#     budget_match = BUDGET_PATTERN.search(message)
#     if budget_match:
#         fields["budget"] = budget_match.group(0).strip()


#     timeline_match = TIMELINE_PATTERN.search(message)
#     if timeline_match:
#         fields["timeline"] = timeline_match.group(1).strip()


#     matched_tech_terms = [term for term in TECH_TERMS if term in text]
#     if matched_tech_terms:
#         fields["preferred_technology"] = ", ".join(matched_tech_terms)


#     for canonical_type, keywords in PROJECT_TYPE_KEYWORDS.items():
#         if any(keyword in text for keyword in keywords):
#             fields["project_type"] = canonical_type
#             break

#     if "project_type" not in fields:
#         purpose_match = PURPOSE_PATTERN.search(message)
#         if purpose_match:
#             fields["project_type"] = purpose_match.group(1).strip()


#     email_match = EMAIL_PATTERN.search(message)
#     if email_match:
#         fields["email"] = email_match.group(0).strip()


#     date_match = MEETING_DATE_PATTERN.search(text)
#     if date_match:
#         fields["meeting_date"] = date_match.group(1).strip()


#     time_match = MEETING_TIME_PATTERN.search(text)
#     if time_match:
#         fields["meeting_time"] = time_match.group(1).strip()


#     return fields




# def _is_declarative(message: str) -> bool:
#     stripped = message.strip()
#     if not stripped:
#         return True
#     if stripped.endswith("?"):
#         return False
#     first_word = stripped.split()[0].lower()
#     return first_word not in QUESTION_STARTERS


import re
from typing import Dict


HUMAN_HANDOFF_KEYWORDS = [
    "talk to a human", "speak to a human", "speak with a human",
    "connect me to a human", "talk to an agent", "speak with an agent",
    "speak to an agent", "human agent", "real person",
    "transfer me to support", "transfer me to a human",
    "escalate", "too complex", "need a consultant", "need to speak with a manager",
    "speak with a manager", "speak to a manager", "talk to a manager",
    "support team", "human representative", "talk to a representative",
    "speak with a representative",
]
SALES_KEYWORDS = ["price", "pricing", "cost", "quote", "package", "plan", "service", "offer", "buy", "purchase"]
TECH_KEYWORDS = ["technology", "technologies", "stack", "architecture", "api", "integration", "technical", "cloud",
                  "erp", "ai model", "database", "security", "postgresql", "mongodb", "mysql", "sql", "nosql", "db"]
DOC_KEYWORDS = ["proposal", "document", "summary", "summarize", "report", "contract", "agreement"]
MEETING_KEYWORDS = ["meeting", "call", "schedule", "demo", "appointment", "book a slot", "discuss"]


NAME_PATTERN = re.compile(r"(?:my name is|i am|i'm)\s+([A-Z][a-zA-Z]+(?:[ \t]+[A-Z][a-zA-Z]+)?)", re.IGNORECASE)
COMPANY_PATTERN = re.compile(r"(?:from|at|company is|represent|company:?)\s+([A-Z][a-zA-Z0-9&. ]{1,30})", re.IGNORECASE)
BUDGET_PATTERN = re.compile(r"\$\s?\d{2,3}(?:,\d{3})*|\b\d+\s?k\b|\b\d+\s?thousand\b", re.IGNORECASE)
TIMELINE_PATTERN = re.compile(r"(\d+\s?(?:weeks?|months?|days?))", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
MEETING_DATE_PATTERN = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow|next week"
    r"|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}"
    r"|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    re.IGNORECASE,
)
MEETING_TIME_PATTERN = re.compile(
    r"\b(\d{1,2}(?::\d{2})?\s?(?:am|pm)|morning|afternoon|evening)\b", re.IGNORECASE
)
PURPOSE_PATTERN = re.compile(r"purpose\s*:?\s*([^\n]+)", re.IGNORECASE)
TECH_TERMS = ["python", "fastapi", "react", "node", "aws", "azure", "gcp", "java", "django", "flask", "sap",
              "salesforce", "kubernetes", "ai", "machine learning"]

# Each project type is matched against several natural phrasings, not just
# one exact string, so e.g. "AI chatbot" and "ERP system" are both recognized
# as their respective category. Checked in this order; the first category
# with any matching keyword wins.
PROJECT_TYPE_KEYWORDS = {
    "AI solution": [
        "ai chatbot", "chatbot", "ai model", "ai solution", "ai system",
        "artificial intelligence", "machine learning",
    ],
    "web development": [
        "web development", "website", "web app", "web application",
    ],
    "mobile app": [
        "mobile app", "mobile application", "android app", "ios app",
    ],
    "ERP": [
        "erp system", "erp",
    ],
    "cloud migration": [
        "cloud migration", "migrate to the cloud", "move to the cloud",
    ],
    "custom software": [
        "custom software", "custom application", "custom solution",
    ],
}

QUESTION_STARTERS = {
    "what", "which", "who", "whom", "whose", "where", "when", "why", "how",
    "do", "does", "did", "is", "are", "am", "can", "could", "would", "will", "should",
}




def route_request(message: str) -> str:
    text = message.lower()
    if any(k in text for k in HUMAN_HANDOFF_KEYWORDS):
        return "human_handoff"
    if any(k in text for k in MEETING_KEYWORDS):
        return "meeting"
    if any(k in text for k in DOC_KEYWORDS):
        return "documentation"
    if any(k in text for k in TECH_KEYWORDS):
        return "technical"
    if any(k in text for k in SALES_KEYWORDS):
        return "sales"

    # No explicit topic keywords matched. Before defaulting to "sales", check
    # whether this message looks like it's answering a Meeting Agent question
    # (supplying a date, time, or email) rather than starting a new topic.
    # This is a content-based heuristic only — route_request has no access to
    # session state or the previously active agent, so this cannot guarantee
    # true multi-turn continuity, only infer it from the message shape.
    if MEETING_DATE_PATTERN.search(text) or MEETING_TIME_PATTERN.search(text) or EMAIL_PATTERN.search(message):
        return "meeting"

    return "sales"




def extract_profile_fields(message: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}

    if not _is_declarative(message):
        return fields

    text = message.lower()


    name_match = NAME_PATTERN.search(message)
    if name_match:
        fields["client_name"] = name_match.group(1).strip()


    company_match = COMPANY_PATTERN.search(message)
    if company_match:
        fields["company"] = company_match.group(1).strip()


    budget_match = BUDGET_PATTERN.search(message)
    if budget_match:
        fields["budget"] = budget_match.group(0).strip()


    timeline_match = TIMELINE_PATTERN.search(message)
    if timeline_match:
        fields["timeline"] = timeline_match.group(1).strip()


    matched_tech_terms = [term for term in TECH_TERMS if term in text]
    if matched_tech_terms:
        fields["preferred_technology"] = ", ".join(matched_tech_terms)


    for canonical_type, keywords in PROJECT_TYPE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            fields["project_type"] = canonical_type
            break

    if "project_type" not in fields:
        purpose_match = PURPOSE_PATTERN.search(message)
        if purpose_match:
            fields["project_type"] = purpose_match.group(1).strip()


    email_match = EMAIL_PATTERN.search(message)
    if email_match:
        fields["email"] = email_match.group(0).strip()


    date_match = MEETING_DATE_PATTERN.search(text)
    if date_match:
        fields["meeting_date"] = date_match.group(1).strip()


    time_match = MEETING_TIME_PATTERN.search(text)
    if time_match:
        fields["meeting_time"] = time_match.group(1).strip()


    return fields




def _is_declarative(message: str) -> bool:
    stripped = message.strip()
    if not stripped:
        return True
    if stripped.endswith("?"):
        return False
    first_word = stripped.split()[0].lower()
    return first_word not in QUESTION_STARTERS