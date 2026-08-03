from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import json
import time
from datetime import datetime
from pythonjsonlogger import jsonlogger
import uuid

app = FastAPI()

# ===== JSON Logging Setup =====
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create console handler with JSON formatter
logHandler = logging.FileHandler("logs/app.log")
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Also log to console for debugging
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

# ===== Data Models =====
class User(BaseModel):
    name: str
    email: str

class Job(BaseModel):
    title: str
    company: str
    location: str

# ===== Routes =====
@app.get("/health")
async def health_check():
    logger.info("Health check called", extra={"endpoint": "/health", "status": "ok"})
    return {"status": "healthy"}

@app.post("/users")
async def create_user(user: User):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "User creation initiated",
            extra={
                "request_id": request_id,
                "user_email": user.email,
                "endpoint": "/users",
                "method": "POST"
            }
        )
        
        # Simulate processing
        time.sleep(0.1)
        
        elapsed = time.time() - start_time
        logger.info(
            "User created successfully",
            extra={
                "request_id": request_id,
                "user_email": user.email,
                "response_time_ms": elapsed * 1000,
                "status_code": 201
            }
        )
        
        return {"id": request_id, "name": user.name, "email": user.email}
    
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "User creation failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "response_time_ms": elapsed * 1000,
                "status_code": 500
            }
        )
        raise HTTPException(status_code=500, detail="Failed to create user")

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(
        "Fetching user",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "endpoint": "/users/{user_id}",
            "method": "GET"
        }
    )
    
    if user_id == "999":
        elapsed = time.time() - start_time
        logger.warning(
            "User not found",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "status_code": 404,
                "response_time_ms": elapsed * 1000
            }
        )
        raise HTTPException(status_code=404, detail="User not found")
    
    elapsed = time.time() - start_time
    logger.info(
        "User retrieved",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "status_code": 200,
            "response_time_ms": elapsed * 1000
        }
    )
    return {"id": user_id, "name": "John Doe", "email": "john@example.com"}

@app.post("/jobs")
async def post_job(job: Job):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(
        "Job posting created",
        extra={
            "request_id": request_id,
            "job_title": job.title,
            "company": job.company,
            "location": job.location,
            "endpoint": "/jobs",
            "method": "POST",
            "status_code": 201,
            "response_time_ms": (time.time() - start_time) * 1000
        }
    )
    
    return {
        "id": request_id,
        "title": job.title,
        "company": job.company,
        "location": job.location
    }

@app.get("/jobs")
async def list_jobs():
    request_id = str(uuid.uuid4())
    
    logger.info(
        "Jobs listed",
        extra={
            "request_id": request_id,
            "endpoint": "/jobs",
            "method": "GET",
            "count": 5,
            "status_code": 200
        }
    )
    
    return [
        {"id": "1", "title": "DevOps Engineer", "company": "TechCorp"},
        {"id": "2", "title": "SRE", "company": "CloudInc"},
        {"id": "3", "title": "Platform Engineer", "company": "StartupXYZ"},
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
