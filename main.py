from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, Form, Header, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import psycopg2
import logging
import json
from typing import List, Optional
from datetime import date,datetime
from typing import Dict
import uuid
import shutil
from typing import List
from pathlib import Path
from passlib.context import CryptContext
import secrets
import string

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]  # Important for file downloads
)

# Database connection
DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://itech_l1q2_user:AoqQkrtzrQW7WEDOJdh0C6hhlY5Xe3sv@dpg-cuvnsbggph6c73ev87g0-a/itech_l1q2")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Pydantic models
class BudgetApproval(BaseModel):
    id: int
    activity_id: int
    activity_name: str
    requested_amount: float
    status: str  # "pending", "approved", "rejected"
    requested_by: str
    approved_by: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class BudgetApprovalCreate(BaseModel):
    activity_id: int
    requested_amount: float
    comments: Optional[str] = None

class BudgetApprovalUpdate(BaseModel):
    status: str
    approved_by: str
    comments: Optional[str] = None

# File storage setup
UPLOAD_DIR = "uploads/fundraising"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

def migrate_database():
    """Handle database schema migrations"""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if donor_name column exists in donations table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='donations' AND column_name='donor_name'
        """)
        if not cursor.fetchone():
            # Add the donor_name column if it doesn't exist
            cursor.execute("""
                ALTER TABLE donations 
                ADD COLUMN donor_name TEXT
            """)
            logger.info("Added donor_name column to donations table")
        
        conn.commit()
    except Exception as e:
        logger.error(f"Error migrating database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Initialize database tables
def init_db():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_approvals (
                id SERIAL PRIMARY KEY,
                activity_id INTEGER REFERENCES activities(id),
                activity_name TEXT NOT NULL,
                requested_amount FLOAT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                requested_by TEXT NOT NULL,
                approved_by TEXT,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Initialize database on startup
try:
    init_db()
    migrate_database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise
            
@app.post("/budget-approvals/", response_model=BudgetApproval)
def create_budget_approval(approval: BudgetApprovalCreate, requested_by: str = Header(...)):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get activity details
        cursor.execute('''
            SELECT a.id, a.name, p.name as project_name 
            FROM activities a
            JOIN projects p ON a.project_id = p.id
            WHERE a.id = %s
        ''', (approval.activity_id,))
        
        activity = cursor.fetchone()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        activity_id, activity_name, project_name = activity
        
        # Create approval request
        cursor.execute('''
            INSERT INTO budget_approvals 
            (activity_id, activity_name, requested_amount, status, requested_by, comments)
            VALUES (%s, %s, %s, 'pending', %s, %s)
            RETURNING id, activity_id, activity_name, requested_amount, status, 
                      requested_by, approved_by, comments, created_at, updated_at
        ''', (
            activity_id,
            f"{activity_name} ({project_name})",
            approval.requested_amount,
            requested_by,
            approval.comments
        ))
        
        new_approval = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_approval[0],
            "activity_id": new_approval[1],
            "activity_name": new_approval[2],
            "requested_amount": new_approval[3],
            "status": new_approval[4],
            "requested_by": new_approval[5],
            "approved_by": new_approval[6],
            "comments": new_approval[7],
            "created_at": new_approval[8],
            "updated_at": new_approval[9]
        }
    except Exception as e:
        logger.error(f"Error creating budget approval: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.put("/budget-approvals/{approval_id}", response_model=BudgetApproval)
def update_budget_approval(approval_id: int, approval: BudgetApprovalUpdate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current approval
        cursor.execute('''
            SELECT id, activity_id, requested_amount, status 
            FROM budget_approvals 
            WHERE id = %s
        ''', (approval_id,))
        
        current_approval = cursor.fetchone()
        if not current_approval:
            raise HTTPException(status_code=404, detail="Approval request not found")
            
        _, activity_id, requested_amount, current_status = current_approval
        
        # Only allow updates if currently pending
        if current_status != 'pending':
            raise HTTPException(status_code=400, detail="Approval request has already been processed")
            
        # Update approval
        cursor.execute('''
            UPDATE budget_approvals
            SET status = %s, approved_by = %s, comments = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, activity_id, activity_name, requested_amount, status, 
                      requested_by, approved_by, comments, created_at, updated_at
        ''', (
            approval.status,
            approval.approved_by,
            approval.comments,
            approval_id
        ))
        
        updated_approval = cursor.fetchone()
        
        # If approved, deduct from program budget
        if approval.status == 'approved':
            # Get the project's program area
            cursor.execute('''
                SELECT p.funding_source, a.budget
                FROM projects p
                JOIN activities a ON a.project_id = p.id
                WHERE a.id = %s
            ''', (activity_id,))
            
            project_info = cursor.fetchone()
            if not project_info:
                raise HTTPException(status_code=404, detail="Project not found for activity")
                
            program_area, activity_budget = project_info
            
            # Verify sufficient funds
            cursor.execute('''
                SELECT balance FROM program_areas WHERE name = %s
            ''', (program_area,))
            
            balance = cursor.fetchone()[0]
            if balance < requested_amount:
                conn.rollback()
                raise HTTPException(status_code=400, detail="Insufficient funds in program area")
                
            # Deduct from program area
            cursor.execute('''
                UPDATE program_areas
                SET balance = balance - %s
                WHERE name = %s
            ''', (requested_amount, program_area))
            
            # Also deduct from main account
            cursor.execute('''
                UPDATE bank_accounts
                SET balance = balance - %s
                WHERE name = 'Main Account'
            ''', (requested_amount,))
            
        conn.commit()
        
        return {
            "id": updated_approval[0],
            "activity_id": updated_approval[1],
            "activity_name": updated_approval[2],
            "requested_amount": updated_approval[3],
            "status": updated_approval[4],
            "requested_by": updated_approval[5],
            "approved_by": updated_approval[6],
            "comments": updated_approval[7],
            "created_at": updated_approval[8],
            "updated_at": updated_approval[9]
        }
    except Exception as e:
        logger.error(f"Error updating budget approval: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/budget-approvals/", response_model=List[BudgetApproval])
def get_budget_approvals(status: Optional[str] = None):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, activity_id, activity_name, requested_amount, status, 
                   requested_by, approved_by, comments, created_at, updated_at
            FROM budget_approvals
        '''
        
        params = []
        if status:
            query += ' WHERE status = %s'
            params.append(status)
            
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        
        approvals = []
        for row in cursor.fetchall():
            approvals.append({
                "id": row[0],
                "activity_id": row[1],
                "activity_name": row[2],
                "requested_amount": row[3],
                "status": row[4],
                "requested_by": row[5],
                "approved_by": row[6],
                "comments": row[7],
                "created_at": row[8],
                "updated_at": row[9]
            })
            
        return approvals
    except Exception as e:
        logger.error(f"Error fetching budget approvals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch approvals")
    finally:
        if conn:
            conn.close()
            
# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
