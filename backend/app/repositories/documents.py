"""Document repository — database access layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentVersion


class DocumentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        company_id: Optional[int] = None,
        source_id: Optional[int] = None,
        is_processed: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[Document], int]:
        query = select(Document)
        count_query = select(func.count(Document.id))

        if company_id:
            query = query.where(Document.company_id == company_id)
            count_query = count_query.where(Document.company_id == company_id)
        if source_id:
            query = query.where(Document.source_id == source_id)
            count_query = count_query.where(Document.source_id == source_id)
        if is_processed is not None:
            query = query.where(Document.is_processed == is_processed)
            count_query = count_query.where(Document.is_processed == is_processed)
        if start_date is not None:
            query = query.where(Document.collected_at >= start_date)
            count_query = count_query.where(Document.collected_at >= start_date)
        if end_date is not None:
            query = query.where(Document.collected_at <= end_date)
            count_query = count_query.where(Document.collected_at <= end_date)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(Document.collected_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, document_id: int) -> Optional[Document]:
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_url_and_company(
        self, url: str, company_id: int
    ) -> Optional[Document]:
        result = await self.db.execute(
            select(Document).where(
                Document.url == url, Document.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_content_hash(self, content_hash: str) -> Optional[Document]:
        result = await self.db.execute(
            select(Document).where(Document.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def get_unprocessed(
        self, limit: int = 100, company_id: Optional[int] = None
    ) -> List[Document]:
        query = select(Document).where(Document.is_processed.is_(False))
        if company_id:
            query = query.where(Document.company_id == company_id)
        result = await self.db.execute(
            query.order_by(Document.collected_at.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Document:
        doc = Document(**kwargs)
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def update_content(
        self, document: Document, content: str, content_hash: str, title: Optional[str] = None
    ) -> Document:
        """Update document content and create a version record."""
        # Create version of old content
        version_count = await self._get_version_count(document.id)
        if document.content:
            version = DocumentVersion(
                document_id=document.id,
                content=document.content,
                content_hash=document.content_hash or "",
                version_number=version_count + 1,
            )
            self.db.add(version)

        document.content = content
        document.content_hash = content_hash
        if title:
            document.title = title
        document.is_processed = False  # Mark for re-processing
        document.collected_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def mark_processed(self, document_id: int) -> None:
        doc = await self.get_by_id(document_id)
        if doc:
            doc.is_processed = True
            await self.db.flush()

    async def count(self, company_id: Optional[int] = None) -> int:
        query = select(func.count(Document.id))
        if company_id:
            query = query.where(Document.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_processed(self, company_id: Optional[int] = None) -> int:
        query = select(func.count(Document.id)).where(Document.is_processed.is_(True))
        if company_id:
            query = query.where(Document.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_version_count(self, document_id: int) -> int:
        result = await self.db.execute(
            select(func.count(DocumentVersion.id)).where(
                DocumentVersion.document_id == document_id
            )
        )
        return result.scalar() or 0

    async def get_company_documents_with_content(
        self, company_id: int, limit: int = 500
    ) -> List[Document]:
        result = await self.db.execute(
            select(Document)
            .where(
                Document.company_id == company_id,
                Document.content.isnot(None),
                Document.content != "",
            )
            .order_by(Document.collected_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
