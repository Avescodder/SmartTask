
from typing import Dict
from app.services.rag_service import RAGService
from app.database import get_db_context
import asyncio
from app.utils.logger import logger


class RAGEvaluator:
    """Evaluate RAG system quality based on ACTUAL documents"""
    
    def __init__(self):
        self.test_questions = [
            {
                "question": "Как создать задачу?",
                "expected_keywords": ["задача", "нажмите", "+", "название"],
                "category": "task_management"
            },
            
            {
                "question": "Где хранятся данные?",
                "expected_keywords": ["aws", "франкфурт", "германия"],
                "category": "security"
            },
            
            {
                "question": "Какие интеграции поддерживаются?",
                "expected_keywords": ["slack", "github", "google"],
                "category": "integrations"
            },
            
            {
                "question": "Как получить список задач через API?",
                "expected_keywords": ["get", "/tasks", "api"],
                "category": "api"
            },
            
            {
                "question": "Как управлять проектом?",
                "expected_keywords": ["kanban", "доска", "перетаскива"],
                "category": "project_management"
            },
            
            {
                "question": "Какое шифрование используется?",
                "expected_keywords": ["aes", "256", "шифрован"],
                "category": "security"
            },
            
            {
                "question": "Какие есть тарифные планы?",
                "expected_keywords": ["free", "pro", "enterprise"],
                "category": "pricing"
            },
            
            {
                "question": "Что делать если не приходят уведомления?",
                "expected_keywords": ["email", "спам", "настройк", "уведомлен"],
                "category": "troubleshooting"
            },
            
            {
                "question": "Какой максимальный размер файла?",
                "expected_keywords": ["50", "мб", "файл"],
                "category": "features"
            },
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
        
        with get_db_context() as db:
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
                        "tokens_used": response.tokens_used,
                        "sources_count": len(response.sources)
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
    for category, stats in sorted(results['by_category'].items()):
        passed = stats['passed']
        total = stats['total']
        accuracy = stats['accuracy']
        
        emoji = "✅" if accuracy >= 0.7 else "⚠️" if accuracy >= 0.5 else "❌"
        print(f"  {emoji} {category.upper()}:")
        print(f"      Passed: {passed}/{total} ({accuracy:.1%})")
    
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
            print(f"Sources: {detail.get('sources_count', 0)} | "
                  f"Time: {detail.get('response_time', 0):.2f}s | "
                  f"Tokens: {detail.get('tokens_used', 0)}")
    
    print("\n" + "="*70)

    if results['accuracy'] < 0.7:
        print("\n💡 Recommendations:")
        print("  1. Check if documents are loaded: docker compose logs api | grep 'Loaded'")
        print("  2. Increase top_k in config.py (try 5 or 7)")
        print("  3. Lower similarity_threshold (try 0.2)")
        print("  4. Use better model: OPENAI_MODEL=gpt-4o-mini")
    elif results['accuracy'] >= 0.7:
        print("\n🎉 Good results! System is working well.")
    
    print("="*70 + "\n")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_eval())