from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from models.api import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    DocumentContentResponse,
    SpecificExtractionResponse,
    SupportedTypesResponse,
    ErrorResponse,
)
from services.ocr import DocumentProcessor
from db.mongodb import MongoDB
from bson import ObjectId
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
processor = DocumentProcessor()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    responses={500: {"model": ErrorResponse}},
    tags=["Documents"],
    summary="Upload and process a document",
)
async def upload_document(file: UploadFile = File(...)):
    try:
        logger.info(f"Received upload request for file: {file.filename}")

        import os
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        file_path = os.path.join(uploads_dir, file.filename)
        logger.info(f"Saving file to: {file_path}")

        try:
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save file")

        logger.info("File saved successfully, starting document processing")

        result = await processor.process_document(file_path)
        logger.info(f"Document processing completed with status: {result['status']}")

        doc = {
            "filename": file.filename,
            "path": file_path,
            "processing_result": result,
            "status": "completed" if result["status"] == "success" else "error",
        }

        logger.info("Saving results to MongoDB")
        db_result = await MongoDB.db.documents.insert_one(doc)

        extractions = None
        if result.get("extractions"):
            extractions = [
                {"type": ext["extractor"], "confidence": ext["confidence"]["overall"]}
                for ext in result["extractions"]
            ]

        return DocumentUploadResponse(
            status="success",
            id=str(db_result.inserted_id),
            filename=file.filename,
            extractions=extractions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["Documents"],
    summary="Get document processing status",
)
async def get_document_status(document_id: str):
    try:
        logger.info(f"Checking status for document: {document_id}")
        doc = await MongoDB.db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        extractions = None
        if doc.get("processing_result", {}).get("extractions"):
            extractions = [
                {"type": ext["extractor"], "confidence": ext["confidence"]["overall"]}
                for ext in doc["processing_result"]["extractions"]
            ]

        return DocumentStatusResponse(
            status=doc["status"],
            extractions=extractions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking document status: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{document_id}/content",
    response_model=DocumentContentResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["Documents"],
    summary="Get extracted document content",
)
async def get_document_content(document_id: str):
    try:
        logger.info(f"Retrieving content for document: {document_id}")
        doc = await MongoDB.db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        if doc["status"] != "completed":
            logger.error(f"Processing not completed for document: {document_id}")
            raise HTTPException(status_code=400, detail="Processing not completed")

        processing_result = doc.get("processing_result", {})
        extractions = processing_result.get("extractions", [])

        extraction_results = []
        for ext in extractions:
            extraction_results.append(
                SpecificExtractionResponse(
                    extractor=ext["extractor"],
                    data=ext["data"],
                    confidence=ext["confidence"],
                    validation_errors=ext.get("validation_errors"),
                )
            )

        return DocumentContentResponse(
            text=processing_result.get("text", ""),
            extractions=extraction_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document content: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{document_id}/extraction/{extractor_type}",
    response_model=SpecificExtractionResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["Documents"],
    summary="Get specific type of extraction results",
)
async def get_specific_extraction(document_id: str, extractor_type: str):
    try:
        logger.info(f"Retrieving {extractor_type} extraction for document: {document_id}")
        doc = await MongoDB.db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        if doc["status"] != "completed":
            logger.error(f"Processing not completed for document: {document_id}")
            raise HTTPException(status_code=400, detail="Processing not completed")

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

        return SpecificExtractionResponse(
            extractor=extraction["extractor"],
            data=extraction["data"],
            confidence=extraction["confidence"],
            validation_errors=extraction.get("validation_errors"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving extraction: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/types",
    response_model=SupportedTypesResponse,
    tags=["Documents"],
    summary="Get list of supported document types",
)
async def get_supported_types():
    return SupportedTypesResponse(
        supported_types=[
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
    )
