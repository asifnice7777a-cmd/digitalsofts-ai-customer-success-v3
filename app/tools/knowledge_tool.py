# from langchain_core.tools import tool
# from app.rag.vector_store import vector_store


# @tool
# def search_company_knowledge(query: str) -> str:
#     """Search DigitalSofts' knowledge base for information about services, pricing, and FAQs relevant to the query."""
#     results = ve                                                                                                                                                 ctor_store.search(query, top_k=3)
#     if not results:
#         return "No relevant information found in the knowledge base."
#     return " | ".join(f"[{r['title']}] {r['content']}" for r in results)

# knowledge_tool.py
# from langchain_core.tools import tool
# from app.rag.vector_store import vector_store


# @tool
# def search_company_knowledge(query: str) -> str:
#     """Search DigitalSofts' knowledge base for information about services, pricing, and FAQs relevant to the query."""
#     results = vector_store.search(query, top_k=3)
#     if not results:
#         return "No relevant information found in the knowledge base."
#     return " | ".join(f"[{r['title']}] {r['content']}" for r in results)

# from langchain_core.tools import tool
# from app.rag.vector_store import vector_store
# from app.rag.knowledge_base import KNOWLEDGE_BASE


# # Small alias map so common pricing-related phrasing (e.g. "price", "cost")
# # still resolves to the "pricing" category, even though those exact words
# # don't literally appear in the knowledge base text.
# _CATEGORY_ALIASES = {
#     "price": "pricing",
#     "prices": "pricing",
#     "pricing": "pricing",
#     "cost": "pricing",
#     "costs": "pricing",
#     "quote": "pricing",
#     "quotes": "pricing",
# }


# def _keyword_lookup(query: str):
#     q = query.lower().strip()
#     words = q.split()
#     matches = []
#     seen_ids = set()

#     for item in KNOWLEDGE_BASE:
#         category = item["category"].lower()
#         title = item["title"].lower()
#         content = item["content"].lower()

#         is_match = q == category or q in title or q in content

#         if not is_match:
#             for word in words:
#                 if _CATEGORY_ALIASES.get(word, word) == category:
#                     is_match = True
#                     break

#         if is_match and item["id"] not in seen_ids:
#             matches.append(item)
#             seen_ids.add(item["id"])

#     return matches


# @tool
# def search_company_knowledge(query: str) -> str:
#     """Search DigitalSofts' knowledge base for information about services, pricing, and FAQs relevant to the query."""
#     keyword_matches = _keyword_lookup(query)
#     if keyword_matches:
#         return " | ".join(f"[{item['title']}] {item['content']}" for item in keyword_matches)

#     results = vector_store.search(query, top_k=3)
#     if not results:
#         return "No relevant information found in the knowledge base."
#     return " | ".join(f"[{r['title']}] {r['content']}" for r in results)


from langchain_core.tools import tool
from app.rag.vector_store import vector_store
from app.rag.knowledge_base import KNOWLEDGE_BASE

@tool
def search_company_knowledge(query: str) -> str:
    """Search DigitalSofts' knowledge base for information about services, pricing, and FAQs relevant to the query."""
    q = query.lower().strip()

    keyword_matches = [
        item for item in KNOWLEDGE_BASE
        if q in item["category"].lower() or q in item["title"].lower() or q in item["content"].lower()
    ]

    if keyword_matches:
        top_matches = keyword_matches[:3]
        return " | ".join(f"[{item['title']}] {item['content']}" for item in top_matches)

    results = vector_store.search(query, top_k=3)
    if not results:
        return "No relevant information found in the knowledge base."

    return " | ".join(f"[{r['title']}] {r['content']}" for r in results)