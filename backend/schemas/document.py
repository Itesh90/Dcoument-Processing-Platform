from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import mimetypes

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    REVIEW = "review"
    ARCHIVED = "archived"

class DocumentType(str, Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    REGULATORY = "regulatory"
    RECEIPT = "receipt"
    STATEMENT = "statement"
    OTHER = "other"

class DocumentCategory(str, Enum):
    FINANCIAL = "financial"
    LEGAL = "legal"
    REGULATORY = "regulatory"
    GENERAL = "general"

class DocumentBase(BaseModel):
    filename: str = Field(..., max_length=255, description="Document filename")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME type")
    document_type: Optional[DocumentType] = Field(None, description="Document type")
    document_category: Optional[DocumentCategory] = Field(None, description="Document category")
    tags: Optional[List[str]] = Field(None, description="Document tags")

    @validator('filename')
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        if len(v) > 255:
            raise ValueError('Filename too long')
        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in v for char in invalid_chars):
            raise ValueError('Filename contains invalid characters')
        return v.strip()

    @validator('mime_type')
    def validate_mime_type(cls, v, values):
        if v and values.get('filename'):
            # Guess MIME type from filename if not provided
            if not v:
                v = mimetypes.guess_type(values['filename'])[0]
            # Validate common document MIME types
            allowed_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'image/jpeg',
                'image/png',
                'image/tiff',
                'text/plain'
            ]
            if v not in allowed_types:
                raise ValueError(f'Unsupported file type: {v}')
        return v

class DocumentCreate(DocumentBase):
    file_path: str = Field(..., description="Path to the uploaded file")
    uploaded_by: int = Field(..., description="ID of the user who uploaded the document")

    @validator('file_path')
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError('File path cannot be empty')
        return v.strip()

class DocumentUpdate(BaseModel):
    document_type: Optional[DocumentType] = Field(None, description="Document type")
    document_category: Optional[DocumentCategory] = Field(None, description="Document category")
    status: Optional[DocumentStatus] = Field(None, description="Document status")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Extracted data from document")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="Confidence score (0-100)")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    version: Optional[int] = Field(None, ge=1, description="Document version")

    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Confidence score must be between 0 and 100')
        return v

class DocumentInDBBase(DocumentBase):
    id: int
    file_path: str
    status: DocumentStatus
    uploaded_by: int
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[int] = None
    processing_time: Optional[int] = None
    version: int = 1
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True

class Document(DocumentInDBBase):
    user: Optional[Any] = None  # Will be populated by the service
    processing_jobs: Optional[List[Any]] = None  # Will be populated by the service

    def needs_review(self) -> bool:
        """Check if document needs human review"""
        return (self.status == DocumentStatus.REVIEW or 
                (self.confidence_score and self.confidence_score < 80))

class DocumentInDB(DocumentInDBBase):
    pass

class DocumentListResponse(BaseModel):
    documents: List[Document]
    total: int
    page: int
    size: int

class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    upload_url: str
    expires_at: datetime

class DocumentProcessingRequest(BaseModel):
    document_id: int
    priority: int = Field(0, ge=0, le=10, description="Processing priority (0-10)")

class DocumentSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    document_type: Optional[DocumentType] = Field(None, description="Filter by document type")
    status: Optional[DocumentStatus] = Field(None, description="Filter by status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")

class DocumentStats(BaseModel):
    total_documents: int
    processed_documents: int
    failed_documents: int
    documents_by_type: Dict[str, int]
    average_confidence: float
    processing_time_avg: float
