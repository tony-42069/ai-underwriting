"""
Enhanced document processing API with specialized extractors.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.ocr import DocumentProcessor
from db.mongodb import MongoDB
from bson import ObjectId
import os
import logging
import traceback
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
processor = DocumentProcessor()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    try:
        logger.info(f"Received upload request for file: {file.filename}")
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save the uploaded file
        file_path = os.path.join(uploads_dir, file.filename)
        logger.info(f"Saving file to: {file_path}")
        
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "error": "Failed to save file"}
            )
        
        logger.info("File saved successfully, starting document processing")
        
        # Process the document
        result = await processor.process_document(file_path)
        logger.info(f"Document processing completed with status: {result['status']}")
        
        # Save to MongoDB
        doc = {
            "filename": file.filename,
            "path": file_path,
            "processing_result": result,
            "status": "completed" if result["status"] == "success" else "error"
        }
        
        logger.info("Saving results to MongoDB")
        db_result = await MongoDB.db.documents.insert_one(doc)
        
        return JSONResponse(
            content={
                "status": "success",
                "id": str(db_result.inserted_id),
                "filename": file.filename,
                "extractions": [
                    {
                        "type": ext["extractor"],
                        "confidence": ext["confidence"]["overall"]
                    }
                    for ext in result.get("extractions", [])
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )

@router.get("/{document_id}/status")
async def get_document_status(document_id: str):
    """Get document processing status."""
    try:
        logger.info(f"Checking status for document: {document_id}")
        doc = await MongoDB.db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        return JSONResponse(content={
            "status": doc["status"],
            "extractions": [
                {
                    "type": ext["extractor"],
                    "confidence": ext["confidence"]["overall"]
                }
                for ext in doc.get("processing_result", {}).get("extractions", [])
            ]
        })
    except Exception as e:
        logger.error(f"Error checking document status: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/content")
async def get_document_content(document_id: str):
    """Get extracted document content."""
    try:
        logger.info(f"Retrieving content for document: {document_id}")
        doc = await MongoDB.db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        if doc["status"] != "completed":
            logger.error(f"Processing not completed for document: {document_id}")
            raise HTTPException(status_code=400, detail="Processing not completed")
        
        return JSONResponse(content={
            "text": doc["processing_result"]["text"],
            "extractions": doc["processing_result"]["extractions"]
        })
    except Exception as e:
        logger.error(f"Error retrieving document content: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/extraction/{extractor_type}")
async def get_specific_extraction(document_id: str, extractor_type: str):
    """Get specific type of extraction results."""
    try:
        logger.info(f"Retrieving {extractor_type} extraction for document: {document_id}")
        doc = await MongoDB.db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        if doc["status"] != "completed":
            logger.error(f"Processing not completed for document: {document_id}")
            raise HTTPException(status_code=400, detail="Processing not completed")
        
        # Find the specific extraction
        extraction = next(
            (ext for ext in doc["processing_result"]["extractions"]
             if ext["extractor"].lower() == extractor_type.lower()),
            None
        )
        
        if not extraction:
            raise HTTPException(
                status_code=404,
                detail=f"No {extractor_type} extraction found"
            )
        
        return JSONResponse(content=extraction)
    except Exception as e:
        logger.error(f"Error retrieving extraction: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_supported_types():
    """Get list of supported document types."""
    return JSONResponse(content={
        "supported_types": [
            {
                "name": "Rent Roll",
                "extractor": "RentRollExtractor",
                "description": "Tenant and lease information from rent rolls"
            },
            {
                "name": "P&L Statement",
                "extractor": "PLStatementExtractor",
                "description": "Financial data from profit and loss statements"
            },
            {
                "name": "Operating Statement",
                "extractor": "OperatingStatementExtractor",
                "description": "Combined financial and occupancy data from operating statements"
            },
            {
                "name": "Lease",
                "extractor": "LeaseExtractor",
                "description": "Detailed lease terms and conditions"
            }
        ]
    })
