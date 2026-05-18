from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import tempfile
import os

try:
    from config import settings
except ImportError:
    from app.config import settings

try:
    from database.session import Base, engine
except ImportError:
    from app.database.session import Base, engine

from app.services.resume__service import parse_resume, create_final_profile
from app.services.job_service import calculate_match
from app.services.email_service import EmailService
from app.schemas.user import FinalUserProfile
from app.schemas.job import JobMatchRequest, JobMatchResult
from app.schemas.email import EmailRequest, EmailResponse, EmailSendRequest
from app.services.gmass_transactional_service import GMassTransactionalService

from app.routers.tracking import router as tracking_router
from app.routers.webhook import router as webhook_router
from app.routers.jobs import router as jobs_router
from app.routers.company import router as company_router
from app.routers.analytics import router as analytics_router

from app.scheduler import start_scheduler, scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Server Startup")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database creation failed or skipped: {e}")
    start_scheduler()
    yield
    # Shutdown
    print("Server Shutdown")
    scheduler.shutdown()

app = FastAPI(
    title="AI-Assisted Smart Job Outreach System",
    description=settings.PROJECT_DESCRIPTION if 'settings' in globals() and hasattr(settings, 'PROJECT_DESCRIPTION') else "AI-Assisted Smart Job Outreach System",
    version=settings.PROJECT_VERSION if 'settings' in globals() and hasattr(settings, 'PROJECT_VERSION') else "1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Import and include routers from HEAD
try:
    from apis import auth as auth_router
    from apis import users as user_router
    from apis import companies as company_router_head
    from apis import emails as email_router_head
except ImportError:
    from app.apis import auth as auth_router
    from app.apis import users as user_router
    from app.apis import companies as company_router_head
    from app.apis import emails as email_router_head

app.include_router(auth_router.router, tags=["Authentication"])
app.include_router(user_router.router, tags=["Users"])
app.include_router(company_router_head.router, tags=["Companies (Legacy)"])
app.include_router(email_router_head.router, tags=["Emails (Legacy)"])

# Register routers from main
app.include_router(tracking_router)
app.include_router(webhook_router)
app.include_router(jobs_router)
app.include_router(company_router)
app.include_router(analytics_router)

@app.get("/")
async def root():
    """Serve the main unified dashboard."""
    return FileResponse("index.html")

@app.post("/api/uploadfile/", response_model=FinalUserProfile)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume PDF to extract candidate profile data using NLP and spaCy.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PDF files are allowed."
        )
    
    temp_file_path = None
    try:
        # Create a temporary file to save the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 1. High-level parser logic
        user_profile = await parse_resume(temp_file_path)
        
        # 2. Final schema mapping
        final_profile = create_final_profile(user_profile)

        # 3. Native Pydantic response (FastAPI handles serialization automatically)
        return final_profile

    except Exception as e:
        # Catch and report parsing or layout errors
        print(f"Error processing resume: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while parsing the resume: {str(e)}"
        )
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as cleanup_err:
                print(f"Warning: Failed to delete temp file {temp_file_path}: {cleanup_err}")

@app.post("/api/match/", response_model=JobMatchResult)
async def match_job(request: JobMatchRequest):
    """
    Match a FinalUserProfile against a Job Description text with weighted scoring.
    """
    try:
        result = calculate_match(request.user_profile, request.jd_text)
        return result
    except Exception as e:
        print(f"Error matching job: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred during job matching: {str(e)}"
        )

@app.post("/api/generate-email/", response_model=EmailResponse)
async def generate_email(request: EmailRequest):
    """
    Generate a personalized outreach email using LLM based on profile and JD.
    """
    try:
        result = await EmailService.generate_email(request)
        return result
    except Exception as e:
        print(f"Error generating email: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while generating the email: {str(e)}"
        )

from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import OutreachEmail, User, JobListing
from fastapi import Depends

@app.post("/api/send-email/")
async def send_email(request: EmailSendRequest, db: AsyncSession = Depends(get_db)):
    """
    Send an email via GMass Transactional API and store in database.
    """
    try:
        # 1. Send the email
        result = await GMassTransactionalService.send_email(
            recipient_email=request.recipient_email,
            subject=request.subject,
            body=request.body,
            sender_email=request.sender_email,
        )
        
        # 2. Extract transactional ID from result (depends on GMass response format)
        t_id = result.get("TransactionalEmailId") or result.get("transactionalEmailId")
        
        # 3. Store in DB
        outreach = OutreachEmail(
            transactional_id=str(t_id) if t_id else None,
            recipient_email=request.recipient_email,
            subject=request.subject,
            body=request.body,
            strategy="N/A",
            status="SENT"
        )
        db.add(outreach)
        await db.commit()
        
        return result
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )

# Static files at /static (NOT "/" — that would intercept API routes)
app.mount("/static", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
