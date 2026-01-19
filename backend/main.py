from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from models.api import (
    ErrorResponse,
    DocumentUploadResponse,
    DocumentStatusResponse,
    FinancialMetrics,
)
from services.ocr import DocumentProcessor
from services.financial_analysis import FinancialAnalysis
from db.mongodb import MongoDB
from bson import ObjectId
import os
import logging
import traceback
from typing import AsyncGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processor = DocumentProcessor()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Starting up the application")
    try:
        await MongoDB.connect_db()
        logger.info("Successfully connected to MongoDB")
        yield
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e
    finally:
        logger.info("Shutting down the application")
        await MongoDB.close_db()


app = FastAPI(
    title="AI Underwriting Assistant",
    description="AI-powered document processing for commercial real estate underwriting",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal server error",
            "detail": str(exc) if app.debug else None,
        },
    )


@app.post(
    "/api/v1/documents/upload",
    response_model=DocumentUploadResponse,
    responses={500: {"model": ErrorResponse}},
    tags=["Documents"],
    summary="Upload and process a document",
)
async def upload_document(file: UploadFile = File(...)):
    try:
        logger.info(f"Received upload request for file: {file.filename}")

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

        if result["status"] == "success":
            logger.info("Starting financial analysis")
            analysis_result = await FinancialAnalysis.analyze_document(result)
            logger.info("Financial analysis completed")
        else:
            logger.error(f"Document processing failed: {result.get('error', 'Unknown error')}")
            analysis_result = None

        doc = {
            "filename": file.filename,
            "path": file_path,
            "processing_result": result,
            "analysis_result": analysis_result,
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


@app.get(
    "/api/v1/documents/{document_id}/status",
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


@app.get(
    "/api/v1/documents/{document_id}/analysis",
    response_model=FinancialMetrics,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["Documents"],
    summary="Get document financial analysis",
)
async def get_document_analysis(document_id: str):
    try:
        logger.info(f"Retrieving analysis for document: {document_id}")
        doc = await MongoDB.db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        if doc["status"] != "completed":
            logger.error(f"Analysis not completed for document: {document_id}")
            raise HTTPException(status_code=400, detail="Analysis not completed")

        analysis_result = doc.get("analysis_result", {})
        return FinancialMetrics(
            noi=analysis_result.get("noi", 0),
            capRate=analysis_result.get("capRate", 0),
            dscr=analysis_result.get("dscr", 0),
            ltv=analysis_result.get("ltv", 0),
            occupancyRate=analysis_result.get("occupancyRate", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/health",
    tags=["Health"],
    summary="Health check endpoint",
)
async def health_check():
    return {"status": "healthy", "service": "ai-underwriting"}
