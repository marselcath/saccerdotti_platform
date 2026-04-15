from fastapi import FastAPI, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database
from datetime import datetime
import cloudinary
import cloudinary.uploader
from typing import List

# --- НАСТРОЙКИ CLOUDINARY ---
cloudinary.config( 
    cloud_name = "dxtzqbydm", 
    api_key = "371626272653482", 
    api_secret = "0SoQUMOI04hLrjnIB49bU28dy80", 
    secure = True
)

app = FastAPI(title="Saccerdotti Platform")
templates = Jinja2Templates(directory="templates")

# Создаем таблицы
database.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ИНТЕРФЕЙС УЧЕНИКА ---

@app.get("/", response_class=HTMLResponse, tags=["Интерфейс"])
def show_dashboard(request: Request, db: Session = Depends(get_db)):
    all_courses = db.query(database.Course).all()
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "courses": all_courses}
    )

@app.get("/view/lesson/{lesson_id}", response_class=HTMLResponse, tags=["Интерфейс"])
def view_lesson_page(request: Request, lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(database.Lesson).filter(database.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    course = db.query(database.Course).filter(database.Course.id == lesson.course_id).first()
    all_lessons = db.query(database.Lesson).filter(database.Lesson.course_id == lesson.course_id).all()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user_name": "Марсель",
            "course_title": course.title,
            "lessons": all_lessons,
            "current_lesson": lesson
        }
    )

# ЕДИНАЯ ФУНКЦИЯ ОТПРАВКИ ДЗ (С ФАЙЛАМИ)
@app.post("/submit/{lesson_id}", tags=["Интерфейс"])
async def submit_homework(
    lesson_id: int,
    student_name: str = Form(...),
    comment: str = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    uploaded_urls = []
    
    # Загружаем каждый файл в Cloudinary
    for file in files:
        if file.filename: # Проверяем, что файл вообще прикреплен
            result = cloudinary.uploader.upload(file.file, resource_type="auto")
            uploaded_urls.append(result['secure_url'])
    
    file_links = ", ".join(uploaded_urls)
    
    new_submission = database.StudentSubmission(
        lesson_id=lesson_id,
        student_name=student_name,
        comment=comment,
        files_url=file_links
    )
    db.add(new_submission)
    db.commit()
    
    # После отправки возвращаем на страницу урока
    return RedirectResponse(url=f"/view/lesson/{lesson_id}", status_code=303)

# --- АДМИН-ПАНЕЛЬ ---

@app.post("/courses/", tags=["Админка"])
def create_course(title: str, description: str, db: Session = Depends(get_db)):
    db_course = database.Course(title=title, description=description)
    db.add(db_course)
    db.commit()
    return {"message": "Курс создан", "id": db_course.id}

@app.post("/lessons/", tags=["Админка"])
def add_lesson(
    course_id: int, 
    title: str, 
    video: str, 
    board: str, 
    classwork_pdf: str = None, 
    homework_pdf: str = None, 
    db: Session = Depends(get_db)
):
    new_lesson = database.Lesson(
        course_id=course_id, 
        title=title, 
        video_url=video, 
        board_link=board,
        classwork_pdf=classwork_pdf, # Теперь можно добавлять ссылки на PDF
        homework_pdf=homework_pdf
    )
    db.add(new_lesson)
    db.commit()
    return {"message": "Урок добавлен", "id": new_lesson.id}

@app.get("/admin/submissions", tags=["Админка"])
def view_submissions(db: Session = Depends(get_db)):
    return db.query(database.StudentSubmission).all()

@app.delete("/courses/{course_id}", tags=["Админка"])
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(database.Course).filter(database.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    db.delete(course)
    db.commit()
    return {"message": f"Курс {course_id} удален"}