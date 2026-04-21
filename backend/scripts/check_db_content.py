import asyncio
import os
import sys
sys.path.append(os.getcwd())
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.models.knowledge import KnowledgeBase, KnowledgeDocument
from app.core.config import settings
import uuid

async def check_kb_contents():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Compter les bases de connaissances
        kb_result = await session.execute(select(KnowledgeBase))
        kb_list = kb_result.scalars().all()
        print(f"--- Rapport des Bases de Connaissances ({len(kb_list)}) ---")
        
        for kb in kb_list:
            # 2. Compter les documents pour chaque KB
            doc_result = await session.execute(
                select(func.count(KnowledgeDocument.id))
                .filter(KnowledgeDocument.knowledge_base_id == kb.id)
            )
            doc_count = doc_result.scalar()
            
            print(f"\nBase: {kb.name}")
            print(f"ID: {kb.id}")
            print(f"Nombre de documents: {doc_count}")
            
            if doc_count > 0:
                docs = await session.execute(
                    select(KnowledgeDocument).filter(KnowledgeDocument.knowledge_base_id == kb.id)
                )
                for d in docs.scalars().all():
                    print(f"  - Document: {d.filename} ({d.file_type}, {d.chunk_count} chunks)")
            else:
                print("  ⚠️ Cette base est vide.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_kb_contents())
