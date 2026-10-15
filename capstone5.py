from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

app = FastAPI(title="Automated Expense & Invoice Analyzer", version="1.0.0")

# In-memory database mocks
USERS_DB = {"user_1": {"id": "user_1", "username": "alice"}}
EXPENSES_DB = []
REPORTS_DB = {}

# Pydantic Models for Boundary Validation
class ExpenseCreate(BaseModel):
    merchant: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    category: str
    raw_text: Optional[str] = None

# 1. Authentication Dependency (Concept: Authentication)
def get_current_user(user_id: str = "user_1") -> dict:
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
    return user

# 2. Background Task Simulator (Concept: Background Jobs)
def background_llm_parser(expense_id: str, raw_text: str):
    """Simulates async LLM extraction of messy receipt text."""
    # In production, call Gemini/OpenAI API here to clean up merchant names/categories
    for exp in EXPENSES_DB:
        if exp["id"] == expense_id:
            exp["parsed_via_llm"] = True
            exp["notes"] = f"Processed text length: {len(raw_text)}"

# 3. API Endpoints & Database Storage (Concepts: API endpoints, Database)
@app.post("/expenses", status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreate, 
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    expense_id = str(uuid.uuid4())
    expense_record = {
        "id": expense_id,
        "user_id": user["id"],
        "merchant": payload.merchant,
        "amount": payload.amount,
        "category": payload.category,
        "parsed_via_llm": False
    }
    EXPENSES_DB.append(expense_record)

    # Trigger background job if raw text is provided
    if payload.raw_text:
        background_tasks.add_task(background_llm_parser, expense_id, payload.raw_text)

    return {"status": "success", "expense_id": expense_id, "data": expense_record}

@app.get("/expenses", response_model=List[dict])
async def list_expenses(user: dict = Depends(get_current_user)):
    return [exp for exp in EXPENSES_DB if exp["user_id"] == user["id"]]

# 4. Reporting Endpoint (Concept: Reporting / PDF generation)
@app.post("/reports/generate")
async def generate_monthly_report(user: dict = Depends(get_current_user)):
    """Generates a summary report of all user expenses."""
    user_expenses = [exp for exp in EXPENSES_DB if exp["user_id"] == user["id"]]
    total_spent = sum(exp["amount"] for exp in user_expenses)
    
    report_id = str(uuid.uuid4())
    report_data = {
        "report_id": report_id,
        "user_id": user["id"],
        "total_items": len(user_expenses),
        "total_spent": total_spent,
        "status": "Generated (PDF mock)"
    }
    REPORTS_DB[report_id] = report_data
    
    return {"status": "success", "report": report_data}