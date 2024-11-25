from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from services.ocr import OCRService
from services.financial_analysis import FinancialAnalysis
from db.mongodb import MongoDB
from bson import ObjectId
import os
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Underwriting Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("Starting up the application")
    try:
        await MongoDB.connect_db()
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down the application")
    await MongoDB.close_db()

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
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
        
        logger.info("File saved successfully, starting OCR processing")
        
        # Process the document with OCR
        ocr_result = await OCRService.process_document(file_path)
        logger.info(f"OCR processing completed with status: {ocr_result['status']}")
        
        # Perform financial analysis
        if ocr_result["status"] == "success":
            logger.info("Starting financial analysis")
            analysis_result = await FinancialAnalysis.analyze_document(ocr_result)
            logger.info("Financial analysis completed")
        else:
            logger.error(f"OCR processing failed: {ocr_result.get('error', 'Unknown error')}")
            analysis_result = None
        
        # Save to MongoDB
        doc = {
            "filename": file.filename,
            "path": file_path,
            "ocr_result": ocr_result,
            "analysis_result": analysis_result,
            "status": "completed" if analysis_result else "error"
        }
        
        logger.info("Saving results to MongoDB")
        result = await MongoDB.db.documents.insert_one(doc)
        
        return JSONResponse(
            content={
                "status": "success",
                "id": str(result.inserted_id),
                "filename": file.filename,
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

@app.get("/api/documents/{document_id}/status")
async def get_document_status(document_id: str):
    try:
        logger.info(f"Checking status for document: {document_id}")
        doc = await MongoDB.db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        return JSONResponse(content={"status": doc["status"]})
    except Exception as e:
        logger.error(f"Error checking document status: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}/analysis")
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
        
        return JSONResponse(content=doc["analysis_result"])
    except Exception as e:
        logger.error(f"Error retrieving analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))