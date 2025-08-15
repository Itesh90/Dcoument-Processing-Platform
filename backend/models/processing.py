from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
from typing import Optional, Dict, Any, List
from datetime import datetime
import enum

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingStep(str, enum.Enum):
    OCR_EXTRACTION = "ocr_extraction"
    TEXT_CLEANING = "text_cleaning"
    ENTITY_RECOGNITION = "entity_recognition"
    CLASSIFICATION = "classification"
    VALIDATION = "validation"
    POST_PROCESSING = "post_processing"

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")
    processing_steps = Column(JSON)  # List of steps completed
    current_step = Column(String(50))  # Current processing step
    progress = Column(Integer, default=0)  # 0-100
    result_data = Column(JSON)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    estimated_completion = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="processing_jobs")
    user = relationship("User", back_populates="processing_jobs")
    audit_logs = relationship("ProcessingAuditLog", back_populates="processing_job")
    
    # Indexes
    __table_args__ = (
        Index('idx_processing_jobs_document_id', 'document_id'),
        Index('idx_processing_jobs_status', 'status'),
        Index('idx_processing_jobs_user_id', 'user_id'),
        Index('idx_processing_jobs_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, document_id={self.document_id}, status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert processing job object to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "status": self.status,
            "processing_steps": self.processing_steps,
            "current_step": self.current_step,
            "progress": self.progress,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "priority": self.priority,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_completed(self) -> bool:
        """Check if processing job is completed"""
        return self.status == ProcessingStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if processing job failed"""
        return self.status == ProcessingStatus.FAILED
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < 3 and self.status in [ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]
    
    def start_processing(self):
        """Mark job as started"""
        self.status = ProcessingStatus.RUNNING
        self.started_at = func.now()
        self.updated_at = func.now()
    
    def complete_processing(self, result_data: Dict[str, Any]):
        """Mark job as completed"""
        self.status = ProcessingStatus.COMPLETED
        self.result_data = result_data
        self.completed_at = func.now()
        self.progress = 100
        self.updated_at = func.now()
    
    def fail_processing(self, error_message: str):
        """Mark job as failed"""
        self.status = ProcessingStatus.FAILED
        self.error_message = error_message
        self.updated_at = func.now()
    
    def update_progress(self, progress: int, current_step: str = None):
        """Update job progress"""
        self.progress = min(100, max(0, progress))
        if current_step:
            self.current_step = current_step
        self.updated_at = func.now()

class ProcessingAuditLog(Base):
    __tablename__ = "processing_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    processing_job_id = Column(Integer, ForeignKey("processing_jobs.id"), nullable=False)
    action = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    processing_job = relationship("ProcessingJob", back_populates="audit_logs")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ProcessingAuditLog(id={self.id}, action='{self.action}', job_id={self.processing_job_id})>"
