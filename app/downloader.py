import os
import shutil
from git import Repo

# Submissions ka folder jahan saare projects download honge
SUBMISSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "submissions"))

def download_student_repo(repo_url: str, student_id: str):
    """
    Student ka GitHub repository link download (clone) karne ka function.
    """
    if not os.path.exists(SUBMISSIONS_DIR):
        os.makedirs(SUBMISSIONS_DIR)
        
    student_folder_path = os.path.join(SUBMISSIONS_DIR, student_id)
    
    # Agar pehle se us student ka folder maujood hai to usay delete karein
    if os.path.exists(student_folder_path):
        print(f"[{student_id}] Purana folder delete ho raha hai...")
        shutil.rmtree(student_folder_path)
        
    print(f"[{student_id}] Downloading repository: {repo_url}...")
    try:
        Repo.clone_from(repo_url, student_folder_path)
        print(f"✅ Success! Project successfully download ho gaya: {student_folder_path}")
        return student_folder_path
    except Exception as e:
        print(f"❌ Error: Repository download nahi ho saki. Wajah: {e}")
        return None