from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

DATABASE_URL = "sqlite:///./saccerdotti.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- ТАБЛИЦЫ ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True)
    role = Column(String) # "teacher" или "student"

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String) # Например: "Подготовка к ЕГЭ: Математика"
    description = Column(Text)
    
    # Связь: один курс может содержать много уроков
    lessons = relationship("Lesson", back_populates="course")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    video_url = Column(String)
    board_link = Column(String)
    # НОВОЕ: Ссылки на PDF файлы
    classwork_pdf = Column(String, nullable=True)  # Ссылка на классную работу
    homework_pdf = Column(String, nullable=True)   # Ссылка на ДЗ (условия)
    course_id = Column(Integer, ForeignKey("courses.id"))

class Homework(Base):
    __tablename__ = "homeworks"
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    content = Column(Text) # Задания (текст или список задач)
    deadline = Column(DateTime) # Срок сдачи
    
    lesson = relationship("Lesson", back_populates="homework")

class StudentSubmission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    student_name = Column(String)
    comment = Column(String)
    # НОВОЕ: Ссылка на папку или список файлов (например, ссылка на диск)
    files_url = Column(String)