import os
import bcrypt
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

database.Base.metadata.create_all(bind=database.engine)

cloudinary.config(
    cloud_name="dxtzqbydm",
    api_key="371626272653482",
    api_secret="0SoQUMOI04hLrjnIB49bU28dy80"
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False

# --- ОБЫЧНЫЕ МАРШРУТЫ ---

@app.get("/", response_class=HTMLResponse, tags=["Просмотр"])
def dashboard(request: Request, db: Session = Depends(get_db)):
    courses = db.query(database.Course).all()
    # Добавляем user_name для совместимости с шаблонами
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"courses": courses, "user_name": "Марсель"})

@app.get("/view/lesson/{lesson_id}", response_class=HTMLResponse, tags=["Просмотр"])
def show_lesson(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    lesson = db.query(database.Lesson).filter(database.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    lessons = db.query(database.Lesson).filter(database.Lesson.course_id == lesson.course_id).all()
    return templates.TemplateResponse(request=request, name="index.html", context={
        "current_lesson": lesson, "lessons": lessons, "user_name": "Марсель"
    })

# --- АДМИНКА (ВЫДЕЛЕННЫЙ БЛОК) ---

@app.post("/courses/", tags=["Админка: Курсы"])
def add_course(title: str, description: str = None, db: Session = Depends(get_db)):
    new_course = database.Course(title=title, description=description)
    db.add(new_course)
    db.commit()
    return {"message": f"Курс создан с ID: {new_course.id}"}

@app.post("/courses/edit/{course_id}", tags=["Админка: Курсы"])
def edit_course(course_id: int, title: str, description: str, db: Session = Depends(get_db)):
    course = db.query(database.Course).filter(database.Course.id == course_id).first()
    if not course: raise HTTPException(status_code=404)
    course.title, course.description = title, description
    db.commit()
    return {"message": "Курс обновлен"}

@app.delete("/courses/{course_id}", tags=["Админка: Курсы"])
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(database.Course).filter(database.Course.id == course_id).first()
    if not course: raise HTTPException(status_code=404)
    db.delete(course)
    db.commit()
    return {"message": "Курс удален"}

@app.post("/lessons/", tags=["Админка: Уроки"])
def add_lesson(course_id: int, title: str, video: str, board: str, meeting_link: str = None, classwork_pdf: str = None, homework_pdf: str = None, db: Session = Depends(get_db)):
    # Здесь добавлено поле meeting_link, которое раньше терялось
    new_lesson = database.Lesson(
        course_id=course_id, title=title, video_url=video, 
        board_link=board, meeting_link=meeting_link, 
        classwork_pdf=classwork_pdf, homework_pdf=homework_pdf
    )
    db.add(new_lesson)
    db.commit()
    return {"message": "Урок добавлен"}

@app.post("/lessons/edit/{lesson_id}", tags=["Админка: Уроки"])
def edit_lesson(lesson_id: int, title: str, video: str, board: str, meeting_link: str = None, db: Session = Depends(get_db)):
    lesson = db.query(database.Lesson).filter(database.Lesson.id == lesson_id).first()
    if not lesson: raise HTTPException(status_code=404)
    lesson.title, lesson.video_url, lesson.board_link, lesson.meeting_link = title, video, board, meeting_link
    db.commit()
    return {"message": "Урок обновлен"}

@app.delete("/lessons/{lesson_id}", tags=["Админка: Уроки"])
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(database.Lesson).filter(database.Lesson.id == lesson_id).first()
    if not lesson: raise HTTPException(status_code=404)
    db.delete(lesson)
    db.commit()
    return {"message": "Урок удален"}

# --- РЕГИСТРАЦИЯ И ВХОД ---

@app.get("/register", response_class=HTMLResponse, tags=["Аккаунт"])
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.post("/register", tags=["Аккаунт"])
def register_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        existing_user = db.query(database.User).filter(database.User.username == username).first()
        if existing_user: return HTMLResponse(content="<h3>Логин занят</h3>", status_code=400)
        new_user = database.User(username=username, hashed_password=hash_password(password))
        db.add(new_user)
        db.commit()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        return HTMLResponse(content=f"<h3>Ошибка: {e}</h3>", status_code=500)

@app.get("/login", response_class=HTMLResponse, tags=["Аккаунт"])
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login", tags=["Аккаунт"])
def login_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return HTMLResponse(content="<h3>Ошибка входа</h3>", status_code=401)
    return RedirectResponse(url="/", status_code=303)

@app.post("/submit/{lesson_id}", tags=["Прочее"])
async def submit_homework(lesson_id: int, student_name: str = Form(...), comment: str = Form(None), files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    file_urls = []
    for file in files:
        result = cloudinary.uploader.upload(file.file)
        file_urls.append(result['secure_url'])
    new_submission = database.StudentSubmission(lesson_id=lesson_id, student_name=student_name, comment=comment, files_url=",".join(file_urls))
    db.add(new_submission)
    db.commit()
    return RedirectResponse(url=f"/view/lesson/{lesson_id}", status_code=303)