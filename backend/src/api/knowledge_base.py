"""
Knowledge Base API Endpoints for WhatsApp RAG Assistant
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.business import Business
from ..models.knowledge_base import KnowledgeBase
from ..models.document import Document
from ..services.knowledge_base_service import KnowledgeBaseService
from ..services.auth_service import get_current_business
from ..schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse

router = APIRouter()
kb_service = KnowledgeBaseService()


@router.get("", response_model=List[KnowledgeBaseResponse])
def get_knowledge_bases(
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Get all knowledge bases for the current business."""
    knowledge_bases = db.query(KnowledgeBase).filter(
        KnowledgeBase.business_id == current_business.business_id
    ).all()

    return [
        KnowledgeBaseResponse(
            kb_id=str(kb.kb_id),
            name=kb.name,
            description=kb.description,
            source_type=kb.source_type,
            source_url=kb.source_url,
            document_count=kb.document_count,
            status=kb.status
        )
        for kb in knowledge_bases
    ]


@router.post("", response_model=KnowledgeBaseResponse)
def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Create a new knowledge base for the business."""
    new_kb = KnowledgeBase(
        business_id=current_business.business_id,
        name=kb_data.name,
        description=kb_data.description,
        source_type=kb_data.source_type,
        source_url=kb_data.source_url
    )

    db.add(new_kb)
    db.commit()
    db.refresh(new_kb)

    return KnowledgeBaseResponse(
        kb_id=str(new_kb.kb_id),
        name=new_kb.name,
        description=new_kb.description,
        source_type=new_kb.source_type,
        source_url=new_kb.source_url,
        document_count=new_kb.document_count,
        status=new_kb.status
    )


@router.post("/{kb_id}/upload")
def upload_documents(
    kb_id: str,
    files: List[UploadFile] = File(...),
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Upload documents to a knowledge base."""
    # Verify that the knowledge base belongs to the current business
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.kb_id == kb_id,
        KnowledgeBase.business_id == current_business.business_id
    ).first()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )

    # Process each uploaded file
    uploaded_files = []
    for file in files:
        # Save the file and add to the knowledge base
        document = kb_service.add_document_to_knowledge_base(file, kb_id, db)
        uploaded_files.append(document.filename)

        # Update document count
        kb.document_count += 1
        db.commit()

    return {"uploaded_files": uploaded_files}


@router.post("/{kb_id}/crawl")
def crawl_website(
    kb_id: str,
    url: str,
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Crawl a website and add content to the knowledge base."""
    # Verify that the knowledge base belongs to the current business
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.kb_id == kb_id,
        KnowledgeBase.business_id == current_business.business_id
    ).first()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )

    # Update the knowledge base with the source URL
    kb.source_url = url
    kb.source_type = "website"
    db.commit()

    # Perform the crawling in the background
    kb_service.crawl_and_index_website(kb_id, url)

    return {"status": "success", "message": f"Crawling initiated for {url}"}


@router.post("/{kb_id}/index")
def reindex_knowledge_base(
    kb_id: str,
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Trigger re-indexing of a knowledge base."""
    # Verify that the knowledge base belongs to the current business
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.kb_id == kb_id,
        KnowledgeBase.business_id == current_business.business_id
    ).first()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )

    # Update status and trigger re-indexing
    kb.status = "indexing"
    db.commit()

    # Perform the re-indexing in the background
    kb_service.reindex_knowledge_base(kb_id)

    return {"status": "success", "message": "Re-indexing initiated"}