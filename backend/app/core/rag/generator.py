"""RAG Generator using OpenRouter"""

from typing import List, Dict, Optional
import httpx
import logging
import re
import uuid
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGGenerator:
    """Generate responses using retrieved context and OpenRouter LLM"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_MODEL
        
        # API key is optional - will fail only if used without it
        if not self.api_key:
            logger.warning("⚠️  OPENROUTER_API_KEY not configured - LLM generation will fail if used")
    
    async def generate_response(
        self,
        query: str,
        context_chunks: Optional[List[Dict]] = None,
        history: Optional[List[Dict]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate response using context and LLM
        
        Args:
            query: User question
            context_chunks: Retrieved context chunks with metadata (optional)
            history: Optional list of previous messages
            max_tokens: Max response length
            temperature: Creativity (0-1)
            
        Returns:
            Dict with response and metadata
        """
        # Handle None or empty chunks
        chunks = context_chunks if context_chunks else []
        
        # Build context from chunks
        context_text = self._build_context(chunks)
        
        # Build prompt
        system_prompt = self._get_system_prompt(has_context=len(chunks) > 0)
        user_prompt = self._build_user_prompt(query, context_text)
        
        # Call OpenRouter
        try:
            response = await self._call_openrouter(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                history=history,
                max_tokens=max_tokens,
                temperature=temperature
            )

            answer = self._clean_response(response['content'])
            
            # Clean sources to ensure JSON serializability (convert UUIDs to strings)
            cleaned_sources = []
            for chunk in chunks:
                meta = chunk.get('metadata', {}).copy()
                for key, value in meta.items():
                    if isinstance(value, uuid.UUID):
                        meta[key] = str(value)
                cleaned_sources.append(meta)

            return {
                'answer': answer,
                'model': self.model,
                'sources': cleaned_sources,
                'context_used': len(chunks),
                'usage': response.get('usage', {})
            }
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context string from chunks"""
        context_parts = []
        
        for chunk in chunks:
            text = chunk.get('text', '')
            if text:
                context_parts.append(text)
        
        return "\n\n".join(context_parts)
    
    def _get_system_prompt(self, has_context: bool = True) -> str:
        """Get system prompt for RAG"""
        if has_context:
            return """Tu es un assistant commercial intelligent (AI Sales Assistant) qui aide les clients avec leurs questions sur nos produits et services.

Instructions :
1. Tu es spécialisé dans la vente et le support client
2. Utilise le contexte fourni pour répondre aux questions sur nos produits/services
3. Sois toujours courtois, professionnel et orienté vers le client
4. Si une question est hors sujet, redirige poliment vers nos services
5. N'affiche jamais de citations, de références, ni de marqueurs de type [Source X] dans la réponse finale
6. Réponds de manière concrète et précise: évite les formulations vagues comme "cela dépend" sans explication
7. Si la question concerne prix/offres: donne une fourchette indicative claire et ce qu'elle inclut
8. Si une info manque vraiment: dis-le en une phrase et pose UNE seule question de clarification très ciblée
9. Utilise un format commercial court: 2-5 phrases max, ou 3 puces max quand utile
10. Termine par une prochaine étape claire (devis, démo 15 min, ou question ciblée)
11. Réponds en français sauf si demandé autrement
12. N'aborde jamais de sujets techniques interno (comme FastAPI, bases de données, etc)
9. **IMPORTANT - Si l'email ou le téléphone est détecté dans le message** :
   - Intégrez naturellement la confirmation dans votre réponse (pas de message séparé)
   - Dites par exemple: "Merci pour votre email [email]. Notre équipe va vous contacter dans 24-48 heures pour discuter de vos besoins."
   - Soyez professionnel mais chaleureux
   - Donnez une estimation de temps de réponse (24-48h)
   - Ne posez pas à nouveau des questions sur ses coordonnées si elles viennent d'être fournies"""
        else:
            return """Tu es un assistant commercial intelligent (AI Sales Assistant) qui aide les clients avec leurs questions sur nos produits et services.

Instructions :
1. Tu es spécialisé dans la vente et le support client
2. Sois toujours courtois, professionnel et orienté vers le client
3. Si une question concerne nos produits/services, aide-le du mieux que tu peux
4. Réponds de manière concrète: donne des exemples d'usage, bénéfices et résultats attendus
5. Si la question est sur le prix: donne une fourchette indicative et propose le prochain pas (devis ou démo)
6. Si une info manque: pose UNE question de clarification précise, puis attends la réponse
7. Évite les réponses longues et génériques: maximum 5 phrases
8. N'aborde jamais de sujets techniques interno
9. Réponds en français sauf si demandé autrement
10. **IMPORTANT** : Si l'utilisateur fournit son email ou ses coordonnées, reconnaissez-le chaleureusement et confirmez que vous avez bien noté ses informations. Soyez enthousiaste!"""
    
    
    def _build_user_prompt(self, query: str, context: str) -> str:
        """Build user prompt with query and context"""
        if context.strip():
            return f"""Contexte :
{context}

Question : {query}

Réponse attendue :
- Réponse précise et exploitable (pas vague)
- 2 à 5 phrases maximum
- Une prochaine étape claire (devis, démo, ou question ciblée)
- Sans citer explicitement les sources"""
        else:
            return f"""Question : {query}

Réponse attendue :
- Réponse précise et exploitable (pas vague)
- 2 à 5 phrases maximum
- Une prochaine étape claire (devis, démo, ou question ciblée)"""

    def _clean_response(self, text: str) -> str:
        """Remove visible source markers and citation-like footnotes from the final answer."""
        cleaned = re.sub(r"\[\s*Source\s*\d+[^\]]*\]", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\(\s*Source\s*\d+[^\)]*\)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
    
    async def _call_openrouter(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[Dict]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict:
        """Call OpenRouter API"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "VoiceRAG App"
        }
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history if available
        if history:
            for msg in history:
                messages.append({"role": msg.get("role"), "content": msg.get("content")})
        
        # Add current user prompt
        messages.append({"role": "user", "content": user_prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract content
            if 'choices' not in data or not data['choices']:
                logger.error(f"Invalid response from OpenRouter: {data}")
                raise ValueError("No response content from LLM")
                
            message = data['choices'][0]['message']
            
            return {
                'content': message['content'],
                'usage': data.get('usage', {})
            }


# Global instance
rag_generator = RAGGenerator()
