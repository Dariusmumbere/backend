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


class Folder(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None

class FileItem(BaseModel):
    id: str
    name: str
    type: str
    size: int
    folder_id: Optional[str] = None

class FolderContents(BaseModel):
    folders: List[Folder]
    files: List[FileItem]

class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None

class DonorStats(BaseModel):
    donation_count: int
    total_donated: float
    first_donation: Optional[date] = None
    last_donation: Optional[date] = None
    
class DonorCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    donor_type: Optional[str] = None
    notes: Optional[str] = None
    category: Optional[str] = "one-time"
    
class Donation(BaseModel):
    donor_name: str
    amount: float
    payment_method: str
    date: date
    project: Optional[str] = None
    notes: Optional[str] = None
    status: str = "pending"  # "pending", "completed"

class Donor(BaseModel):
    id: Optional[int] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    donor_type: Optional[str] = None
    notes: Optional[str] = None
    category: Optional[str] = "one-time"
    created_at: Optional[datetime] = None
    stats: Optional[DonorStats] = None

class DonationCreate(BaseModel):
    donor_name: str
    amount: float
    payment_method: str
    date: date
    project: Optional[str] = None
    notes: Optional[str] = None

class Donation(DonationCreate):
    id: int
    status: str
    created_at: datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: str
    end_date: str
    budget: float
    funding_source: str
    status: str = "planned"

class Project(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    start_date: str
    end_date: str
    budget: float
    funding_source: str
    status: str
    created_at: datetime
    
class ActivityCreate(BaseModel):
    name: str
    project_id: int
    description: Optional[str] = None
    start_date: str
    end_date: str
    budget: float
    status: str = "planned"

class Activity(BaseModel):
    id: int
    name: str
    project_id: int
    project_name: str
    description: Optional[str] = None
    start_date: str
    end_date: str
    budget: float
    status: str
    created_at: datetime

class BudgetItemCreate(BaseModel):
    project_id: int
    item_name: str
    description: Optional[str] = None
    quantity: float
    unit_price: float
    category: str

class BudgetItem(BudgetItemCreate):
    id: int
    total: float
    created_at: datetime
    
class EmployeeCreate(BaseModel):
    name: str
    nin: str
    dob: str
    qualification: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "active"

class Employee(EmployeeCreate):
    id: int
    created_at: datetime

class DeploymentCreate(BaseModel):
    employee_id: int
    activity_id: int
    role: str

class Deployment(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    activity_id: int
    activity_name: str
    project_name: str
    role: str
    created_at: datetime
class WorkOpportunityCreate(BaseModel):
    title: str
    description: str
    status: str = "open"

class WorkOpportunity(WorkOpportunityCreate):
    id: int
    created_at: datetime

class OpportunityAssignmentCreate(BaseModel):
    opportunity_id: int
    employee_id: int

class OpportunityAssignment(OpportunityAssignmentCreate):
    id: int
    employee_name: str
    opportunity_title: str
    created_at: datetime
class PaymentRequest(BaseModel):
    employee_id: int
    amount: float
    payment_period: str  # e.g., "2023-10"
    description: Optional[str] = None
    payment_method: str = "bank_transfer"  # or "mobile_money", "cash"

class PaymentApproval(BaseModel):
    payment_id: int
    approved: bool
    remarks: Optional[str] = None

class PaymentRequest(BaseModel):
    employee_id: int
    amount: float
    payment_period: str  # Format: YYYY-MM
    description: Optional[str] = None
    payment_method: str = "bank_transfer"  # or "mobile_money", "cash"

class PaymentApproval(BaseModel):
    payment_id: int
    approved: bool
    remarks: Optional[str] = None

class Payment(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    amount: float
    payment_period: str
    description: Optional[str]
    payment_method: str
    status: str  # pending, approved, rejected
    remarks: Optional[str]
    created_at: datetime
    approved_at: Optional[datetime]
    processed_by: Optional[int]
    
class ReportCreate(BaseModel):
    employee_id: int
    activity_id: int
    title: str
    content: str

class Report(ReportCreate):
    id: int
    created_at: datetime
    status: str = "submitted"
    submitted_by: Optional[int] = None
    approved_by: Optional[int] = None

class BudgetItemCreate(BaseModel):
    item_name: str 
    description: Optional[str] = None  # Changed from str to None as default
    quantity: float
    unit_price: float 
    category: str 
    project_id: Optional[int] = None  # Make this optional
    
class ProgramArea(BaseModel):
    id: int
    name: str
    budget: float
    balance: float

class BankAccount(BaseModel):
    id: int
    name: str
    account_number: str
    balance: float
class ActivityApprovalRequest(BaseModel):
    activity_id: int
    requested_by: str
    requested_amount: float
    comments: Optional[str] = None

class ActivityApproval(BaseModel):
    id: int
    activity_id: int
    activity_name: str
    requested_by: str
    requested_amount: float
    comments: Optional[str]
    status: str  # pending, approved, rejected
    created_at: datetime
    approved_at: Optional[datetime]
    approved_by: Optional[str]
    response_comments: Optional[str] 
    budget_items: List[BudgetItem] = []

class ApprovalDecision(BaseModel):
    decision: str
    approved_by: str
    response_comments: Optional[str] = None

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

def migrate_database():
    """Handle database schema migrations"""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create activity_approvals table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_approvals (
                id SERIAL PRIMARY KEY,
                activity_id INTEGER NOT NULL REFERENCES activities(id),
                activity_name TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                requested_amount FLOAT NOT NULL,
                comments TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                approved_by TEXT,
                response_comments TEXT
            )
        ''')
        
        # Add status column to activities if it doesn't exist
        cursor.execute("""
            DO $$
            BEGIN
                BEGIN
                    ALTER TABLE activities ADD COLUMN status TEXT DEFAULT 'pending';
                EXCEPTION
                    WHEN duplicate_column THEN 
                    RAISE NOTICE 'column status already exists in activities';
                END;
            END $$;
        """)
        
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
            CREATE TABLE IF NOT EXISTS donors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                donor_type TEXT,
                notes TEXT,
                category TEXT DEFAULT 'one-time',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("""
            DO $$
            BEGIN
                BEGIN
                    ALTER TABLE donors ADD COLUMN category TEXT DEFAULT 'one-time';
                EXCEPTION
                    WHEN duplicate_column THEN 
                    RAISE NOTICE 'column category already exists in donors';
                END;
            END $$;
        """)
       
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folders (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                parent_id TEXT REFERENCES folders(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                id SERIAL PRIMARY KEY,
                donor_id INTEGER REFERENCES donors(id) ON DELETE SET NULL,  
                donor_name TEXT, 
                amount FLOAT NOT NULL,
                payment_method TEXT NOT NULL,
                date DATE NOT NULL,
                project TEXT,
                notes TEXT,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                size INTEGER NOT NULL,
                folder_id TEXT REFERENCES folders(id) ON DELETE CASCADE,
                path TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                budget REAL NOT NULL,
                funding_source TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                project_id INTEGER REFERENCES projects(id),
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                budget REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
             )
         ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_items (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
                item_name TEXT NOT NULL,
                description TEXT,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                total REAL GENERATED ALWAYS AS (quantity * unit_price) STORED,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                nin TEXT NOT NULL UNIQUE,
                dob DATE NOT NULL,
                qualification TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployments (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_opportunities (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunity_assignments (
                id SERIAL PRIMARY KEY,
                opportunity_id INTEGER NOT NULL REFERENCES work_opportunities(id) ON DELETE CASCADE,
                employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                amount DECIMAL(12, 2) NOT NULL,
                payment_period VARCHAR(7) NOT NULL,  -- Format: YYYY-MM
                description TEXT,
                payment_method VARCHAR(20) NOT NULL,
                status VARCHAR(10) NOT NULL DEFAULT 'pending',  -- pending, approved, rejected
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                processed_by INTEGER REFERENCES employees(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(id),
                activity_id INTEGER REFERENCES activities(id),
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'submitted',
                submitted_by INTEGER REFERENCES employees(id),
                approved_by INTEGER REFERENCES employees(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
      

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_attachments (
                id SERIAL PRIMARY KEY,
                report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_attachments (
                id SERIAL PRIMARY KEY,
                report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS program_areas (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                budget FLOAT DEFAULT 0,
                balance FLOAT DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                account_number TEXT NOT NULL,
                balance FLOAT DEFAULT 0
            )
        ''')
        
        program_areas = [
            ("Main Account", 0),
            ("Women Empowerment", 0),
            ("Vocational Education", 0),
            ("Climate Change", 0),
            ("Reproductive Health", 0)
        ]
        
        for name, budget in program_areas:
            cursor.execute('''
                INSERT INTO program_areas (name, budget)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
            ''', (name, budget))
        
        # Insert main bank account if it doesn't exist
        cursor.execute('''
            INSERT INTO bank_accounts (name, account_number, balance)
            VALUES ('Main Account', '****5580', 0)
            ON CONFLICT (name) DO NOTHING
        ''')
       


        cursor.execute('SELECT id FROM folders WHERE id = %s', ('root',))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO folders (id, name) VALUES (%s, %s)', ('root', 'Fundraising Documents'))
        
        # Initialize the balance to 0 if the table is empty
        cursor.execute('SELECT COUNT(*) FROM bank_account')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO bank_account (balance) VALUES (0)')
            
        conn.commit()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Initialize database
init_db()
migrate_database()
            

@app.post("/folders/", response_model=Folder)
def create_folder(folder_data: FolderCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        folder_id = str(uuid.uuid4())
        
        if folder_data.parent_id:
            # Check if parent folder exists
            cursor.execute('SELECT id FROM folders WHERE id = %s', (folder_data.parent_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Parent folder not found")
            
            cursor.execute('''
                INSERT INTO folders (id, name, parent_id)
                VALUES (%s, %s, %s)
                RETURNING id, name, parent_id
            ''', (folder_id, folder_data.name, folder_data.parent_id))
        else:
            cursor.execute('''
                INSERT INTO folders (id, name)
                VALUES (%s, %s)
                RETURNING id, name, parent_id
            ''', (folder_id, folder_data.name))
        
        folder = cursor.fetchone()
        conn.commit()
        return {"id": folder[0], "name": folder[1], "parent_id": folder[2]}
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
            
@app.get("/folders/{folder_id}/contents", response_model=FolderContents)
def get_folder_contents(folder_id: str = "root"):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get subfolders
        if folder_id == "root":
            cursor.execute('SELECT id, name, parent_id FROM folders WHERE parent_id IS NULL')
        else:
            cursor.execute('SELECT id, name, parent_id FROM folders WHERE parent_id = %s', (folder_id,))
            
        folders = [
            {"id": row[0], "name": row[1], "parent_id": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Get files
        if folder_id == "root":
            cursor.execute('SELECT id, name, type, size FROM files WHERE folder_id IS NULL')
        else:
            cursor.execute('SELECT id, name, type, size FROM files WHERE folder_id = %s', (folder_id,))
            
        files = [
            {"id": row[0], "name": row[1], "type": row[2], "size": row[3]}
            for row in cursor.fetchall()
        ]
        
        return {"folders": folders, "files": files}
    except Exception as e:
        logger.error(f"Error getting folder contents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get folder contents")
    finally:
        if conn:
            conn.close()
            
@app.post("/upload/")
def upload_files(
    files: List[UploadFile] = File(...),
    folder_id: str = Form(None)
):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        uploaded_files = []
        
        for file in files:
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix
            file_path = Path(UPLOAD_DIR) / f"{file_id}{file_ext}"
            
            # Save file synchronously
            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())
            
            file_size = file_path.stat().st_size
            
            cursor.execute('''
                INSERT INTO files (id, name, type, size, folder_id, path)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                file_id,
                file.filename,
                file.content_type,
                file_size,
                folder_id,
                str(file_path)
            ))
            
            uploaded_files.append({
                "id": file_id,
                "name": file.filename,
                "type": file.content_type,
                "size": file_size
            })
        
        conn.commit()
        return {"uploadedFiles": uploaded_files}
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to upload files")
    finally:
        if conn:
            conn.close()
            
@app.get("/files/{file_id}/download")
def download_file(file_id: str):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, path FROM files WHERE id = %s', (file_id,))
        file_data = cursor.fetchone()
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_name, file_path = file_data
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on server")
        
        return FileResponse(
            file_path,
            filename=file_name,
            media_type='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")
    finally:
        if conn:
            conn.close()

@app.put("/folders/{folder_id}")
def rename_folder(folder_id: str, name: str = Form(...)):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE folders
            SET name = %s
            WHERE id = %s
            RETURNING id, name, parent_id
        ''', (name, folder_id))
        
        updated_folder = cursor.fetchone()
        if not updated_folder:
            raise HTTPException(status_code=404, detail="Folder not found")
            
        conn.commit()
        return {"id": updated_folder[0], "name": updated_folder[1], "parent_id": updated_folder[2]}
    except Exception as e:
        logger.error(f"Error renaming folder: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to rename folder")
    finally:
        if conn:
            conn.close()

@app.delete("/folders/{folder_id}")
def delete_folder(folder_id: str):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if folder exists
        cursor.execute('SELECT id FROM folders WHERE id = %s', (folder_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Folder not found")
            
        # Delete folder (cascade will handle files)
        cursor.execute('DELETE FROM folders WHERE id = %s', (folder_id,))
        conn.commit()
        return {"message": "Folder deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting folder: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete folder")
    finally:
        if conn:
            conn.close()

@app.put("/files/{file_id}")
def rename_file(file_id: str, name: str = Form(...)):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE files
            SET name = %s
            WHERE id = %s
            RETURNING id, name, type, size, folder_id
        ''', (name, file_id))
        
        updated_file = cursor.fetchone()
        if not updated_file:
            raise HTTPException(status_code=404, detail="File not found")
            
        conn.commit()
        return {
            "id": updated_file[0],
            "name": updated_file[1],
            "type": updated_file[2],
            "size": updated_file[3],
            "folder_id": updated_file[4]
        }
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to rename file")
    finally:
        if conn:
            conn.close()

@app.delete("/files/{file_id}")
def delete_file(file_id: str):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get file path before deleting
        cursor.execute('SELECT path FROM files WHERE id = %s', (file_id,))
        file_data = cursor.fetchone()
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
            
        # Delete from database
        cursor.execute('DELETE FROM files WHERE id = %s', (file_id,))
        
        # Delete physical file
        file_path = Path(file_data[0])
        if file_path.exists():
            file_path.unlink()
            
        conn.commit()
        return {"message": "File deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete file")
    finally:
        if conn:
            conn.close()

@app.get("/files/{file_id}/preview")
def preview_file(file_id: str):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, path, type FROM files WHERE id = %s', (file_id,))
        file_data = cursor.fetchone()
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_name, file_path, file_type = file_data
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on server")
        
        # For images and PDFs, return the file directly
        if file_type in ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']:
            return FileResponse(
                file_path,
                filename=file_name,
                media_type=file_type
            )
        else:
            # For other types, return a download response
            return FileResponse(
                file_path,
                filename=file_name,
                media_type='application/octet-stream'
            )
    except Exception as e:
        logger.error(f"Error previewing file: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview file")
    finally:
        if conn:
            conn.close()

@app.post("/donations/", response_model=Donation)
def create_donation(donation: DonationCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Insert donation
        cursor.execute('''
            INSERT INTO donations (donor_name, amount, payment_method, date, project, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'completed')
            RETURNING id, donor_name, amount, payment_method, date, project, notes, status, created_at
        ''', (
            donation.donor_name,
            donation.amount,
            donation.payment_method,
            donation.date,
            donation.project,
            donation.notes
        ))
        
        new_donation = cursor.fetchone()
        
        # Update the appropriate program area balance if project is specified
        if donation.project:
            cursor.execute('''
                UPDATE program_areas
                SET balance = balance + %s
                WHERE name = %s
                RETURNING balance
            ''', (donation.amount, donation.project))
            
            # Verify the program area was updated
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Program area '{donation.project}' not found")
        
        # Update main account balance
        cursor.execute('''
            UPDATE bank_accounts
            SET balance = balance + %s
            WHERE name = 'Main Account'
            RETURNING balance
        ''', (donation.amount,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=500, detail="Main account not found")
        
        conn.commit()
        
        return {
            "id": new_donation[0],
            "donor_name": new_donation[1],
            "amount": new_donation[2],
            "payment_method": new_donation[3],
            "date": new_donation[4],
            "project": new_donation[5],
            "notes": new_donation[6],
            "status": new_donation[7],
            "created_at": new_donation[8]
        }
    except Exception as e:
        logger.error(f"Error creating donation: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
            
            
@app.get("/donations/", response_model=List[Donation])
def get_donations():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.id, 
                   COALESCE(d.donor_name, dn.name) as donor_name, 
                   d.amount, d.payment_method, 
                   d.date, d.project, d.notes, 
                   d.status, d.created_at
            FROM donations d
            LEFT JOIN donors dn ON d.donor_id = dn.id
            ORDER BY date DESC
        ''')
        
        donations = []
        for row in cursor.fetchall():
            donations.append({
                "id": row[0],
                "donor_name": row[1],
                "amount": row[2],
                "payment_method": row[3],
                "date": row[4],
                "project": row[5],
                "notes": row[6],
                "status": row[7],
                "created_at": row[8]
            })
            
        return donations
    except Exception as e:
        logger.error(f"Error fetching donations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch donations")
    finally:
        if conn:
            conn.close()
            
@app.get("/program-areas/", response_model=List[ProgramArea])
def get_program_areas():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, budget, balance
            FROM program_areas
            ORDER BY name
        ''')
        
        program_areas = []
        for row in cursor.fetchall():
            program_areas.append({
                "id": row[0],
                "name": row[1],
                "budget": row[2],
                "balance": row[3]
            })
            
        return program_areas
    except Exception as e:
        logger.error(f"Error fetching program areas: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch program areas")
    finally:
        if conn:
            conn.close()

@app.get("/bank-accounts/", response_model=List[BankAccount])
def get_bank_accounts():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, account_number, balance
            FROM bank_accounts
            ORDER BY name
        ''')
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                "id": row[0],
                "name": row[1],
                "account_number": row[2],
                "balance": row[3]
            })
            
        return accounts
    except Exception as e:
        logger.error(f"Error fetching bank accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bank accounts")
    finally:
        if conn:
            conn.close()

@app.get("/dashboard-summary/")
def get_dashboard_summary():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total donations
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM donations WHERE status = %s', ('completed',))
        total_donations = cursor.fetchone()[0]
        
        # Get program area balances
        cursor.execute('SELECT name, balance FROM program_areas')
        program_balances = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get main account balance
        cursor.execute('SELECT balance FROM bank_accounts WHERE name = %s', ('Main Account',))
        main_balance = cursor.fetchone()[0]
        
        return {
            "total_donations": total_donations,
            "program_balances": program_balances,
            "main_account_balance": main_balance
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard summary")
    finally:
        if conn:
            conn.close()
            
@app.delete("/donations/{donation_id}")
def delete_donation(donation_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # First get the donation details to check if it exists and get amount/project
        cursor.execute('''
            SELECT amount, project, status 
            FROM donations 
            WHERE id = %s
        ''', (donation_id,))
        donation = cursor.fetchone()
        
        if not donation:
            raise HTTPException(status_code=404, detail="Donation not found")
            
        amount, project, status = donation
        
        # Only allow deletion if status is 'pending' or 'completed'
        if status not in ['pending', 'completed']:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete donation with current status"
            )
        
        # Delete the donation
        cursor.execute('DELETE FROM donations WHERE id = %s', (donation_id,))
        
        # If donation was completed, reverse the accounting entries
        if status == 'completed':
            # Reverse the program area balance if project was specified
            if project:
                cursor.execute('''
                    UPDATE program_areas
                    SET balance = balance - %s
                    WHERE name = %s
                    RETURNING balance
                ''', (amount, project))
                
                if not cursor.fetchone():
                    logger.warning(f"Failed to update program area {project} when deleting donation")
            
            # Reverse the main account balance
            cursor.execute('''
                UPDATE bank_accounts
                SET balance = balance - %s
                WHERE name = 'Main Account'
                RETURNING balance
            ''', (amount,))
            
            if not cursor.fetchone():
                logger.error("Failed to update main account when deleting donation")
        
        # Create a notification about the deletion
        notification_message = f"Donation {donation_id} (Amount: {amount}) deleted"
        cursor.execute('''
            INSERT INTO notifications (message, type)
            VALUES (%s, 'donation_deletion')
        ''', (notification_message,))
        
        conn.commit()
        return {"message": "Donation deleted successfully and accounting entries reversed"}
        
    except Exception as e:
        logger.error(f"Error deleting donation: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete donation: {str(e)}"
        )
    finally:
        if conn:
            conn.close()
            
@app.get("/donors/", response_model=List[Donor])
def get_donors(search: Optional[str] = None):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get donors with their stats
        if search:
            cursor.execute('''
                SELECT 
                    d.id, d.name, d.email, d.phone, d.address, 
                    d.donor_type, d.notes, d.category, d.created_at,
                    COUNT(dn.id) as donation_count,
                    COALESCE(SUM(dn.amount), 0) as total_donated,
                    MIN(dn.date) as first_donation,
                    MAX(dn.date) as last_donation
                FROM donors d
                LEFT JOIN donations dn ON d.id = dn.donor_id
                WHERE d.name ILIKE %s OR d.email ILIKE %s OR d.phone ILIKE %s
                GROUP BY d.id
                ORDER BY d.name
            ''', (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            cursor.execute('''
                SELECT 
                    d.id, d.name, d.email, d.phone, d.address, 
                    d.donor_type, d.notes, d.category, d.created_at,
                    COUNT(dn.id) as donation_count,
                    COALESCE(SUM(dn.amount), 0) as total_donated,
                    MIN(dn.date) as first_donation,
                    MAX(dn.date) as last_donation
                FROM donors d
                LEFT JOIN donations dn ON d.id = dn.donor_id
                GROUP BY d.id
                ORDER BY d.name
            ''')
        
        donors = []
        for row in cursor.fetchall():
            donors.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "address": row[4],
                "donor_type": row[5],
                "notes": row[6],
                "category": row[7],
                "created_at": row[8],
                "stats": {
                    "donation_count": row[9],
                    "total_donated": float(row[10]),
                    "first_donation": row[11],
                    "last_donation": row[12]
                }
            })
            
        return donors
    except Exception as e:
        logger.error(f"Error fetching donors: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch donors")
    finally:
        if conn:
            conn.close()
            
@app.get("/donors/{donor_id}", response_model=Donor)
def get_donor(donor_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get donor basic info
        cursor.execute('''
            SELECT id, name, email, phone, address, donor_type, notes, category, created_at
            FROM donors
            WHERE id = %s
        ''', (donor_id,))
        
        donor = cursor.fetchone()
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
            
        # Get donor statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as donation_count,
                COALESCE(SUM(amount), 0) as total_donated,
                MIN(date) as first_donation,
                MAX(date) as last_donation
            FROM donations
            WHERE donor_id = %s
        ''', (donor_id,))
        
        stats = cursor.fetchone()
        
        return {
            "id": donor[0],
            "name": donor[1],
            "email": donor[2],
            "phone": donor[3],
            "address": donor[4],
            "donor_type": donor[5],
            "notes": donor[6],
            "category": donor[7],
            "created_at": donor[8],
            "stats": {
                "donation_count": stats[0] if stats else 0,
                "total_donated": float(stats[1]) if stats else 0.0,
                "first_donation": stats[2] if stats else None,
                "last_donation": stats[3] if stats else None
            }
        }
    except Exception as e:
        logger.error(f"Error fetching donor: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch donor")
    finally:
        if conn:
            conn.close()

@app.put("/donors/{donor_id}", response_model=Donor)
def update_donor(donor_id: int, donor: Donor):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE donors
            SET name = %s, email = %s, phone = %s, address = %s, 
                donor_type = %s, notes = %s
            WHERE id = %s
            RETURNING id, name, email, phone, address, donor_type, notes, created_at
        ''', (
            donor.name, donor.email, donor.phone, donor.address,
            donor.donor_type, donor.notes, donor_id
        ))
        
        updated_donor = cursor.fetchone()
        if not updated_donor:
            raise HTTPException(status_code=404, detail="Donor not found")
            
        conn.commit()
        return {
            "id": updated_donor[0],
            "name": updated_donor[1],
            "email": updated_donor[2],
            "phone": updated_donor[3],
            "address": updated_donor[4],
            "donor_type": updated_donor[5],
            "notes": updated_donor[6],
            "created_at": updated_donor[7]
        }
    except Exception as e:
        logger.error(f"Error updating donor: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update donor")
    finally:
        if conn:
            conn.close()

@app.delete("/donors/{donor_id}")
def delete_donor(donor_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # First check if donor exists
        cursor.execute('SELECT id FROM donors WHERE id = %s', (donor_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Donor not found")
            
        # Delete donor
        cursor.execute('DELETE FROM donors WHERE id = %s', (donor_id,))
        conn.commit()
        
        return {"message": "Donor deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting donor: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete donor")
    finally:
        if conn:
            conn.close()

@app.get("/donors/{donor_id}/donations")
def get_donor_donations(donor_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # First check if donor exists
        cursor.execute('SELECT name FROM donors WHERE id = %s', (donor_id,))
        donor = cursor.fetchone()
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
            
        donor_name = donor[0]
        
        # Get all donations for this donor
        cursor.execute('''
            SELECT id, date, amount, purpose 
            FROM transactions 
            WHERE type = 'deposit' AND purpose LIKE %s
            ORDER BY date DESC
        ''', (f"Donation from {donor_name}%",))
        
        donations = []
        for row in cursor.fetchall():
            # Parse the purpose field to extract project
            purpose_parts = row[3].split(' for ')
            project = purpose_parts[1] if len(purpose_parts) > 1 else 'general fund'
            
            donations.append({
                "id": row[0],
                "date": row[1].strftime("%Y-%m-%d") if isinstance(row[1], datetime) else row[1],
                "amount": row[2],
                "project": project,
                "status": "completed"
            })
            
        return {
            "donor_id": donor_id,
            "donor_name": donor_name,
            "donations": donations,
            "total_donations": sum(d['amount'] for d in donations),
            "donation_count": len(donations)
        }
    except Exception as e:
        logger.error(f"Error fetching donor donations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch donor donations")
    finally:
        if conn:
            conn.close()

@app.post("/donors/", response_model=Donor)
def create_donor(donor: DonorCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Validate donor type and category
        if donor.donor_type not in ["individual", "corporate", "foundation", "other"]:
            raise HTTPException(status_code=400, detail="Invalid donor type")
            
        if donor.category not in ["regular", "one-time"]:
            raise HTTPException(status_code=400, detail="Invalid donor category")
        
        cursor.execute('''
            INSERT INTO donors (name, email, phone, address, donor_type, notes, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, email, phone, address, donor_type, notes, category, created_at
        ''', (
            donor.name, donor.email, donor.phone, donor.address, 
            donor.donor_type, donor.notes, donor.category
        ))
        
        new_donor = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_donor[0],
            "name": new_donor[1],
            "email": new_donor[2],
            "phone": new_donor[3],
            "address": new_donor[4],
            "donor_type": new_donor[5],
            "notes": new_donor[6],
            "category": new_donor[7],
            "created_at": new_donor[8]
        }
    except Exception as e:
        logger.error(f"Error creating donor: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.put("/donors/{donor_id}", response_model=Donor)
def update_donor(donor_id: int, donor: DonorCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Validate donor type and category
        if donor.donor_type not in ["individual", "corporate", "foundation", "other"]:
            raise HTTPException(status_code=400, detail="Invalid donor type")
            
        if donor.category not in ["regular", "one-time"]:
            raise HTTPException(status_code=400, detail="Invalid donor category")
        
        cursor.execute('''
            UPDATE donors
            SET name = %s, email = %s, phone = %s, address = %s, 
                donor_type = %s, notes = %s, category = %s
            WHERE id = %s
            RETURNING id, name, email, phone, address, donor_type, notes, category, created_at
        ''', (
            donor.name, donor.email, donor.phone, donor.address,
            donor.donor_type, donor.notes, donor.category, donor_id
        ))
        
        updated_donor = cursor.fetchone()
        if not updated_donor:
            raise HTTPException(status_code=404, detail="Donor not found")
            
        conn.commit()
        return {
            "id": updated_donor[0],
            "name": updated_donor[1],
            "email": updated_donor[2],
            "phone": updated_donor[3],
            "address": updated_donor[4],
            "donor_type": updated_donor[5],
            "notes": updated_donor[6],
            "category": updated_donor[7],
            "created_at": updated_donor[8]
        }
    except Exception as e:
        logger.error(f"Error updating donor: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/donors/stats/")
def get_donor_stats():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get donation statistics grouped by donor
        cursor.execute('''
            SELECT d.id as donor_id, d.name, 
                   COUNT(t.id) as donation_count,
                   SUM(t.amount) as total_donated,
                   MIN(t.date) as first_donation,
                   MAX(t.date) as last_donation
            FROM donors d
            LEFT JOIN transactions t ON t.purpose LIKE 'Donation from ' || d.name || '%' AND t.type = 'deposit'
            GROUP BY d.id, d.name
        ''')
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {  # donor_id as key
                "name": row[1],
                "donation_count": row[2] or 0,
                "total_donated": float(row[3] or 0),
                "first_donation": row[4].strftime("%Y-%m-%d") if row[4] else None,
                "last_donation": row[5].strftime("%Y-%m-%d") if row[5] else None
            }
            
        return {"donor_stats": stats}
    except Exception as e:
        logger.error(f"Error fetching donor stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch donor stats")
    finally:
        if conn:
            conn.close()

@app.post("/projects/", response_model=Project)
def create_project(project: ProjectCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projects (name, description, start_date, end_date, budget, funding_source, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, description, start_date, end_date, budget, funding_source, status, created_at
        ''', (
            project.name,
            project.description,
            project.start_date,
            project.end_date,
            project.budget,
            project.funding_source,
            project.status
        ))
        
        new_project = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_project[0],
            "name": new_project[1],
            "description": new_project[2],
            "start_date": new_project[3].strftime("%Y-%m-%d"),
            "end_date": new_project[4].strftime("%Y-%m-%d"),
            "budget": new_project[5],
            "funding_source": new_project[6],
            "status": new_project[7],
            "created_at": new_project[8]
        }
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/projects/")
def get_projects():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, start_date, end_date, budget, funding_source, status, created_at
            FROM projects
            ORDER BY created_at DESC
        ''')
        
        projects = []
        for row in cursor.fetchall():
            projects.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "start_date": row[3].strftime("%Y-%m-%d"),
                "end_date": row[4].strftime("%Y-%m-%d"),
                "budget": row[5],
                "funding_source": row[6],
                "status": row[7],
                "created_at": row[8].strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")
    finally:
        if conn:
            conn.close()

@app.get("/projects/{project_id}")
def get_project(project_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, start_date, end_date, budget, funding_source, status, created_at
            FROM projects
            WHERE id = %s
        ''', (project_id,))
        
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        return {
            "id": project[0],
            "name": project[1],
            "description": project[2],
            "start_date": project[3].strftime("%Y-%m-%d"),
            "end_date": project[4].strftime("%Y-%m-%d"),
            "budget": project[5],
            "funding_source": project[6],
            "status": project[7],
            "created_at": project[8].strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch project")
    finally:
        if conn:
            conn.close()

@app.delete("/projects/{project_id}")
def delete_project(project_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM projects WHERE id = %s', (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")
            
        cursor.execute('DELETE FROM projects WHERE id = %s', (project_id,))
        conn.commit()
        
        return {"message": "Project deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete project")
    finally:
        if conn:
            conn.close()

@app.post("/activities/", response_model=Activity)
def create_activity(activity: ActivityCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # First verify the project exists
        cursor.execute('SELECT name FROM projects WHERE id = %s', (activity.project_id,))
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        project_name = project[0]
        
        # Insert the activity with status "pending" if not specified
        status = activity.status if activity.status else "pending"
        
        cursor.execute('''
            INSERT INTO activities (name, project_id, description, start_date, end_date, budget, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, project_id, description, start_date, end_date, budget, status, created_at
        ''', (
            activity.name,
            activity.project_id,
            activity.description,
            activity.start_date,
            activity.end_date,
            activity.budget,
            status
        ))
        
        new_activity = cursor.fetchone()
        
        # Create an approval request if status is pending
        if status == "pending":
            cursor.execute('''
                INSERT INTO activity_approvals 
                (activity_id, activity_name, requested_by, requested_amount, status)
                VALUES (%s, %s, %s, %s, 'pending')
            ''', (
                new_activity[0],  # activity_id
                new_activity[1],  # activity_name
                "system",         # requested_by (could be changed to actual user)
                new_activity[6],  # budget amount
            ))
        
        conn.commit()
        
        return {
            "id": new_activity[0],
            "name": new_activity[1],
            "project_id": new_activity[2],
            "project_name": project_name,
            "description": new_activity[3],
            "start_date": new_activity[4].strftime("%Y-%m-%d"),
            "end_date": new_activity[5].strftime("%Y-%m-%d"),
            "budget": new_activity[6],
            "status": new_activity[7],
            "created_at": new_activity[8].strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
@app.get("/activities/", response_model=List[Activity])
def get_activities():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.id, a.name, a.project_id, p.name as project_name, 
                   a.description, a.start_date, a.end_date, 
                   a.budget, a.status, a.created_at
            FROM activities a
            JOIN projects p ON a.project_id = p.id
            ORDER BY a.created_at DESC
        ''')
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                "id": row[0],
                "name": row[1],
                "project_id": row[2],
                "project_name": row[3],
                "description": row[4],
                "start_date": row[5].strftime("%Y-%m-%d"),
                "end_date": row[6].strftime("%Y-%m-%d"),
                "budget": row[7],
                "status": row[8],
                "created_at": row[9].strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return activities
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch activities")
    finally:
        if conn:
            conn.close()

@app.get("/activities/{activity_id}", response_model=Activity)
def get_activity(activity_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.id, a.name, a.project_id, p.name as project_name, 
                   a.description, a.start_date, a.end_date, 
                   a.budget, a.status, a.created_at
            FROM activities a
            JOIN projects p ON a.project_id = p.id
            WHERE a.id = %s
        ''', (activity_id,))
        
        activity = cursor.fetchone()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        return {
            "id": activity[0],
            "name": activity[1],
            "project_id": activity[2],
            "project_name": activity[3],
            "description": activity[4],
            "start_date": activity[5].strftime("%Y-%m-%d"),
            "end_date": activity[6].strftime("%Y-%m-%d"),
            "budget": activity[7],
            "status": activity[8],
            "created_at": activity[9].strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error fetching activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity")
    finally:
        if conn:
            conn.close()

@app.put("/activities/{activity_id}", response_model=Activity)
def update_activity(activity_id: int, activity: ActivityCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()        
        # First verify the project exists
        cursor.execute('SELECT name FROM projects WHERE id = %s', (activity.project_id,))
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        project_name = project[0]
        
        cursor.execute('''
            UPDATE activities
            SET name = %s, project_id = %s, description = %s, 
                start_date = %s, end_date = %s, budget = %s, status = %s
            WHERE id = %s
            RETURNING id, name, project_id, description, start_date, end_date, budget, status, created_at
        ''', (
            activity.name,
            activity.project_id,
            activity.description,
            activity.start_date,
            activity.end_date,
            activity.budget,
            activity.status,
            activity_id
        ))
        
        updated_activity = cursor.fetchone()
        if not updated_activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        conn.commit()
        return {
            "id": updated_activity[0],
            "name": updated_activity[1],
            "project_id": updated_activity[2],
            "project_name": project_name,
            "description": updated_activity[3],
            "start_date": updated_activity[4].strftime("%Y-%m-%d"),
            "end_date": updated_activity[5].strftime("%Y-%m-%d"),
            "budget": updated_activity[6],
            "status": updated_activity[7],
            "created_at": updated_activity[8].strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error updating activity: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.delete("/activities/{activity_id}")
def delete_activity(activity_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM activities WHERE id = %s', (activity_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Activity not found")
            
        cursor.execute('DELETE FROM activities WHERE id = %s', (activity_id,))
        conn.commit()
        
        return {"message": "Activity deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting activity: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete activity")
    finally:
        if conn:
            conn.close()
@app.post("/budget-items/", response_model=BudgetItem)
def create_budget_item(budget_item: BudgetItemCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify project exists
        cursor.execute('SELECT id FROM projects WHERE id = %s', (budget_item.project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")
            
        cursor.execute('''
            INSERT INTO budget_items (project_id, item_name, description, quantity, unit_price, category)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, project_id, item_name, description, quantity, unit_price, total, category, created_at
        ''', (
            budget_item.project_id,
            budget_item.item_name,
            budget_item.description,
            budget_item.quantity,
            budget_item.unit_price,
            budget_item.category
        ))
        
        new_item = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_item[0],
            "project_id": new_item[1],
            "item_name": new_item[2],
            "description": new_item[3],
            "quantity": new_item[4],
            "unit_price": new_item[5],
            "total": new_item[6],
            "category": new_item[7],
            "created_at": new_item[8]
        }
    except Exception as e:
        logger.error(f"Error creating budget item: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/budget-items/{project_id}", response_model=List[BudgetItem])
def get_budget_items(project_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, project_id, item_name, description, quantity, unit_price, total, category, created_at
            FROM budget_items
            WHERE project_id = %s
            ORDER BY created_at DESC
        ''', (project_id,))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                "id": row[0],
                "project_id": row[1],
                "item_name": row[2],
                "description": row[3],
                "quantity": row[4],
                "unit_price": row[5],
                "total": row[6],
                "category": row[7],
                "created_at": row[8].strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return items
    except Exception as e:
        logger.error(f"Error fetching budget items: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch budget items")
    finally:
        if conn:
            conn.close()

@app.delete("/budget-items/{item_id}")
def delete_budget_item(item_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM budget_items WHERE id = %s RETURNING id', (item_id,))
        deleted_item = cursor.fetchone()
        if not deleted_item:
            raise HTTPException(status_code=404, detail="Budget item not found")
            
        conn.commit()
        return {"message": "Budget item deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting budget item: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete budget item")
    finally:
        if conn:
            conn.close()
            
@app.post("/employees/", response_model=Employee)
def create_employee(employee: EmployeeCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            dob = datetime.strptime(employee.dob, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        cursor.execute('''
            INSERT INTO employees (name, nin, dob, qualification, email, phone, address, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, nin, dob, qualification, email, phone, address, status, created_at
        ''', (
            employee.name,
            employee.nin,
            dob,
            employee.qualification,
            employee.email,
            employee.phone,
            employee.address,
            employee.status
        ))
        
        new_employee = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_employee[0],
            "name": new_employee[1],
            "nin": new_employee[2],
            "dob": new_employee[3].strftime("%Y-%m-%d"),
            "qualification": new_employee[4],
            "email": new_employee[5],
            "phone": new_employee[6],
            "address": new_employee[7],
            "status": new_employee[8],
            "created_at": new_employee[9].strftime("%Y-%m-%d %H:%M:%S")
        }
    except psycopg2.IntegrityError as e:
        if "employees_nin_key" in str(e):
            raise HTTPException(status_code=400, detail="NIN already exists")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating employee: {str(e)}")
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to create employee",
                "error": str(e),
                "type": type(e).__name__
            }
        )
    finally:
        if conn:
            conn.close()
            
@app.get("/employees/", response_model=List[Employee])
def get_employees():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, nin, dob, qualification, email, phone, address, status, created_at
            FROM employees
            ORDER BY created_at DESC
        ''')
        
        employees = []
        for row in cursor.fetchall():
            employees.append({
                "id": row[0],
                "name": row[1],
                "nin": row[2],
                "dob": row[3].strftime("%Y-%m-%d"),
                "qualification": row[4],
                "email": row[5],
                "phone": row[6],
                "address": row[7],
                "status": row[8],
                "created_at": row[9].strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return employees
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch employees")
    finally:
        if conn:
            conn.close()

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM employees WHERE id = %s RETURNING id', (employee_id,))
        deleted = cursor.fetchone()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        conn.commit()
        return {"message": "Employee deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting employee: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete employee")
    finally:
        if conn:
            conn.close()

@app.post("/deployments/", response_model=Deployment)
def create_deployment(deployment: DeploymentCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify employee exists
        cursor.execute('SELECT name FROM employees WHERE id = %s', (deployment.employee_id,))
        employee = cursor.fetchone()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        employee_name = employee[0]
        
        # Verify activity exists and get project name
        cursor.execute('''
            SELECT a.name, p.name 
            FROM activities a
            JOIN projects p ON a.project_id = p.id
            WHERE a.id = %s
        ''', (deployment.activity_id,))
        activity = cursor.fetchone()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        activity_name = activity[0]
        project_name = activity[1]
        
        cursor.execute('''
            INSERT INTO deployments (employee_id, activity_id, role)
            VALUES (%s, %s, %s)
            RETURNING id, employee_id, activity_id, role, created_at
        ''', (
            deployment.employee_id,
            deployment.activity_id,
            deployment.role
        ))
        
        new_deployment = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_deployment[0],
            "employee_id": new_deployment[1],
            "employee_name": employee_name,
            "activity_id": new_deployment[2],
            "activity_name": activity_name,
            "project_name": project_name,
            "role": new_deployment[3],
            "created_at": new_deployment[4].strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error creating deployment: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/deployments/", response_model=List[Deployment])
def get_deployments():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.id, d.employee_id, e.name as employee_name, 
                   d.activity_id, a.name as activity_name, p.name as project_name,
                   d.role, d.created_at
            FROM deployments d
            JOIN employees e ON d.employee_id = e.id
            JOIN activities a ON d.activity_id = a.id
            JOIN projects p ON a.project_id = p.id
            ORDER BY d.created_at DESC
        ''')
        
        deployments = []
        for row in cursor.fetchall():
            deployments.append({
                "id": row[0],
                "employee_id": row[1],
                "employee_name": row[2],
                "activity_id": row[3],
                "activity_name": row[4],
                "project_name": row[5],
                "role": row[6],
                "created_at": row[7].strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return deployments
    except Exception as e:
        logger.error(f"Error fetching deployments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch deployments")
    finally:
        if conn:
            conn.close()

@app.delete("/deployments/{deployment_id}")
def delete_deployment(deployment_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM deployments WHERE id = %s RETURNING id', (deployment_id,))
        deleted = cursor.fetchone()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Deployment not found")
            
        conn.commit()
        return {"message": "Deployment deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting deployment: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete deployment")
    finally:
        if conn:
            conn.close()
@app.post("/work-opportunities/", response_model=WorkOpportunity)
def create_work_opportunity(opportunity: WorkOpportunityCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO work_opportunities (title, description, status)
            VALUES (%s, %s, %s)
            RETURNING id, title, description, status, created_at
        ''', (
            opportunity.title,
            opportunity.description,
            opportunity.status
        ))
        
        new_opportunity = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_opportunity[0],
            "title": new_opportunity[1],
            "description": new_opportunity[2],
            "status": new_opportunity[3],
            "created_at": new_opportunity[4]
        }
    except Exception as e:
        logger.error(f"Error creating work opportunity: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/work-opportunities/", response_model=List[WorkOpportunity])
def get_work_opportunities():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, description, status, created_at
            FROM work_opportunities
            ORDER BY created_at DESC
        ''')
        
        opportunities = []
        for row in cursor.fetchall():
            opportunities.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "status": row[3],
                "created_at": row[4].strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return opportunities
    except Exception as e:
        logger.error(f"Error fetching work opportunities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch work opportunities")
    finally:
        if conn:
            conn.close()

@app.post("/opportunity-assignments/", response_model=OpportunityAssignment)
def create_opportunity_assignment(assignment: OpportunityAssignmentCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify opportunity exists
        cursor.execute('SELECT title FROM work_opportunities WHERE id = %s', (assignment.opportunity_id,))
        opportunity = cursor.fetchone()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        opportunity_title = opportunity[0]
        
        # Verify employee exists
        cursor.execute('SELECT name FROM employees WHERE id = %s', (assignment.employee_id,))
        employee = cursor.fetchone()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        employee_name = employee[0]
        
        cursor.execute('''
            INSERT INTO opportunity_assignments (opportunity_id, employee_id)
            VALUES (%s, %s)
            RETURNING id, opportunity_id, employee_id, created_at
        ''', (
            assignment.opportunity_id,
            assignment.employee_id
        ))
        
        new_assignment = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_assignment[0],
            "opportunity_id": new_assignment[1],
            "opportunity_title": opportunity_title,
            "employee_id": new_assignment[2],
            "employee_name": employee_name,
            "created_at": new_assignment[3].strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error creating opportunity assignment: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/opportunity-assignments/{opportunity_id}", response_model=List[OpportunityAssignment])
def get_opportunity_assignments(opportunity_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT oa.id, oa.opportunity_id, w.title as opportunity_title,
                   oa.employee_id, e.name as employee_name, oa.created_at
            FROM opportunity_assignments oa
            JOIN work_opportunities w ON oa.opportunity_id = w.id
            JOIN employees e ON oa.employee_id = e.id
            WHERE oa.opportunity_id = %s
            ORDER BY oa.created_at DESC
        ''', (opportunity_id,))
        
        assignments = []
        for row in cursor.fetchall():
            assignments.append({
                "id": row[0],
                "opportunity_id": row[1],
                "opportunity_title": row[2],
                "employee_id": row[3],
                "employee_name": row[4],
                "created_at": row[5].strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return assignments
    except Exception as e:
        logger.error(f"Error fetching opportunity assignments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch opportunity assignments")
    finally:
        if conn:
            conn.close()

@app.delete("/opportunity-assignments/{assignment_id}")
def delete_opportunity_assignment(assignment_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM opportunity_assignments WHERE id = %s RETURNING id', (assignment_id,))
        deleted = cursor.fetchone()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Assignment not found")
            
        conn.commit()
        return {"message": "Assignment deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting opportunity assignment: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete opportunity assignment")
    finally:
        if conn:
            conn.close()
@app.post("/payments/request", response_model=Payment)
def request_payment(payment: PaymentRequest):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify employee exists
        cursor.execute("SELECT id FROM employees WHERE id = %s", (payment.employee_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Insert payment request
        cursor.execute('''
            INSERT INTO payments (
                employee_id, amount, payment_period, 
                description, payment_method, status
            ) 
            VALUES (%s, %s, %s, %s, %s, 'pending')
            RETURNING id
        ''', (
            payment.employee_id, payment.amount, payment.payment_period,
            payment.description, payment.payment_method
        ))
        
        payment_id = cursor.fetchone()[0]
        conn.commit()
        
        # Return the created payment with all required fields
        cursor.execute('''
            SELECT 
                p.id, 
                p.employee_id, 
                e.name as employee_name,
                p.amount, 
                p.payment_period, 
                p.description,
                p.payment_method,
                p.status, 
                p.remarks,
                p.created_at, 
                p.approved_at,
                p.processed_by
            FROM payments p
            JOIN employees e ON p.employee_id = e.id
            WHERE p.id = %s
        ''', (payment_id,))
        payment_data = cursor.fetchone()
        
        return dict(zip([col[0] for col in cursor.description], payment_data))
    except Exception as e:
        logger.error(f"Error creating payment request: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to create payment request")
    finally:
        if conn:
            conn.close()
@app.post("/payments/approve", response_model=Payment)
def approve_payment(approval: PaymentApproval):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get the payment
        cursor.execute('''
            SELECT p.*, e.name as employee_name 
            FROM payments p
            JOIN employees e ON p.employee_id = e.id
            WHERE p.id = %s
        ''', (approval.payment_id,))
        payment_data = cursor.fetchone()
        
        if not payment_data:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        if payment_data[7] != 'pending':  # status field
            raise HTTPException(status_code=400, detail="Payment is not pending approval")
        
        # Update payment status
        status = 'approved' if approval.approved else 'rejected'
        cursor.execute('''
            UPDATE payments 
            SET status = %s, 
                remarks = %s, 
                approved_at = CURRENT_TIMESTAMP,
                processed_by = 1  # In a real app, this would be the logged-in user's ID
            WHERE id = %s
            RETURNING *
        ''', (status, approval.remarks, approval.payment_id))
        
        updated_payment = cursor.fetchone()
        conn.commit()
        
        return dict(zip([col[0] for col in cursor.description], updated_payment))
    except Exception as e:
        logger.error(f"Error processing payment approval: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to process payment approval")
    finally:
        if conn:
            conn.close()

@app.get("/payments/pending", response_model=List[Payment])
def get_pending_payments():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.id, 
                p.employee_id, 
                e.name as employee_name,
                p.amount, 
                p.payment_period, 
                p.description,
                p.payment_method,
                p.status, 
                p.remarks,
                p.created_at, 
                p.approved_at,
                p.processed_by
            FROM payments p
            JOIN employees e ON p.employee_id = e.id
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
        ''')
        
        payments = cursor.fetchall()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in payments]
    except Exception as e:
        logger.error(f"Error fetching pending payments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending payments")
    finally:
        if conn:
            conn.close()

@app.get("/payments/history", response_model=List[Payment])
def get_payment_history(status: Optional[str] = None):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                p.id, 
                p.employee_id, 
                e.name as employee_name,
                p.amount, 
                p.payment_period, 
                p.description,
                p.payment_method,
                p.status, 
                p.remarks,
                p.created_at, 
                p.approved_at,
                p.processed_by
            FROM payments p
            JOIN employees e ON p.employee_id = e.id
        '''
        params = []
        
        if status:
            query += ' WHERE p.status = %s'
            params.append(status)
            
        query += ' ORDER BY p.created_at DESC'
        
        cursor.execute(query, params)
        payments = cursor.fetchall()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in payments]
    except Exception as e:
        logger.error(f"Error fetching payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment history")
    finally:
        if conn:
            conn.close()
            
@app.get("/payments/employee/{employee_id}", response_model=List[Payment])
def get_employee_payments(employee_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, e.name as employee_name 
            FROM payments p
            JOIN employees e ON p.employee_id = e.id
            WHERE p.employee_id = %s
            ORDER BY p.created_at DESC
        ''', (employee_id,))
        
        payments = cursor.fetchall()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in payments]
    except Exception as e:
        logger.error(f"Error fetching employee payments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch employee payments")
    finally:
        if conn:
            conn.close()
            
@app.post("/reports/")
def create_report(
    employee_id: int = Form(...),
    activity_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    attachments: List[UploadFile] = File([])
):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify employee exists
        cursor.execute('SELECT id FROM employees WHERE id = %s', (employee_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Verify activity exists
        cursor.execute('SELECT id FROM activities WHERE id = %s', (activity_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Save report to database
        cursor.execute('''
            INSERT INTO reports (employee_id, activity_id, title, content, status, submitted_by)
            VALUES (%s, %s, %s, %s, 'submitted', %s)
            RETURNING id
        ''', (employee_id, activity_id, title, content, employee_id))
        
        report_id = cursor.fetchone()[0]
        
        # Handle file attachments
        if attachments:
            upload_dir = Path(UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            for file in attachments:
                file_id = str(uuid.uuid4())
                file_ext = Path(file.filename).suffix
                file_path = upload_dir / f"{file_id}{file_ext}"
                
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                cursor.execute('''
                    INSERT INTO report_attachments (report_id, original_filename, stored_filename, file_type)
                    VALUES (%s, %s, %s, %s)
                ''', (report_id, file.filename, str(file_path), file.content_type))
        
        conn.commit()
        
        return {
            "id": report_id,
            "employee_id": employee_id,
            "activity_id": activity_id,
            "title": title,
            "content": content,
            "status": "submitted"
        }
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to create report")
    finally:
        if conn:
            conn.close()

@app.get("/reports/")
def get_reports():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Updated query to handle potential schema differences
        cursor.execute('''
            SELECT r.id, r.title, r.content, r.status, r.created_at,
                   a.id as activity_id, a.name as activity_name,
                   COALESCE(r.employee_id, 0) as employee_id,
                   COALESCE(e.name, 'Unknown') as employee_name,
                   COALESCE(r.submitted_by, 0) as submitted_by,
                   COALESCE(submitter.name, 'Unknown') as submitted_by_name
            FROM reports r
            LEFT JOIN activities a ON r.activity_id = a.id
            LEFT JOIN employees e ON r.employee_id = e.id
            LEFT JOIN employees submitter ON r.submitted_by = submitter.id
            ORDER BY r.created_at DESC
        ''')
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "status": row[3],
                "created_at": row[4],
                "activity_id": row[5],
                "activity_name": row[6],
                "employee_id": row[7],
                "employee_name": row[8],
                "submitted_by": row[9],
                "submitted_by_name": row[10]
            })
            
        return {"reports": reports}
    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reports")
    finally:
        if conn:
            conn.close()

@app.get("/reports/export")
def export_reports(
    status: str = None,
    activity_id: int = None,
    search: str = None,
    start_date: str = None,
    end_date: str = None
):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT r.id, r.title, a.name as activity, e.name as employee,
                   r.status, r.created_at, r.director_comments
            FROM reports r
            JOIN activities a ON r.activity_id = a.id
            JOIN employees e ON r.employee_id = e.id
        """
        
        conditions = []
        params = []
        
        if status:
            conditions.append("r.status = %s")
            params.append(status)
            
        if activity_id:
            conditions.append("r.activity_id = %s")
            params.append(activity_id)
            
        if search:
            conditions.append("(r.title ILIKE %s OR r.content ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
            
        if start_date and end_date:
            conditions.append("r.created_at BETWEEN %s AND %s")
            params.extend([start_date, end_date])
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY r.created_at DESC"
        
        cursor.execute(query, params)
        reports = cursor.fetchall()
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID", "Title", "Activity", "Employee", 
            "Status", "Created At", "Director Comments"
        ])
        
        # Write data
        for report in reports:
            writer.writerow([
                report[0], report[1], report[2], report[3],
                report[4], report[5], report[6] or ""
            ])
        
        # Return CSV file
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=reports_export_{datetime.now().date()}.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to export reports")
    finally:
        if conn:
            conn.close()

@app.put("/reports/{report_id}/status")
def update_report_status(report_id: int, status_update: dict):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify report exists
        cursor.execute("SELECT id FROM reports WHERE id = %s", (report_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Report not found")
            
        # Update status
        cursor.execute("""
            UPDATE reports 
            SET status = %s, 
                approved_by = %s,
                approved_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (status_update['status'], status_update.get('director_id'), report_id))
        
        # Update comments if provided
        if status_update.get('comments'):
            cursor.execute("""
                UPDATE reports
                SET director_comments = %s
                WHERE id = %s
            """, (status_update['comments'], report_id))
            
        conn.commit()
        return {"message": "Report status updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating report status: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update report status")
    finally:
        if conn:
            conn.close()

@app.get("/director/reports/")
def get_director_reports(
    status: str = "submitted",
    page: int = 1,
    per_page: int = 10,
    activity_id: int = None,
    search: str = None,
    start_date: str = None,
    end_date: str = None
):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Base query
        query = """
            SELECT r.id, r.title, r.content, r.status, r.created_at,
                   a.id as activity_id, a.name as activity_name,
                   e.id as employee_id, e.name as employee_name,
                   r.submitted_by, submitter.name as submitted_by_name,
                   COUNT(ra.id) as attachments_count
            FROM reports r
            JOIN activities a ON r.activity_id = a.id
            JOIN employees e ON r.employee_id = e.id
            LEFT JOIN employees submitter ON r.submitted_by = submitter.id
            LEFT JOIN report_attachments ra ON r.id = ra.report_id
        """
        
        # Where conditions
        conditions = []
        params = []
        
        if status != "all":
            conditions.append("r.status = %s")
            params.append(status)
            
        if activity_id:
            conditions.append("r.activity_id = %s")
            params.append(activity_id)
            
        if search:
            conditions.append("(r.title ILIKE %s OR r.content ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
            
        if start_date and end_date:
            conditions.append("r.created_at BETWEEN %s AND %s")
            params.extend([start_date, end_date])
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        # Group by and pagination
        query += """
            GROUP BY r.id, a.id, e.id, submitter.id
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        reports = cursor.fetchall()
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM reports r"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
            
        cursor.execute(count_query, params[:-2])  # Exclude LIMIT params
        total_reports = cursor.fetchone()[0]
        
        # Format results
        result = []
        for row in reports:
            report = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "status": row[3],
                "created_at": row[4],
                "activity_id": row[5],
                "activity_name": row[6],
                "employee_id": row[7],
                "employee_name": row[8],
                "submitted_by": row[9],
                "submitted_by_name": row[10],
                "attachments_count": row[11]
            }
            result.append(report)
            
        return {
            "reports": result,
            "total": total_reports,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_reports + per_page - 1) // per_page
        }
        
    except Exception as e:
        logger.error(f"Error fetching director reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reports")
    finally:
        if conn:
            conn.close()

@app.delete("/reports/{report_id}")
def delete_report(report_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # First check if report exists
        cursor.execute('SELECT id FROM reports WHERE id = %s', (report_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Delete the report (attachments will be deleted automatically due to ON DELETE CASCADE)
        cursor.execute('DELETE FROM reports WHERE id = %s', (report_id,))
        conn.commit()
        
        return {"message": "Report deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete report")
    finally:
        if conn:
            conn.close()

@app.post("/activity-approvals/", response_model=ActivityApproval)
def create_activity_approval(approval: ActivityApprovalRequest):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify activity exists
        cursor.execute('SELECT name FROM activities WHERE id = %s', (approval.activity_id,))
        activity = cursor.fetchone()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        activity_name = activity[0]
        
        cursor.execute('''
            INSERT INTO activity_approvals 
            (activity_id, activity_name, requested_by, requested_amount, comments, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            RETURNING id, activity_id, activity_name, requested_by, requested_amount, 
                      comments, status, created_at, approved_at, approved_by, response_comments
        ''', (
            approval.activity_id,
            activity_name,
            approval.requested_by,
            approval.requested_amount,
            approval.comments
        ))
        
        new_approval = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_approval[0],
            "activity_id": new_approval[1],
            "activity_name": new_approval[2],
            "requested_by": new_approval[3],
            "requested_amount": new_approval[4],
            "comments": new_approval[5],
            "status": new_approval[6],
            "created_at": new_approval[7],
            "approved_at": new_approval[8],
            "approved_by": new_approval[9],
            "response_comments": new_approval[10]
        }
    except Exception as e:
        logger.error(f"Error creating activity approval: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.put("/activity-approvals/{approval_id}", response_model=ActivityApproval)
def update_activity_approval(approval_id: int, decision_data: ApprovalDecision):
    if decision_data.decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be either 'approved' or 'rejected'")
    
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE activity_approvals
            SET status = %s,
                approved_at = CURRENT_TIMESTAMP,
                approved_by = %s,
                response_comments = %s
            WHERE id = %s
            RETURNING id, activity_id, activity_name, requested_by, requested_amount, 
                      comments, status, created_at, approved_at, approved_by, response_comments
        ''', (decision, approved_by, response_comments, approval_id))
        
        updated_approval = cursor.fetchone()
        if not updated_approval:
            raise HTTPException(status_code=404, detail="Approval request not found")
            
        # If approved, update the activity status
        if decision == "approved":
            cursor.execute('''
                UPDATE activities
                SET status = 'approved'
                WHERE id = %s
            ''', (updated_approval[1],))
            
        conn.commit()
        
        return {
            "id": updated_approval[0],
            "activity_id": updated_approval[1],
            "activity_name": updated_approval[2],
            "requested_by": updated_approval[3],
            "requested_amount": updated_approval[4],
            "comments": updated_approval[5],
            "status": updated_approval[6],
            "created_at": updated_approval[7],
            "approved_at": updated_approval[8],
            "approved_by": updated_approval[9],
            "response_comments": updated_approval[10]
        }
    except Exception as e:
        logger.error(f"Error updating activity approval: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/activity-approvals/", response_model=List[ActivityApproval])
def get_activity_approvals(status: Optional[str] = None):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, activity_id, activity_name, requested_by, requested_amount, 
                   comments, status, created_at, approved_at, approved_by, response_comments
            FROM activity_approvals
        '''
        
        params = []
        if status:
            query += ' WHERE status = %s'
            params.append(status)
            
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        
        approvals = []
        for row in cursor.fetchall():
            # Get budget items for this activity
            cursor.execute('''
                SELECT id, project_id, activity_id, item_name, description, 
                       quantity, unit_price, total, category, created_at
                FROM budget_items
                WHERE activity_id = %s
            ''', (row[1],))  # row[1] is activity_id
            
            budget_items = []
            for item in cursor.fetchall():
                budget_items.append({
                    "id": item[0],
                    "project_id": item[1],
                    "activity_id": item[2],
                    "item_name": item[3],
                    "description": item[4],
                    "quantity": item[5],
                    "unit_price": item[6],
                    "total": item[7],
                    "category": item[8],
                    "created_at": item[9]
                })
            
            approvals.append({
                "id": row[0],
                "activity_id": row[1],
                "activity_name": row[2],
                "requested_by": row[3],
                "requested_amount": row[4],
                "comments": row[5],
                "status": row[6],
                "created_at": row[7],
                "approved_at": row[8],
                "approved_by": row[9],
                "response_comments": row[10],
                "budget_items": budget_items  # Add budget items to the response
            })
            
        return approvals
    except Exception as e:
        logger.error(f"Error fetching activity approvals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity approvals")
    finally:
        if conn:
            conn.close()

@app.get("/activities/{activity_id}/budget-items/", response_model=List[BudgetItem])
def get_activity_budget_items(activity_id: int):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify activity exists
        cursor.execute('SELECT id FROM activities WHERE id = %s', (activity_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Activity not found")
            
        cursor.execute('''
            SELECT id, project_id, activity_id, item_name, description, 
                   quantity, unit_price, total, category, created_at
            FROM budget_items
            WHERE activity_id = %s
            ORDER BY created_at DESC
        ''', (activity_id,))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                "id": row[0],
                "project_id": row[1],
                "activity_id": row[2],
                "item_name": row[3],
                "description": row[4],
                "quantity": row[5],
                "unit_price": row[6],
                "total": row[7],
                "category": row[8],
                "created_at": row[9].strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return items
    except Exception as e:
        logger.error(f"Error fetching activity budget items: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity budget items")
    finally:
        if conn:
            conn.close()

@app.post("/activities/{activity_id}/budget-items/", response_model=BudgetItem)
def create_activity_budget_item(activity_id: int, budget_item: BudgetItemCreate):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify activity exists and get its project_id
        cursor.execute('SELECT project_id FROM activities WHERE id = %s', (activity_id,))
        activity = cursor.fetchone()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        project_id = activity[0]
            
        cursor.execute('''
            INSERT INTO budget_items (project_id, activity_id, item_name, description, quantity, unit_price, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, project_id, activity_id, item_name, description, quantity, unit_price, total, category, created_at
        ''', (
            project_id,
            activity_id,
            budget_item.item_name,
            budget_item.description,
            budget_item.quantity,
            budget_item.unit_price,
            budget_item.category
        ))
        
        new_item = cursor.fetchone()
        conn.commit()
        
        return {
            "id": new_item[0],
            "project_id": new_item[1],
            "activity_id": new_item[2],
            "item_name": new_item[3],
            "description": new_item[4],
            "quantity": new_item[5],
            "unit_price": new_item[6],
            "total": new_item[7],
            "category": new_item[8],
            "created_at": new_item[9]
        }
    except Exception as e:
        logger.error(f"Error creating activity budget item: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/activities/{activity_id}/request-approval")
def request_activity_approval(activity_id: int, requested_by: str = "system"):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get activity details
        cursor.execute('''
            SELECT a.id, a.name, a.budget 
            FROM activities a
            WHERE a.id = %s
        ''', (activity_id,))
        activity = cursor.fetchone()
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        # Create approval request
        cursor.execute('''
            INSERT INTO activity_approvals 
            (activity_id, activity_name, requested_by, requested_amount, status)
            VALUES (%s, %s, %s, %s, 'pending')
            ON CONFLICT (activity_id) DO UPDATE
            SET status = 'pending',
                requested_at = CURRENT_TIMESTAMP
            RETURNING id
        ''', (
            activity[0],  # activity_id
            activity[1],  # activity_name
            requested_by,
            activity[2]   # budget amount
        ))
        
        # Update activity status
        cursor.execute('''
            UPDATE activities
            SET status = 'pending'
            WHERE id = %s
        ''', (activity_id,))
        
        conn.commit()
        return {"message": "Approval requested successfully"}
    except Exception as e:
        logger.error(f"Error requesting approval: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
