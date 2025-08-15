from typing import Dict, Any, List
from sqlalchemy.orm import Session
import logging
import time
from datetime import datetime
from ..models.document import Document as DocumentModel
from ..models.processing import ProcessingJob as ProcessingJobModel, ProcessingStatus
from ..schemas.processing import ProcessingStepResult, ProcessingPipelineResult
from .ocr_service import ocr_service
from .nlp_service import nlp_service
from ..core.database import get_db_context

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.ocr_service = ocr_service
        self.nlp_service = nlp_service
    
    def process_document(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """Process document through complete pipeline"""
        try:
            processing_steps = []
            result = {}
            start_time = time.time()
            
            # Step 1: OCR Extraction
            logger.info("Starting OCR extraction")
            ocr_result = self.ocr_service.extract_data_from_document(file_path, mime_type)
            processing_steps.extend(ocr_result.get("processing_steps", []))
            result.update(ocr_result)
            
            # Step 2: NLP Analysis
            logger.info("Starting NLP analysis")
            if ocr_result.get("extracted_text"):
                nlp_result = self.nlp_service.analyze_document(ocr_result["extracted_text"])
                processing_steps.extend(nlp_result.get("processing_steps", []))
                result.update(nlp_result)
            
            # Calculate overall confidence (weighted average)
            ocr_confidence = ocr_result.get("confidence", 0)
            nlp_confidence = 80  # Assume good NLP confidence
            result["confidence"] = int(ocr_confidence * 0.7 + nlp_confidence * 0.3)
            
            result["processing_steps"] = processing_steps
            result["status"] = "processed"
            
            total_time = time.time() - start_time
            result["total_processing_time_ms"] = int(total_time * 1000)
            
            logger.info(f"Document processing completed successfully in {int(total_time * 1000)}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "processing_steps": processing_steps,
                "total_processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def process_document_pipeline(self, document_id: int, job_id: int) -> ProcessingPipelineResult:
        """
        Process document through complete pipeline with step tracking
        """
        steps_results: List[ProcessingStepResult] = []
        final_result: Dict[str, Any] = {}
        overall_status = ProcessingStatus.RUNNING
        confidence_score = 0
        total_time = 0
        
        try:
            # Get document from database
            with get_db_context() as db:
                document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                
                job = db.query(ProcessingJobModel).filter(ProcessingJobModel.id == job_id).first()
                if not job:
                    raise ValueError(f"Processing job {job_id} not found")
                
                # Update job status
                job.start_processing()
                db.add(job)
                db.commit()
                
                # Process OCR step
                ocr_step = self.ocr_service.process_step(document.file_path, document.mime_type)
                steps_results.append(ocr_step)
                
                # Update job progress
                job.update_progress(30, "ocr_extraction")
                db.add(job)
                db.commit()
                
                if ocr_step.status == "success" and ocr_step.output:
                    # Process NLP step
                    nlp_step = self.nlp_service.process_step(ocr_step.output.get("extracted_text", ""))
                    steps_results.append(nlp_step)
                    
                    # Update job progress
                    job.update_progress(70, "nlp_analysis")
                    db.add(job)
                    db.commit()
                    
                    if nlp_step.status == "success" and nlp_step.output:
                        # Combine results
                        final_result = {
                            **ocr_step.output,
                            **nlp_step.output
                        }
                        
                        # Calculate confidence
                        ocr_conf = ocr_step.output.get("confidence", 0)
                        confidence_score = int(ocr_conf * 0.7 + 80 * 0.3)  # Weighted average
                        
                        # Update document
                        document.update_processing_result(
                            extracted_data=final_result.get("key_value_pairs", {}),
                            confidence_score=confidence_score,
                            processing_time=ocr_step.duration + nlp_step.duration
                        )
                        db.add(document)
                        
                        overall_status = ProcessingStatus.COMPLETED
                        job.complete_processing(final_result)
                        
                    else:
                        overall_status = ProcessingStatus.FAILED
                        job.fail_processing(nlp_step.error or "NLP processing failed")
                else:
                    overall_status = ProcessingStatus.FAILED
                    job.fail_processing(ocr_step.error or "OCR processing failed")
                
                # Update job completion
                job.updated_at = datetime.utcnow()
                db.add(job)
                db.commit()
                
                # Calculate total processing time
                total_time = sum(step.duration for step in steps_results)
                
                return ProcessingPipelineResult(
                    job_id=job_id,
                    document_id=document_id,
                    steps=steps_results,
                    overall_status=overall_status,
                    final_result=final_result if overall_status == ProcessingStatus.COMPLETED else None,
                    confidence_score=confidence_score if overall_status == ProcessingStatus.COMPLETED else None,
                    processing_time=total_time
                )
                
        except Exception as e:
            logger.error(f"Error in document processing pipeline: {str(e)}")
            
            # Update job status to failed
            try:
                with get_db_context() as db:
                    job = db.query(ProcessingJobModel).filter(ProcessingJobModel.id == job_id).first()
                    if job:
                        job.fail_processing(str(e))
                        job.updated_at = datetime.utcnow()
                        db.add(job)
                        db.commit()
            except Exception as db_error:
                logger.error(f"Error updating job status: {str(db_error)}")
            
            return ProcessingPipelineResult(
                job_id=job_id,
                document_id=document_id,
                steps=steps_results,
                overall_status=ProcessingStatus.FAILED,
                error=str(e),
                processing_time=total_time
            )
    
    def retry_failed_job(self, job_id: int) -> ProcessingPipelineResult:
        """
        Retry a failed processing job
        """
        try:
            with get_db_context() as db:
                job = db.query(ProcessingJobModel).filter(ProcessingJobModel.id == job_id).first()
                if not job:
                    raise ValueError(f"Processing job {job_id} not found")
                
                if not job.can_retry():
                    raise ValueError("Job cannot be retried")
                
                job.retry_count += 1
                db.add(job)
                db.commit()
                
                return self.process_document_pipeline(job.document_id, job_id)
                
        except Exception as e:
            logger.error(f"Error retrying job {job_id}: {str(e)}")
            raise

# Global instance
document_processor = DocumentProcessor()
