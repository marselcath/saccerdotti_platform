import os
from fastapi import FastAPI, Depends, HTTPException, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database
import cloudinary
import cloudinary.uploader
from typing import List
from passlib.context import CryptContext

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Хеширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Инициализация БД
database.Base.metadata.create_all(bind=database.engine)

# Настройка Cloudinary
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

# --- МАРШРУТЫ ---

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    courses = db.query(database.Course).all()
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"courses": courses})

@app.get("/view/lesson/{lesson_id}", response_class=HTMLResponse)
def show_lesson(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    lesson = db.query(database.Lesson).filter(database.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    lessons = db.query(database.Lesson).filter(database.Lesson.course_id == lesson.course_id).all()
    return templates.TemplateResponse(request=request, name="index.html", context={
        "current_lesson": lesson, "lessons": lessons, "user_name": "Марсель"
    })

# --- РЕГИСТРАЦИЯ И ВХОД ---

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.post("/register")
def register_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        existing_user = db.query(database.User).filter(database.User.username == username).first()
        if existing_user:
            return HTMLResponse(content="<h3>Пользователь уже существует</h3><a href='/register'>Назад</a>", status_code=400)
        
        hashed = pwd_context.hash(password)
        new_user = database.User(username=username, hashed_password=hashed)
        db.add(new_user)
        db.commit()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        # Если база данных "ругнется", мы увидим причину
        return HTMLResponse(content=f"<h3>Ошибка БД: {e}</h3>", status_code=500)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return HTMLResponse(content="<h3>Неверный логин или пароль</h3><a href='/login'>Назад</a>", status_code=401)
    return RedirectResponse(url="/", status_code=303)

# --- ПРИЕМ ЗАДАНИЙ ---

@app.post("/submit/{lesson_id}")
async def submit_homework(lesson_id: int, student_name: str = Form(...), comment: str = Form(None), files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    file_urls = []
    for file in files:
        result = cloudinary.uploader.upload(file.file)
        file_urls.append(result['secure_url'])
    new_submission = database.StudentSubmission(lesson_id=lesson_id, student_name=student_name, comment=comment, files_url=",".join(file_urls))
    db.add(new_submission)
    db.commit()
    return RedirectResponse(url=f"/view/lesson/{lesson_id}", status_code=303)