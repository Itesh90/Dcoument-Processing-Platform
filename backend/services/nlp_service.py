import spacy
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime
from transformers import pipeline
import re
from ..schemas.processing import ProcessingStepResult

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        try:
            # Load English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Spacy model loaded successfully")
        except OSError:
            logger.warning("Spacy model not found. Please install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Initialize transformer pipelines for advanced NLP tasks
        try:
            self.sentiment_analyzer = pipeline("sentiment-analysis")
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            logger.info("Transformer pipelines loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load transformer models: {str(e)}")
            self.sentiment_analyzer = None
            self.summarizer = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "description": spacy.explain(ent.label_),
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": getattr(ent, 'score', 1.0)  # Not available in all models
                })
            
            logger.info(f"Extracted {len(entities)} entities")
            return entities
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            key_phrases = []
            
            # Extract noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.strip()) > 2:  # Filter very short phrases
                    key_phrases.append(chunk.text.strip())
            
            # Extract verb phrases (simplified)
            verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
            key_phrases.extend(verbs)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_phrases = []
            for phrase in key_phrases:
                if phrase.lower() not in seen:
                    seen.add(phrase.lower())
                    unique_phrases.append(phrase)
            
            logger.info(f"Extracted {len(unique_phrases)} key phrases")
            return unique_phrases[:50]  # Limit to 50 phrases
        except Exception as e:
            logger.error(f"Error extracting key phrases: {str(e)}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        if not self.sentiment_analyzer:
            return {"sentiment": "neutral", "confidence": 0.5}
        
        try:
            # For long texts, analyze in chunks
            if len(text) > 512:
                chunks = self._split_text_chunks(text, 512)
                sentiments = []
                for chunk in chunks:
                    result = self.sentiment_analyzer(chunk[:512])  # Limit to model max length
                    sentiments.extend(result)
                
                # Aggregate results
                positive_score = sum(1 for s in sentiments if s['label'] == 'POSITIVE')
                negative_score = len(sentiments) - positive_score
                overall_sentiment = 'POSITIVE' if positive_score > negative_score else 'NEGATIVE'
                avg_confidence = sum(s['score'] for s in sentiments) / len(sentiments)
                
                return {
                    "sentiment": overall_sentiment.lower(),
                    "confidence": avg_confidence,
                    "details": sentiments
                }
            else:
                result = self.sentiment_analyzer(text[:512])
                return {
                    "sentiment": result[0]['label'].lower(),
                    "confidence": result[0]['score'],
                    "details": result
                }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"sentiment": "neutral", "confidence": 0.5}
    
    def summarize_text(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        """Summarize text using transformer model"""
        if not self.summarizer:
            # Fallback to simple extraction
            sentences = text.split('.')
            return '. '.join(sentences[:3]) + '.' if len(sentences) > 3 else text
        
        try:
            # For very long texts, summarize in chunks
            if len(text) > 1024:
                chunks = self._split_text_chunks(text, 1024)
                summaries = []
                for chunk in chunks:
                    if len(chunk.strip()) > min_length:
                        summary = self.summarizer(
                            chunk, 
                            max_length=max_length//len(chunks), 
                            min_length=min_length//len(chunks), 
                            do_sample=False
                        )
                        summaries.append(summary[0]['summary_text'])
                
                return ' '.join(summaries)
            else:
                summary = self.summarizer(
                    text, 
                    max_length=max_length, 
                    min_length=min_length, 
                    do_sample=False
                )
                return summary[0]['summary_text']
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            # Fallback to first few sentences
            sentences = text.split('.')
            return '. '.join(sentences[:3]) + '.' if len(sentences) > 3 else text
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract dates from text"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            dates = []
            
            # Extract date entities
            for ent in doc.ents:
                if ent.label_ in ["DATE", "TIME"]:
                    dates.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })
            
            # Extract dates using regex patterns as backup
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY-MM-DD
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{2,4}\b',  # Month DD, YYYY
                r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{2,4}\b'     # DD Month YYYY
            ]
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Avoid duplicates
                    if not any(d['start'] <= match.start() <= d['end'] for d in dates):
                        dates.append({
                            "text": match.group(),
                            "label": "DATE_REGEX",
                            "start": match.start(),
                            "end": match.end()
                        })
            
            logger.info(f"Extracted {len(dates)} dates")
            return dates
        except Exception as e:
            logger.error(f"Error extracting dates: {str(e)}")
            return []
    
    def extract_monetary_values(self, text: str) -> List[Dict[str, Any]]:
        """Extract monetary values from text"""
        try:
            # Pattern for monetary values
            money_pattern = r'(?:\$|€|£|¥|USD|EUR|GBP|JPY)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY|dollars|euros|pounds|yen)?'
            matches = re.finditer(money_pattern, text, re.IGNORECASE)
            
            monetary_values = []
            for match in matches:
                monetary_values.append({
                    "text": match.group().strip(),
                    "value": self._parse_monetary_value(match.group()),
                    "start": match.start(),
                    "end": match.end()
                })
            
            logger.info(f"Extracted {len(monetary_values)} monetary values")
            return monetary_values
        except Exception as e:
            logger.error(f"Error extracting monetary values: {str(e)}")
            return []
    
    def classify_document(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """Classify document type based on content and entities"""
        try:
            # Analyze entities for classification
            entity_labels = [ent["label"] for ent in entities]
            
            # Check for specific document indicators
            text_lower = text.lower()
            
            # Financial documents
            if ("invoice" in text_lower or "bill" in text_lower or 
                "amount" in text_lower or "total" in text_lower or
                "MONEY" in entity_labels):
                return "financial"
            
            # Legal documents
            elif ("contract" in text_lower or "agreement" in text_lower or
                  "party" in text_lower or "sign" in text_lower or
                  ("ORG" in entity_labels and "PERSON" in entity_labels)):
                return "legal"
            
            # Regulatory documents
            elif ("regulation" in text_lower or "compliance" in text_lower or
                  "section" in text_lower or "article" in text_lower):
                return "regulatory"
            
            # Receipts
            elif ("receipt" in text_lower or "purchase" in text_lower or
                  "item" in text_lower or "quantity" in text_lower):
                return "receipt"
            
            # Default to general
            else:
                return "general"
                
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            return "general"
    
    def analyze_document(self, text: str) -> Dict[str, Any]:
        """Complete NLP analysis of document text"""
        try:
            start_time = self._get_timestamp()
            
            # Extract entities
            entities = self.extract_entities(text)
            
            # Extract key phrases
            key_phrases = self.extract_key_phrases(text)
            
            # Analyze sentiment
            sentiment = self.analyze_sentiment(text)
            
            # Extract dates
            dates = self.extract_dates(text)
            
            # Extract monetary values
            monetary_values = self.extract_monetary_values(text)
            
            # Classify document
            document_type = self.classify_document(text, entities)
            
            # Summarize text (for longer documents)
            summary = ""
            if len(text) > 500:
                summary = self.summarize_text(text)
            
            processing_time = self._get_timestamp() - start_time
            
            result = {
                "entities": entities,
                "key_phrases": key_phrases,
                "sentiment": sentiment,
                "dates": dates,
                "monetary_values": monetary_values,
                "document_type": document_type,
                "summary": summary,
                "processing_steps": ["nlp_analysis"],
                "processing_time_ms": int(processing_time * 1000)
            }
            
            logger.info(f"NLP analysis completed in {int(processing_time * 1000)}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            raise
    
    def _split_text_chunks(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks of maximum length"""
        sentences = text.split('.')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += sentence + '.'
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + '.'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _parse_monetary_value(self, text: str) -> float:
        """Parse monetary value from text"""
        try:
            # Remove currency symbols and commas
            clean_text = re.sub(r'[^\d\.]', '', text)
            return float(clean_text) if clean_text else 0.0
        except:
            return 0.0
    
    def _get_timestamp(self) -> float:
        """Get current timestamp in seconds"""
        import time
        return time.time()
    
    def process_step(self, text: str) -> ProcessingStepResult:
        """
        Process NLP analysis step for pipeline
        """
        try:
            start_time = self._get_timestamp()
            
            result = self.analyze_document(text)
            
            end_time = self._get_timestamp()
            duration_ms = int((end_time - start_time) * 1000)
            
            return ProcessingStepResult(
                step_name="nlp_analysis",
                status="success",
                duration=duration_ms,
                output=result
            )
            
        except Exception as e:
            logger.error(f"NLP processing step failed: {str(e)}")
            return ProcessingStepResult(
                step_name="nlp_analysis",
                status="failed",
                duration=0,
                error=str(e)
            )

# Global instance
nlp_service = NLPService()
