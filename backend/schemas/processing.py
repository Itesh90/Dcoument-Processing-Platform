from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingStep(str, Enum):
    OCR_EXTRACTION = "ocr_extraction"
    TEXT_CLEANING = "text_cleaning"
    ENTITY_RECOGNITION = "entity_recognition"
    CLASSIFICATION = "classification"
    VALIDATION = "validation"
    POST_PROCESSING = "post_processing"

class ProcessingJobBase(BaseModel):
    document_id: int = Field(..., gt=0, description="ID of the document to process")
    user_id: Optional[int] = Field(None, gt=0, description="ID of the user who initiated processing")
    priority: int = Field(0, ge=0, le=10, description="Processing priority (0-10)")

class ProcessingJobCreate(ProcessingJobBase):
    pass

class ProcessingJobUpdate(BaseModel):
    status: Optional[ProcessingStatus] = Field(None, description="Current processing status")
    processing_steps: Optional[List[str]] = Field(None, description="Completed processing steps")
    current_step: Optional[str] = Field(None, description="Current processing step")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Processing progress (0-100)")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Processing results")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message if failed")
    retry_count: Optional[int] = Field(None, ge=0, description="Number of retry attempts")
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")

    @validator('progress')
    def validate_progress(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Progress must be between 0 and 100')
        return v

class ProcessingJobInDBBase(ProcessingJobBase):
    id: int
    status: str = "pending"
    processing_steps: Optional[List[str]] = None
    current_step: Optional[str] = None
    progress: int = 0
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProcessingJob(ProcessingJobInDBBase):
    document: Optional[Any] = None  # Will be populated by the service
    user: Optional[Any] = None  # Will be populated by the service

class ProcessingJobInDB(ProcessingJobInDBBase):
    pass

class ProcessingJobListResponse(BaseModel):
    jobs: List[ProcessingJob]
    total: int
    page: int
    size: int

class ProcessingResult(BaseModel):
    job_id: int
    document_id: int
    status: ProcessingStatus
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[int] = None
    processing_time: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None

class ProcessingStats(BaseModel):
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    average_processing_time: float
    success_rate: float

class ProcessingQueueStats(BaseModel):
    high_priority: int
    normal_priority: int
    low_priority: int
    estimated_wait_time: int  # in seconds

class ProcessingStepResult(BaseModel):
    step_name: str
    status: str  # success, failed, skipped
    duration: int  # in milliseconds
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ProcessingPipelineResult(BaseModel):
    job_id: int
    document_id: int
    steps: List[ProcessingStepResult]
    overall_status: ProcessingStatus
    final_result: Optional[Dict[str, Any]] = None
    confidence_score: Optional[int] = None
    processing_time: int  # total time in milliseconds
