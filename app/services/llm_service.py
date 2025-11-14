from openai import AsyncOpenAI
from typing import List, Tuple
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)


class LLMService:
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        """Получаем embedding для текста"""
        try:
            response = await client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise
    
    @staticmethod
    async def generate_answer(question: str, context: str) -> Tuple[str, int]:
        """Генерируем ответ используя контекст из RAG"""
        system_prompt = """Ты - умный помощник по продукту SmartTask. 
Отвечай на вопросы пользователей используя предоставленный контекст.
Если информации нет в контексте, честно скажи об этом.
Отвечай кратко и по делу на русском языке."""
        
        user_prompt = f"""Контекст из документации:
{context}

Вопрос пользователя: {question}

Ответ:"""
        
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            logger.info(f"LLM response: {tokens} tokens")
            return answer, tokens
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
