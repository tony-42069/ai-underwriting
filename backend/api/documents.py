from fastapi import APIRouter, UploadFile, File
from typing import List
import shutil
import os

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        
        # Save the uploaded file
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": file.filename,
            "status": "success",
            "message": "File uploaded successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }