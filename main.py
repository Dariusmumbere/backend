from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import List, Optional
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://itech_l1q2_user:AoqQkrtzrQW7WEDOJdh0C6hhlY5Xe3sv@dpg-cuvnsbggph6c73ev87g0-a/itech_l1q2")
pool = None

async def get_db():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

# Models
class SavingsGoal(BaseModel):
    target_amount: float
    current_amount: float
    start_date: date
    target_date: date
    monthly_savings: float

class SavingsTransaction(BaseModel):
    amount: float
    type: str  # 'deposit' or 'withdrawal'
    date: date
    description: Optional[str] = None

class AbstinenceTracker(BaseModel):
    start_date: date
    end_date: date
    current_streak: int
    longest_streak: int
    total_days: int

class AbstinenceCheckIn(BaseModel):
    date: date
    success: bool
    notes: Optional[str] = None

class SavingsProgress(BaseModel):
    progress_percent: float
    months_remaining: int
    monthly_savings: float
    on_track: bool

class AbstinenceProgress(BaseModel):
    days_completed: int
    total_days_planned: int
    days_remaining: int
    success_rate: float

# Database initialization
async def initialize_db():
    pool = await get_db()
    async with pool.acquire() as conn:
        # Create tables if they don't exist
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS savings_goal (
                id SERIAL PRIMARY KEY,
                target_amount NUMERIC NOT NULL,
                current_amount NUMERIC NOT NULL,
                start_date DATE NOT NULL,
                target_date DATE NOT NULL,
                monthly_savings NUMERIC NOT NULL
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS savings_transactions (
                id SERIAL PRIMARY KEY,
                amount NUMERIC NOT NULL,
                type VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                description TEXT
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS abstinence_tracker (
                id SERIAL PRIMARY KEY,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                current_streak INTEGER NOT NULL,
                longest_streak INTEGER NOT NULL,
                total_days INTEGER NOT NULL
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS abstinence_checkins (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL UNIQUE,
                success BOOLEAN NOT NULL,
                notes TEXT
            )
        ''')
        
        # Initialize with default data if tables are empty
        if await conn.fetchval("SELECT COUNT(*) FROM savings_goal") == 0:
            start_date = date.today()
            target_date = start_date + timedelta(days=19*30)  # 19 months
            await conn.execute('''
                INSERT INTO savings_goal (target_amount, current_amount, start_date, target_date, monthly_savings)
                VALUES (100000000, 0, $1, $2, 5263157.89)
            ''', start_date, target_date)
        
        if await conn.fetchval("SELECT COUNT(*) FROM abstinence_tracker") == 0:
            start_date = date.today()
            end_date = start_date + timedelta(days=19*30)  # 19 months
            await conn.execute('''
                INSERT INTO abstinence_tracker (start_date, end_date, current_streak, longest_streak, total_days)
                VALUES ($1, $2, 0, 0, 0)
            ''', start_date, end_date)

@app.on_event("startup")
async def startup():
    await initialize_db()

# Savings Goal Endpoints
@app.get("/savings/goal/", response_model=SavingsGoal)
async def get_savings_goal():
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM savings_goal LIMIT 1")
        if not row:
            raise HTTPException(status_code=404, detail="Savings goal not found")
        return dict(row)

@app.get("/savings/progress/", response_model=SavingsProgress)
async def get_savings_progress():
    pool = await get_db()
    async with pool.acquire() as conn:
        goal = await conn.fetchrow("SELECT * FROM savings_goal LIMIT 1")
        if not goal:
            raise HTTPException(status_code=404, detail="Savings goal not found")
        
        today = date.today()
        total_days = (goal['target_date'] - goal['start_date']).days
        days_passed = (today - goal['start_date']).days
        months_remaining = max(0, (goal['target_date'] - today).days // 30)
        
        expected_progress = days_passed / total_days if total_days > 0 else 0
        actual_progress = goal['current_amount'] / goal['target_amount'] if goal['target_amount'] > 0 else 0
        
        return {
            "progress_percent": round(actual_progress * 100, 2),
            "months_remaining": months_remaining,
            "monthly_savings": goal['monthly_savings'],
            "on_track": actual_progress >= expected_progress
        }

@app.get("/savings/transactions/", response_model=List[dict])
async def get_savings_transactions():
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM savings_transactions ORDER BY date DESC")
        return [dict(row) for row in rows]

@app.post("/savings/transaction/")
async def create_savings_transaction(transaction: SavingsTransaction):
    pool = await get_db()
    async with pool.acquire() as conn:
        # Update current amount in savings goal
        amount = transaction.amount if transaction.type == 'deposit' else -transaction.amount
        await conn.execute('''
            UPDATE savings_goal 
            SET current_amount = current_amount + $1
        ''', amount)
        
        # Record transaction
        await conn.execute('''
            INSERT INTO savings_transactions (amount, type, date, description)
            VALUES ($1, $2, $3, $4)
        ''', transaction.amount, transaction.type, transaction.date, transaction.description)
        
        return {"message": "Transaction recorded successfully"}

# Abstinence Tracker Endpoints
@app.get("/abstinence/tracker/", response_model=AbstinenceTracker)
async def get_abstinence_tracker():
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM abstinence_tracker LIMIT 1")
        if not row:
            raise HTTPException(status_code=404, detail="Abstinence tracker not found")
        return dict(row)

@app.get("/abstinence/progress/", response_model=AbstinenceProgress)
async def get_abstinence_progress():
    pool = await get_db()
    async with pool.acquire() as conn:
        tracker = await conn.fetchrow("SELECT * FROM abstinence_tracker LIMIT 1")
        if not tracker:
            raise HTTPException(status_code=404, detail="Abstinence tracker not found")
        
        total_days = (tracker['end_date'] - tracker['start_date']).days
        days_completed = tracker['total_days']
        days_remaining = max(0, (tracker['end_date'] - date.today()).days)
        
        total_success = await conn.fetchval('''
            SELECT COUNT(*) FROM abstinence_checkins WHERE success = true
        ''')
        
        success_rate = (total_success / days_completed * 100) if days_completed > 0 else 0
        
        return {
            "days_completed": days_completed,
            "total_days_planned": total_days,
            "days_remaining": days_remaining,
            "success_rate": round(success_rate, 2)
        }

@app.get("/abstinence/checkins/", response_model=List[dict])
async def get_abstinence_checkins():
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM abstinence_checkins ORDER BY date DESC")
        return [dict(row) for row in rows]

@app.post("/abstinence/checkin/")
async def create_abstinence_checkin(checkin: AbstinenceCheckIn):
    pool = await get_db()
    async with pool.acquire() as conn:
        # Check if check-in already exists for this date
        existing = await conn.fetchrow("SELECT * FROM abstinence_checkins WHERE date = $1", checkin.date)
        if existing:
            raise HTTPException(status_code=400, detail="Check-in already exists for this date")
        
        # Record check-in
        await conn.execute('''
            INSERT INTO abstinence_checkins (date, success, notes)
            VALUES ($1, $2, $3)
        ''', checkin.date, checkin.success, checkin.notes)
        
        # Update tracker stats
        tracker = await conn.fetchrow("SELECT * FROM abstinence_tracker LIMIT 1")
        if not tracker:
            raise HTTPException(status_code=404, detail="Abstinence tracker not found")
        
        current_streak = 0
        longest_streak = tracker['longest_streak']
        
        if checkin.success:
            # Get previous day's check-in to determine streak
            prev_date = checkin.date - timedelta(days=1)
            prev_checkin = await conn.fetchrow("SELECT * FROM abstinence_checkins WHERE date = $1", prev_date)
            
            if prev_checkin and prev_checkin['success']:
                current_streak = tracker['current_streak'] + 1
            else:
                current_streak = 1
            
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0
        
        await conn.execute('''
            UPDATE abstinence_tracker 
            SET 
                current_streak = $1,
                longest_streak = $2,
                total_days = total_days + 1
        ''', current_streak, longest_streak)
        
        return {"message": "Check-in recorded successfully"}
