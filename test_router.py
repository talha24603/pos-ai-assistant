"""
Test Suite for Rule-Based Query Router
======================================
This script validates the router service's decisions across diverse scenarios:
- SQL Analytics & Inventory
- RAG Documents & Policies
- BOTH (SQL + RAG) hybrid queries
- UNKNOWN / Ambiguous queries

It prints a comprehensive, readable evaluation report highlighting scores,
matched keywords, and the reasoning behind each routing decision.
"""

import sys
import os

# Ensure the root folder is on the python path to load the app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.router import route_query_detailed, MIN_THRESHOLD, BOTH_THRESHOLD

# Define test cases: (Question, Expected Decision, Description)
TEST_CASES = [
    # ----------------------------------------------------
    # SQL Intent Cases
    # ----------------------------------------------------
    (
        "What are our total sales and revenue for this month?",
        "SQL",
        "Analytics query matching multiple SQL terms (sales, revenue, monthly sales)"
    ),
    (
        "Check the inventory levels and see which products have low stock.",
        "SQL",
        "Operational inventory query matching stock terms (inventory, products, low stock)"
    ),
    (
        "Show me a performance report of the top selling items from daily sales.",
        "SQL",
        "Report query matching analytics terms (performance, reports, top selling, daily sales)"
    ),
    (
        "Who are our top customers based on recent orders?",
        "SQL",
        "Customer analytics query matching SQL database concepts (customers, orders)"
    ),
    (
        "What are the customer trends and statistics for the profit margins?",
        "SQL",
        "Analytics query matching SQL terms (trends, statistics, profit, customers)"
    ),
    
    # ----------------------------------------------------
    # RAG Intent Cases
    # ----------------------------------------------------
    (
        "What is our refund policy for electronic products?",
        "RAG",
        "Policy query matching RAG terms (refund policy, policy)"
    ),
    (
        "Where is the onboarding guide for new cashier staff?",
        "RAG",
        "User guide query matching RAG documentation terms (onboarding, guide)"
    ),
    (
        "Can you show me the training manual for refund procedures?",
        "RAG",
        "Training document query matching RAG manual terms (training, manual, procedures)"
    ),
    (
        "How to handle workflow instructions when returning items?",
        "RAG",
        "Procedural query matching RAG instructions terms (how to, workflow, instructions)"
    ),
    (
        "What does our return policy say about damaged stock?",
        "RAG",
        "Wait: 'return policy' is RAG, but 'stock' is SQL. Let's see if return policy (RAG) wins or if it's BOTH."
    ),
    
    # ----------------------------------------------------
    # BOTH (SQL & RAG) Hybrid Cases
    # ----------------------------------------------------
    (
        "What are the top selling products and what does our refund policy say about them?",
        "BOTH",
        "Exact prompt example querying both sales database and return policy guide."
    ),
    (
        "How do I generate a monthly sales report, and is there a manual on how to do it?",
        "BOTH",
        "Hybrid query searching for sales report (SQL) and manual guide instructions (RAG)."
    ),
    
    # ----------------------------------------------------
    # UNKNOWN / Ambiguous Cases
    # ----------------------------------------------------
    (
        "Hello, how are you today?",
        "UNKNOWN",
        "General greeting that does not contain domain-specific terms."
    ),
    (
        "What is the weather like in New York right now?",
        "UNKNOWN",
        "Out of scope general question."
    ),
]


def run_tests() -> bool:
    """Runs all test cases, outputs detailed results, and asserts performance."""
    print("=" * 110)
    print(f"RUNNING INTENT ROUTER TEST SUITE")
    print(f"Settings: MIN_THRESHOLD = {MIN_THRESHOLD}, BOTH_THRESHOLD = {BOTH_THRESHOLD}")
    print("=" * 110)
    
    passed_count = 0
    total_count = len(TEST_CASES)
    
    # ANSI escape colors for fancy output
    COLOR_SUCCESS = "\033[92m"
    COLOR_FAIL = "\033[91m"
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    
    # Check if terminal supports colors (disable if not on standard interactive terminal)
    if os.name == 'nt':
        # Enable virtual terminal processing on Windows if possible
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            COLOR_SUCCESS = ""
            COLOR_FAIL = ""
            COLOR_RESET = ""
            COLOR_BOLD = ""
            
    row_format = "{:<65} | {:<8} | {:<8} | {:<5} | {:<5} | {:<6}"
    
    print(COLOR_BOLD + row_format.format(
        "Question", "Expected", "Actual", "SQL", "RAG", "Result"
    ) + COLOR_RESET)
    print("-" * 110)
    
    for idx, (question, expected, desc) in enumerate(TEST_CASES, 1):
        explanation = route_query_detailed(question)
        actual = explanation["decision"]
        sql_score = explanation["sql_score"]
        rag_score = explanation["rag_score"]
        matched_sql = explanation["matched_sql_keywords"]
        matched_rag = explanation["matched_rag_keywords"]
        
        # Determine status.
        # Note: For the specific cross-over cases, we evaluate if it behaves reasonably.
        # Let's check "What does our return policy say about damaged stock?":
        # - "return policy", "policy" match RAG (Score = 2)
        # - "stock" matches SQL (Score = 1)
        # Since RAG (2.0) > SQL (1.0), it should route to RAG.
        # This matches expected behavior.
        is_correct = (actual == expected)
        
        status_str = ""
        if is_correct:
            status_str = f"{COLOR_SUCCESS}PASS{COLOR_RESET}"
            passed_count += 1
        else:
            # Let's be flexible on hybrid cases if they route to BOTH
            status_str = f"{COLOR_FAIL}FAIL{COLOR_RESET}"
            
        # Truncate question for pretty printing if too long
        display_question = question if len(question) <= 62 else question[:59] + "..."
        
        print(row_format.format(
            display_question,
            expected,
            actual,
            str(sql_score),
            str(rag_score),
            status_str
        ))
        
        # Detailed prints for matched keywords if verbose or failed
        if matched_sql or matched_rag:
            print(f"   -> SQL matched: {matched_sql} | RAG matched: {matched_rag}")
            
    print("=" * 110)
    accuracy = (passed_count / total_count) * 100
    print(f"Summary: {passed_count}/{total_count} test cases passed ({accuracy:.1f}%)")
    print("=" * 110)
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
