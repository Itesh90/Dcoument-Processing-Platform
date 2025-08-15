from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    REVIEW = "review"
    ARCHIVED = "archived"

class DocumentType(str, enum.Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    REGULATORY = "regulatory"
    RECEIPT = "receipt"
    STATEMENT = "statement"
    OTHER = "other"

class DocumentCategory(str, enum.Enum):
    FINANCIAL = "financial"
    LEGAL = "legal"
    REGULATORY = "regulatory"
    GENERAL = "general"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    document_type = Column(Enum(DocumentType), default=DocumentType.OTHER)
    document_category = Column(Enum(DocumentCategory), default=DocumentCategory.GENERAL)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    extracted_data = Column(JSON)
    confidence_score = Column(Integer)  # 0-100
    processing_time = Column(Integer)  # in milliseconds
    version = Column(Integer, default=1)
    tags = Column(JSON)  # Array of tags
    metadata = Column(JSON)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    processing_jobs = relationship("ProcessingJob", back_populates="document")
    audit_logs = relationship("DocumentAuditLog", back_populates="document")
    
    # Indexes
    __table_args__ = (
        Index('idx_documents_uploaded_by', 'uploaded_by'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_type', 'document_type'),
        Index('idx_documents_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert document object to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "document_type": self.document_type.value if self.document_type else None,
            "document_category": self.document_category.value if self.document_category else None,
            "status": self.status.value if self.status else None,
            "uploaded_by": self.uploaded_by,
            "extracted_data": self.extracted_data,
            "confidence_score": self.confidence_score,
            "processing_time": self.processing_time,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_processed(self) -> bool:
        """Check if document is processed"""
        return self.status == DocumentStatus.PROCESSED
    
    def is_failed(self) -> bool:
        """Check if document processing failed"""
        return self.status == DocumentStatus.FAILED
    
    def needs_review(self) -> bool:
        """Check if document needs human review"""
        return self.status == DocumentStatus.REVIEW or (self.confidence_score and self.confidence_score < 80)
    
    def archive(self):
        """Archive the document"""
        self.status = DocumentStatus.ARCHIVED
        self.deleted_at = func.now()
    
    def update_processing_result(self, extracted_data: Dict[str, Any], confidence_score: int, processing_time: int):
        """Update document with processing results"""
        self.extracted_data = extracted_data
        self.confidence_score = confidence_score
        self.processing_time = processing_time
        self.status = DocumentStatus.PROCESSED if confidence_score >= 80 else DocumentStatus.REVIEW
        self.updated_at = func.now()

# Document audit log for compliance
class DocumentAuditLog(Base):
    __tablename__ = "document_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    action = Column(String(50), nullable=False)  # upload, process, review, delete, etc.
    user_id = Column(Integer, ForeignKey("users.id"))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="audit_logs")
    user = relationship("User")
    
    def __repr__(self):
        return f"<DocumentAuditLog(id={self.id}, action='{self.action}', document_id={self.document_id})>"
