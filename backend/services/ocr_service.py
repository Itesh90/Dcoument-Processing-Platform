import pytesseract
from PIL import Image
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple
import logging
from pdf2image import convert_from_path
import os
import tempfile
from ..schemas.processing import ProcessingStepResult

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        # Configure Tesseract path if needed (for Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def preprocess_image(self, image_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Preprocess image for better OCR results
        Returns processed image and preprocessing steps info
        """
        try:
            steps_info = {
                "original_size": None,
                "final_size": None,
                "operations_applied": []
            }
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            steps_info["original_size"] = image.shape[:2]  # (height, width)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            steps_info["operations_applied"].append("grayscale_conversion")
            
            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 5)
            steps_info["operations_applied"].append("noise_reduction")
            
            # Apply adaptive threshold to get binary image
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            steps_info["operations_applied"].append("adaptive_thresholding")
            
            # Optional: Morphological operations to remove small noise
            kernel = np.ones((1, 1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            steps_info["operations_applied"].append("morphological_closing")
            
            steps_info["final_size"] = binary.shape[:2]
            
            return binary, steps_info
            
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {str(e)}")
            raise
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image using Tesseract OCR
        """
        try:
            # Preprocess image
            processed_image, preprocessing_info = self.preprocess_image(image_path)
            
            # Convert to PIL Image for pytesseract
            pil_image = Image.fromarray(processed_image)
            
            # Configure Tesseract with custom parameters for better accuracy
            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            
            # Extract text
            text = pytesseract.image_to_string(pil_image, config=custom_config)
            
            # Get detailed data including confidence scores and bounding boxes
            data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT, config=custom_config)
            
            # Get bounding boxes for words
            boxes = pytesseract.image_to_boxes(pil_image, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) // len(confidences) if confidences else 0
            
            # Extract word-level information
            words = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 30:  # Filter low confidence words
                    words.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    })
            
            result = {
                "text": text.strip(),
                "confidence": avg_confidence,
                "words": words,
                "preprocessing_info": preprocessing_info,
                "raw_data": {
                    "data": data,
                    "boxes": boxes
                }
            }
            
            logger.info(f"OCR extraction completed with {avg_confidence}% confidence")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from image {image_path}: {str(e)}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF by converting to images first
        """
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=200, fmt='jpeg')
            
            all_text = []
            all_words = []
            total_confidence = 0
            page_count = len(images)
            
            for i, image in enumerate(images):
                # Save temporary image
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    image.save(tmp_file.name, 'JPEG')
                    temp_path = tmp_file.name
                
                try:
                    # Extract text from page
                    page_result = self.extract_text_from_image(temp_path)
                    all_text.append(page_result["text"])
                    all_words.extend(page_result["words"])
                    total_confidence += page_result["confidence"]
                    
                    # Clean up temporary file
                    os.unlink(temp_path)
                except Exception as e:
                    logger.error(f"Error processing page {i+1} of PDF: {str(e)}")
                    # Clean up temporary file even on error
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    continue
            
            avg_confidence = total_confidence // page_count if page_count > 0 else 0
            
            result = {
                "text": "\n\n".join(all_text),
                "confidence": avg_confidence,
                "words": all_words,
                "page_count": page_count,
                "pages_processed": len(all_text)
            }
            
            logger.info(f"PDF OCR extraction completed with {avg_confidence}% average confidence")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            raise
    
    def extract_data_from_document(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Extract structured data from document based on file type
        """
        try:
            start_time = self._get_timestamp()
            
            # Determine file type and process accordingly
            if mime_type == "application/pdf":
                ocr_result = self.extract_text_from_pdf(file_path)
            elif mime_type.startswith("image/"):
                ocr_result = self.extract_text_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {mime_type}")
            
            # Simple key-value extraction (can be enhanced with NLP)
            lines = ocr_result["text"].split('\n')
            key_value_pairs = {}
            
            for line in lines:
                if ':' in line and len(line.strip()) > 3:
                    parts = line.split(':', 1)
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key and value:
                        key_value_pairs[key] = value
            
            processing_time = self._get_timestamp() - start_time
            
            result = {
                "extracted_text": ocr_result["text"],
                "key_value_pairs": key_value_pairs,
                "confidence": ocr_result["confidence"],
                "words": ocr_result.get("words", []),
                "processing_steps": ["ocr_extraction"],
                "processing_time_ms": int(processing_time * 1000),
                "metadata": {
                    "page_count": ocr_result.get("page_count", 1),
                    "pages_processed": ocr_result.get("pages_processed", 1)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting document data from {file_path}: {str(e)}")
            raise
    
    def _get_timestamp(self) -> float:
        """Get current timestamp in seconds"""
        import time
        return time.time()
    
    def process_step(self, file_path: str, mime_type: str) -> ProcessingStepResult:
        """
        Process OCR extraction step for pipeline
        """
        try:
            start_time = self._get_timestamp()
            
            result = self.extract_data_from_document(file_path, mime_type)
            
            end_time = self._get_timestamp()
            duration_ms = int((end_time - start_time) * 1000)
            
            return ProcessingStepResult(
                step_name="ocr_extraction",
                status="success",
                duration=duration_ms,
                output=result
            )
            
        except Exception as e:
            logger.error(f"OCR processing step failed: {str(e)}")
            return ProcessingStepResult(
                step_name="ocr_extraction",
                status="failed",
                duration=0,
                error=str(e)
            )

# Global instance
ocr_service = OCRService()
