"""
Integration Test Suite for Unified Assistant Route
==================================================
This script exercises the `/assistant` endpoint using FastAPI's standard `TestClient`.
It validates the dynamic pipeline end-to-end for:
- SQL Analytics queries
- RAG Policy/Document retrievals
- BOTH (SQL + RAG) Synthesized hybrid results
- UNKNOWN Intent fallback handling
"""

import sys
import os

# Ensure workspace root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

# Create the test client
client = TestClient(app)

TEST_QUERIES = [
    {
        "question": "What are our total sales and revenue for this month?",
        "expected_route": "SQL",
        "tenant_id": "tenant-123"
    },
    {
        "question": "Where is the onboarding guide for new cashier staff?",
        "expected_route": "RAG",
        "tenant_id": "tenant-123"
    },
    {
        "question": "What are the top selling products and what does our refund policy say about them?",
        "expected_route": "BOTH",
        "tenant_id": "tenant-123"
    },
    {
        "question": "How many units of each product were sold?",
        "expected_route": "SQL",
        "tenant_id": "cmdxzt9qy0007v4tg9e942hmb"
    },
    {
        "question": "Hello there! Can you write me a quick poem about coffee?",
        "expected_route": "UNKNOWN",
        "tenant_id": "tenant-123"
    }
]


def test_endpoint():
    print("=" * 110)
    print("RUNNING END-TO-END ASSISTANT INTEGRATION TESTS")
    print("=" * 110)
    
    passed = 0
    total = len(TEST_QUERIES)
    
    for idx, case in enumerate(TEST_QUERIES, 1):
        q = case["question"]
        expected = case["expected_route"]
        tenant = case["tenant_id"]
        
        print(f"\n[Test Case {idx}/{total}] Question: '{q}'")
        print(f" -> Expected Route: {expected}")
        
        try:
            payload = {
                "question": q,
                "tenant_id": tenant,
                "enforce_tenant": True
            }
            
            response = client.post("/assistant", json=payload)
            
            if response.status_code != 200:
                print(f" -> ERROR: Status Code {response.status_code}")
                print(f"    Detail: {response.text}")
                continue
                
            res_data = response.json()
            actual_route = res_data.get("route")
            answer = res_data.get("answer")
            explanation = res_data.get("routing_explanation", {})
            
            print(f" -> Actual Route: {actual_route}")
            print(f" -> Calculated SQL Score: {explanation.get('sql_score')} | RAG Score: {explanation.get('rag_score')}")
            print(f" -> Response Answer:\n    {answer}")
            
            if actual_route == expected:
                print(" -> STATUS: PASS")
                passed += 1
            else:
                print(f" -> STATUS: FAIL (Expected '{expected}', got '{actual_route}')")
                
        except Exception as e:
            print(f" -> CRITICAL CRASH: {str(e)}")
            
    print("\n" + "=" * 110)
    print(f"INTEGRATION TEST SUMMARY: {passed}/{total} CASES PASSED")
    print("=" * 110)
    
    return passed == total


if __name__ == "__main__":
    success = test_endpoint()
    sys.exit(0 if success else 1)
