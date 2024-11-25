import pytesseract
from pdf2image import convert_from_path
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    @staticmethod
    async def process_document(file_path: str) -> dict:
        try:
            logger.info(f"Starting document processing: {file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {
                    "status": "error",
                    "error": "File not found",
                    "processed_at": datetime.now().isoformat()
                }
            
            logger.info("Converting PDF to images...")
            # Convert PDF to images
            images = convert_from_path(
                file_path,
                poppler_path=r"C:\Users\dsade\Documents\poppler-24.08.0\Library\bin"
            )
            
            logger.info(f"Successfully converted PDF to {len(images)} images")
            
            # Extract text from each image
            text_content = []
            for i, img in enumerate(images):
                logger.info(f"Processing page {i+1}/{len(images)}")
                text = pytesseract.image_to_string(img)
                text_content.append(text)
            
            logger.info("Document processing completed successfully")
            return {
                "status": "success",
                "text": "\n".join(text_content),
                "processed_at": datetime.now().isoformat(),
                "pages": len(images)
            }
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }