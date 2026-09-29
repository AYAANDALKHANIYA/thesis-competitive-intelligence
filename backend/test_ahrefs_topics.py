import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.services.nlp.topics import extract_deterministic_topics
from pprint import pprint

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT content, title FROM documents WHERE company_id = (SELECT id FROM companies WHERE name = 'Ahrefs')"))
        docs = res.fetchall()
        
        doc_texts = []
        for d in docs:
            if d.content:
                doc_texts.append(d.content)
            elif d.title:
                doc_texts.append(d.title)
        
        print("Number of docs:", len(doc_texts))
        res = extract_deterministic_topics(doc_texts)
        pprint(res)

if __name__ == "__main__":
    asyncio.run(main())
