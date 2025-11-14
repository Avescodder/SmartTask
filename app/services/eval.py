from typing import Dict
from app.services.rag_service import RAGService
from app.database import get_db
import asyncio


class RAGEvaluator:
    """Оценка качества RAG системы"""
    
    def __init__(self):
        self.test_questions = [
            {
                "question": "Как создать задачу?",
                "expected_keywords": ["нажмите", "задача", "название", "дедлайн"]
            },
            {
                "question": "Где хранятся данные?",
                "expected_keywords": ["AWS", "Франкфурт", "Германия"]
            },
            {
                "question": "Какие интеграции поддерживаются?",
                "expected_keywords": ["Slack", "Google Calendar", "GitHub"]
            },
            {
                "question": "Как включить двухфакторную аутентификацию?",
                "expected_keywords": ["2FA", "настройках", "профиля"]
            }
        ]
    
    async def evaluate(self) -> Dict:
        """Запускаем eval"""
        results = {
            "total": len(self.test_questions),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        with get_db() as db:
            rag = RAGService(db)
            
            for test_case in self.test_questions:
                question = test_case["question"]
                expected_keywords = test_case["expected_keywords"]
                
                response = await rag.answer_question(question)
                answer = response.answer.lower()
                
                found_keywords = [
                    kw for kw in expected_keywords 
                    if kw.lower() in answer
                ]
                
                passed = len(found_keywords) >= len(expected_keywords) * 0.5
                
                if passed:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                
                results["details"].append({
                    "question": question,
                    "passed": passed,
                    "found_keywords": found_keywords,
                    "expected_keywords": expected_keywords,
                    "answer_preview": answer[:200]
                })
        
        results["accuracy"] = results["passed"] / results["total"]
        return results


async def run_eval():
    """Запуск оценки"""
    evaluator = RAGEvaluator()
    results = await evaluator.evaluate()
    
    print("\n" + "="*60)
    print("📊 RAG System Evaluation Results")
    print("="*60)
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Accuracy: {results['accuracy']:.1%}")
    print("="*60 + "\n")
    
    for detail in results['details']:
        status = "✅" if detail['passed'] else "❌"
        print(f"{status} {detail['question']}")
        print(f"   Found: {detail['found_keywords']}")
        print(f"   Expected: {detail['expected_keywords']}")
        print()
    
    return results


if __name__ == "__main__":
    asyncio.run(run_eval())