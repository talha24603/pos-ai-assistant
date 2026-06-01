"""
Query Router Service
====================
This module provides a rule-based query router to classify user questions
into SQL queries (for structured POS database inquiries/analytics), RAG queries
(for documentation, policies, guides, manuals), BOTH, or UNKNOWN.

It uses a pre-compiled, regex-based scoring system with configurable thresholds and weights,
making it fast, precise, and easily extensible.
"""

import re
from typing import Dict, List, Set, Tuple, TypedDict

# =====================================================================
# Constants & Configurations
# =====================================================================

# Default thresholds for decision routing
MIN_THRESHOLD: float = 1.0   # Min score for either SQL or RAG to be considered valid
BOTH_THRESHOLD: float = 2.0  # Min score for both routes to be considered for "BOTH"

# SQL Agent related intent keywords and phrases
SQL_INTENTS: List[str] = [
    "sales",
    "revenue",
    "profit",
    "inventory",
    "stock",
    "products",
    "customers",
    "orders",
    "trends",
    "analytics",
    "statistics",
    "performance",
    "reports",
    "low stock",
    "top selling",
    "monthly sales",
    "daily sales",
]

# RAG Agent related intent keywords and phrases
RAG_INTENTS: List[str] = [
    "policy",
    "refund policy",
    "return policy",
    "guide",
    "manual",
    "documentation",
    "faq",
    "onboarding",
    "instructions",
    "training",
    "procedures",
    "workflow",
    "how to",
]


class RoutingExplanation(TypedDict):
    """Detailed metadata explaining a routing decision."""
    sql_score: float
    rag_score: float
    matched_sql_keywords: List[str]
    matched_rag_keywords: List[str]
    decision: str


# =====================================================================
# Regex Helper & Compiler
# =====================================================================

def compile_keyword_pattern(keyword: str) -> re.Pattern:
    """
    Compiles a keyword or phrase into a regular expression pattern.
    Uses word boundaries (\\b) to ensure partial word matches do not occur,
    handles flexible whitespace for multi-word phrases, and automatically
    supports singular/plural inflections (e.g. product/products, policy/policies).
    
    Args:
        keyword: The input intent term or phrase.
        
    Returns:
        A compiled regular expression Pattern.
    """
    cleaned = keyword.strip().lower()
    
    # Special casing for FAQ acronym
    if cleaned == "faq":
        return re.compile(r'\bfaqs?\b', re.IGNORECASE)
        
    # Split the phrase into words to inject singular/plural options per word
    words = cleaned.split()
    pattern_parts = []
    
    for word in words:
        # Check endings and build singular/plural variations
        if word.endswith("ies"):
            stem = re.escape(word[:-3])
            part = rf"{stem}(y|ies)"
        elif word.endswith("y"):
            stem = re.escape(word[:-1])
            part = rf"{stem}(y|ies)"
        elif word.endswith("s"):
            stem = re.escape(word[:-1])
            part = rf"{stem}s?"
        else:
            # Singular term, allow optional plural 's'
            part = rf"{re.escape(word)}s?"
            
        pattern_parts.append(part)
        
    # Join the word patterns with flexible whitespace
    pattern_str = r'\s+'.join(pattern_parts)
    
    return re.compile(rf'\b{pattern_str}\b', re.IGNORECASE)


# Pre-compile the pattern lists for high runtime performance
SQL_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (kw, compile_keyword_pattern(kw)) for kw in SQL_INTENTS
]

RAG_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (kw, compile_keyword_pattern(kw)) for kw in RAG_INTENTS
]


# =====================================================================
# Router Service Functions
# =====================================================================

def calculate_score(question: str, patterns: List[Tuple[str, re.Pattern]]) -> Tuple[float, List[str]]:
    """
    Calculates the classification score for a given question against a list of pre-compiled patterns.
    Each unique pattern match adds 1.0 to the score.
    
    Args:
        question: The user input text.
        patterns: Pre-compiled regex patterns coupled with their keyword names.
        
    Returns:
        A tuple of (total_score, list_of_matched_keywords).
    """
    score = 0.0
    matched_keywords: List[str] = []
    
    for keyword, pattern in patterns:
        if pattern.search(question):
            score += 1.0
            matched_keywords.append(keyword)
            
    return score, matched_keywords


def route_query_detailed(question: str) -> RoutingExplanation:
    """
    Analyzes the question and returns the routing decision along with detailed metrics and explanations.
    
    Args:
        question: The user's input question string.
        
    Returns:
        A dictionary containing the decision, individual scores, and matched keywords.
    """
    # Safe fallback if input is None or empty
    if not question or not question.strip():
        return {
            "sql_score": 0.0,
            "rag_score": 0.0,
            "matched_sql_keywords": [],
            "matched_rag_keywords": [],
            "decision": "UNKNOWN"
        }
        
    # Calculate scores and track matched terms
    sql_score, matched_sql = calculate_score(question, SQL_PATTERNS)
    rag_score, matched_rag = calculate_score(question, RAG_PATTERNS)
    
    # Routing decision logic:
    # 1. Check for BOTH: both must be >= BOTH_THRESHOLD
    if sql_score >= BOTH_THRESHOLD and rag_score >= BOTH_THRESHOLD:
        decision = "BOTH"
    # 2. SQL Agent priority
    elif sql_score > rag_score and sql_score >= MIN_THRESHOLD:
        decision = "SQL"
    # 3. RAG Agent priority
    elif rag_score > sql_score and rag_score >= MIN_THRESHOLD:
        decision = "RAG"
    # 4. Tie-breaker when both are non-zero, equal, and meet minimum threshold
    elif sql_score == rag_score and sql_score >= MIN_THRESHOLD:
        # Since they are equal and above threshold, route to BOTH to be comprehensive
        decision = "BOTH"
    # 5. Default fallback to UNKNOWN
    else:
        decision = "UNKNOWN"
        
    return {
        "sql_score": sql_score,
        "rag_score": rag_score,
        "matched_sql_keywords": matched_sql,
        "matched_rag_keywords": matched_rag,
        "decision": decision
    }


def route_query(question: str) -> str:
    """
    Routes a user question to one of the backend systems.
    
    Args:
        question: The user's input question string.
        
    Returns:
        One of the strings: "SQL", "RAG", "BOTH", "UNKNOWN".
    """
    explanation = route_query_detailed(question)
    return explanation["decision"]
