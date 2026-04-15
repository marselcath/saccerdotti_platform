import os
from fastapi import FastAPI, Depends, HTTPException, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database
import cloudinary
import cloudinary.uploader
from typing import List

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Настройка Cloudinary
cloudinary.config(
    cloud_name="dxtzqbydm",
    api_key="371626272653482",
    api_secret="0SoQUMOI04hLrjnIB49bU28dy80"
)

# Функция для получения сессии БД
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- КЛИЕНТСКАЯ ЧАСТЬ (Сайт) ---

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    courses = db.query(database.Course).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "courses": courses})

@app.get("/view/lesson/{lesson_id}", response_class=HTMLResponse)
def show_lesson(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    lesson = db.query(database.Lesson).filter(database.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    # Получаем все уроки этого курса для бокового меню
    lessons = db.query(database.Lesson).filter(database.Lesson.course_id == lesson.course_id).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_lesson": lesson,
        "lessons": lessons,
        "user_name": "Марсель"  # Пока захардкодим, пока нет регистрации
    })

# --- АДМИН-ПАНЕЛЬ (Управление) ---

@app.post("/courses/", tags=["Админка"])
def add_course(title: str, description: str, db: Session = Depends(get_db)):
    new_course = database.Course(title=title, description=description)
    db.add(new_course)
    db.commit()
    return {"message": "Курс создан", "id": new_course.id}

@app.post("/lessons/", tags=["Админка"])
def add_lesson(
    course_id: int, title: str, video: str, board: str, 
    meeting: str = None, classwork_pdf: str = None, homework_pdf: str = None, 
    db: Session = Depends(get_db)
):
    new_lesson = database.Lesson(
        course_id=course_id, title=title, video_url=video, 
        board_link=board, meeting_link=meeting,
        classwork_pdf=classwork_pdf, homework_pdf=homework_pdf
    )
    db.add(new_lesson)
    db.commit()
    return {"message": "Урок добавлен", "id": new_lesson.id}

@app.put("/lessons/{lesson_id}", tags=["Админка"])
def update_lesson(
    lesson_id: int, title: str = None, video: str = None, board: str = None,
    meeting: str = None, classwork_pdf: str = None, homework_pdf: str = None,
    db: Session = Depends(get_db)
):
    lesson = db.query(database.Lesson).filter(database.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    if title: lesson.title = title
    if video: lesson.video_url = video
    if board: lesson.board_link = board
    if meeting: lesson.meeting_link = meeting
    if classwork_pdf: lesson.classwork_pdf = classwork_pdf
    if homework_pdf: lesson.homework_pdf = homework_pdf
    
    db.commit()
    return {"message": f"Урок {lesson_id} успешно обновлен"}

@app.delete("/lessons/{lesson_id}", tags=["Админка"])
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(database.Lesson).filter(database.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    db.delete(lesson)
    db.commit()
    return {"message": "Урок удален"}

# --- ПРИЕМ ЗАДАНИЙ ---

@app.post("/submit/{lesson_id}")
async def submit_homework(
    lesson_id: int, 
    student_name: str = Form(...), 
    comment: str = Form(None), 
    files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db)
):
    file_urls = []
    for file in files:
        result = cloudinary.uploader.upload(file.file)
        file_urls.append(result['secure_url'])
    
    new_submission = database.StudentSubmission(
        lesson_id=lesson_id,
        student_name=student_name,
        comment=comment,
        files_url=",".join(file_urls)
    )
    db.add(new_submission)
    db.commit()
    return RedirectResponse(url=f"/view/lesson/{lesson_id}", status_code=303)