from typing import Dict, List
from app.services.rag_service import RAGService
from app.database import get_db
import asyncio
from app.utils.logger import logger


class RAGEvaluator:
    """Evaluate RAG system quality"""
    
    def __init__(self):
        self.test_questions = [
            {
                "question": "Как создать задачу?",
                "expected_keywords": ["нажмите", "создать", "кнопка", "+", "название"],
                "category": "task_management"
            },
            {
                "question": "How do I create a task?",
                "expected_keywords": ["click", "button", "create", "title", "+"],
                "category": "task_management"
            },
            {
                "question": "Где хранятся данные?",
                "expected_keywords": ["франкфурт", "германия", "aws", "европ", "сервер"],
                "category": "security"
            },
            {
                "question": "Where is data stored?",
                "expected_keywords": ["frankfurt", "germany", "aws", "europe", "server"],
                "category": "security"
            },
            {
                "question": "Какие интеграции поддерживаются?",
                "expected_keywords": ["slack", "google", "calendar", "github", "интеграц"],
                "category": "features"
            },
            {
                "question": "What integrations are available?",
                "expected_keywords": ["slack", "google", "calendar", "github", "integration"],
                "category": "features"
            },
            {
                "question": "Как включить двухфакторную аутентификацию?",
                "expected_keywords": ["настройк", "безопасн", "2fa", "qr", "код"],
                "category": "security"
            },
            {
                "question": "How to enable two-factor authentication?",
                "expected_keywords": ["settings", "security", "2fa", "qr", "code"],
                "category": "security"
            }
        ]
    
    async def evaluate(self) -> Dict:
        """Run evaluation on test questions"""
        results = {
            "total": len(self.test_questions),
            "passed": 0,
            "failed": 0,
            "by_category": {},
            "details": []
        }
        
        with get_db() as db:
            rag = RAGService(db)
            
            for test_case in self.test_questions:
                question = test_case["question"]
                expected_keywords = test_case["expected_keywords"]
                category = test_case["category"]
                
                try:
                    response = await rag.answer_question(question)
                    answer = response.answer.lower()
                    
                    found_keywords = [
                        kw for kw in expected_keywords 
                        if kw.lower() in answer
                    ]
                    
                    threshold = len(expected_keywords) * 0.4
                    passed = len(found_keywords) >= threshold
                    
                    if passed:
                        results["passed"] += 1
                    else:
                        results["failed"] += 1
                    
                    if category not in results["by_category"]:
                        results["by_category"][category] = {"passed": 0, "total": 0}
                    
                    results["by_category"][category]["total"] += 1
                    if passed:
                        results["by_category"][category]["passed"] += 1
                    
                    results["details"].append({
                        "question": question,
                        "category": category,
                        "passed": passed,
                        "found_keywords": found_keywords,
                        "expected_keywords": expected_keywords,
                        "keyword_match_rate": len(found_keywords) / len(expected_keywords),
                        "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer,
                        "response_time": response.response_time,
                        "tokens_used": response.tokens_used
                    })
                
                except Exception as e:
                    logger.error(f"Error evaluating question '{question}': {e}")
                    results["failed"] += 1
                    results["details"].append({
                        "question": question,
                        "category": category,
                        "passed": False,
                        "error": str(e)
                    })
        
        results["accuracy"] = results["passed"] / results["total"] if results["total"] > 0 else 0
        
        for category, stats in results["by_category"].items():
            stats["accuracy"] = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
        
        return results


async def run_eval():
    """Run and display evaluation results"""
    evaluator = RAGEvaluator()
    results = await evaluator.evaluate()
    
    print("\n" + "="*70)
    print("📊 RAG System Evaluation Results")
    print("="*70)
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Overall Accuracy: {results['accuracy']:.1%}")
    print("="*70)
    
    print("\n📁 Results by Category:")
    for category, stats in results['by_category'].items():
        print(f"  {category.upper()}:")
        print(f"    Passed: {stats['passed']}/{stats['total']} ({stats['accuracy']:.1%})")
    
    print("\n📝 Detailed Results:")
    print("-"*70)
    
    for detail in results['details']:
        status = "✅ PASS" if detail['passed'] else "❌ FAIL"
        print(f"\n{status} [{detail['category']}]")
        print(f"Question: {detail['question']}")
        
        if 'error' in detail:
            print(f"Error: {detail['error']}")
        else:
            match_rate = detail.get('keyword_match_rate', 0)
            print(f"Keyword Match: {match_rate:.1%}")
            print(f"Found: {detail['found_keywords']}")
            print(f"Expected: {detail['expected_keywords']}")
            print(f"Time: {detail.get('response_time', 0):.2f}s | Tokens: {detail.get('tokens_used', 0)}")
    
    print("\n" + "="*70)
    
    return results


if __name__ == "__main__":
    asyncio.run(run_eval())