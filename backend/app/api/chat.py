from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.services.text_to_sql import process_chat_query

router = APIRouter(
    prefix="/ai",
    tags=["AI Text-to-SQL Chat"]
)

class ChatRequest(BaseModel):
    message: str = Field(..., description="Natural language question about business/financial data", example="What is the total revenue?")
    dataset_id: Optional[int] = Field(None, description="Optional dataset ID to filter queries", example=1)

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the total revenue?",
                "dataset_id": 1
            }
        }

class ChatResponse(BaseModel):
    question: str
    sql: str
    result: List[Dict[str, Any]]
    answer: str

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Text-to-SQL AI Chatbot",
    description="Ask natural-language questions about uploaded financial datasets. Translates text to safe SQL, executes it, and returns natural language answers."
)
def chat_endpoint(payload: ChatRequest):
    message = payload.message.strip() if payload.message else ""
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'message' field cannot be empty."
        )

    db: Session = SessionLocal()
    try:
        response_data = process_chat_query(
            db=db,
            question=message,
            dataset_id=payload.dataset_id
        )
        return response_data
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except RuntimeError as run_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution error: {str(run_err)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred processing your query: {str(e)}"
        )
    finally:
        db.close()
