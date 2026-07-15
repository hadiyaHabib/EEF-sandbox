from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
import sys
import os

# Taake imports sahi se kaam karein
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader import download_student_repo
from database import init_db, get_db, Submission
from evaluator import evaluate_project  # Naya evaluator import kiya

# FastAPI Application Instance
app = FastAPI(
    title="Ezitech Engineering Framework (EEF)",
    description="Enterprise AI Engineering Sandbox & Auto Evaluation Platform",
    version="1.0.0"
)

# Templates directory configure karna (HTML files ke liye)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(BASE_DIR, "templates")
if not os.path.exists(templates_dir):
    templates_dir = os.path.join(os.path.dirname(BASE_DIR), "templates")

templates = Jinja2Templates(directory=templates_dir)

# Server start hote hi database tables banayega
@app.on_event("startup")
def on_startup():
    init_db()

# Input Validation Model
class SubmissionRequest(BaseModel):
    student_id: str
    github_url: str

# 1. Base API Welcome Route (Professional HTML dashboard)
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    try:
        return templates.TemplateResponse(request=request, name="index.html")
    except Exception as e:
        return HTMLResponse(content=f"<h3>Template Error (index.html):</h3><p>{str(e)}</p>", status_code=500)

# 2. Submission Route (With Auto Evaluation Scoring)
@app.post("/api/v1/submissions")
def submit_project(request: SubmissionRequest, db: Session = Depends(get_db)):
    if not request.student_id or not request.github_url:
        raise HTTPException(status_code=400, detail="Student ID aur GitHub URL dono zaroori hain!")
    
    # Check karein ke student pehle se exist karta hai ya nahi
    existing_submission = db.query(Submission).filter(Submission.student_id == request.student_id).first()
    if existing_submission:
        raise HTTPException(status_code=400, detail="Is Student ID ki submission pehle se exist karti hai.")

    # Entry with "Downloading" Status
    new_submission = Submission(
        student_id=request.student_id,
        github_url=request.github_url,
        status="Downloading"
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    try:
        # Clone action
        folder_path = download_student_repo(request.github_url, request.student_id)
        
        if folder_path:
            # 🚀 RUN AUTO-EVALUATION ENGINE HERE!
            scores = evaluate_project(folder_path)
            
            # Status aur Scores update karna
            new_submission.status = "Completed"
            new_submission.downloaded_path = folder_path
            new_submission.code_quality_score = scores.get("code_quality", 0)
            new_submission.architecture_score = scores.get("architecture", 0)
            new_submission.feature_score = scores.get("feature_score", 0)
            new_submission.ai_feedback = scores.get("feedback", "No feedback generated.")
            db.commit()
            
            return {
                "status": "success",
                "message": f"Repository clone ho gayi hai! Scores -> Quality: {scores.get('code_quality', 0)}%, Architecture: {scores.get('architecture', 0)}%, Features: {scores.get('feature_score', 0)}%",
                "student_id": request.student_id,
                "saved_path": folder_path
            }
        else:
            raise Exception("Clone path empty returned.")

    except Exception as e:
        # If clone or evaluation fails, change status to Failed
        new_submission.status = "Failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Process fail ho gaya: {str(e)}")

# 3. Get All Submissions API
@app.get("/api/v1/submissions")
def get_all_submissions(db: Session = Depends(get_db)):
    submissions = db.query(Submission).all()
    return submissions

# 4. Leaderboard HTML Page Route (Fixed dict error)
@app.get("/leaderboard", response_class=HTMLResponse)
def get_leaderboard_page(request: Request):
    """
    Leaderboard page render karne ke liye HTML response.
    """
    try:
        return templates.TemplateResponse(request=request, name="leaderboard.html")
    except Exception as e:
        return HTMLResponse(
            content=f"<h3>Template Loading Error!</h3>"
                    f"<p>Exact Error: {str(e)}</p>",
            status_code=500
        )

# 5. Leaderboard Data API
@app.get("/api/v1/leaderboard/data")
def get_leaderboard_data(db: Session = Depends(get_db)):
    """
    Top scores wale students ka data return karega sorting ke sath.
    """
    try:
        # Completed submissions ko fetch karein
        submissions = db.query(Submission).filter(Submission.status == "Completed").all()
        
        leaderboard_list = []
        for sub in submissions:
            quality = sub.code_quality_score or 0
            arch = sub.architecture_score or 0
            feat = sub.feature_score or 0
            
            total_score = quality + arch + feat
            avg_score = round(total_score / 3, 1)
            
            leaderboard_list.append({
                "student_id": sub.student_id,
                "github_url": sub.github_url,
                "avg_score": avg_score,
                "code_quality": quality,
                "architecture": arch,
                "features": feat
            })
        
        # Total average score ke mutabiq descending order mein sort karein
        leaderboard_list.sort(key=lambda x: x["avg_score"], reverse=True)
        
        # Rank numbers assign karein
        for rank, item in enumerate(leaderboard_list, 1):
            item["rank"] = rank
            
        return leaderboard_list[:10]  # Top 10 returns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")