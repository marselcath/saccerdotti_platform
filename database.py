from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./saccerdotti.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    video_url = Column(String)
    board_link = Column(String)
    meeting_link = Column(String, nullable=True) # Поле для онлайн-уроков
    classwork_pdf = Column(String, nullable=True)
    homework_pdf = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    
    course = relationship("Course", back_populates="lessons")
    submissions = relationship("StudentSubmission", back_populates="lesson")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    # Связь с уроками
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    video_url = Column(String)
    board_link = Column(String)
    classwork_pdf = Column(String, nullable=True) # Ссылка на PDF классной
    homework_pdf = Column(String, nullable=True)  # Ссылка на PDF домашки
    course_id = Column(Integer, ForeignKey("courses.id"))
    
    # ТЕ САМЫЕ СВЯЗИ, КОТОРЫХ НЕ ХВАТАЛО:
    course = relationship("Course", back_populates="lessons")
    submissions = relationship("StudentSubmission", back_populates="lesson")

class StudentSubmission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    student_name = Column(String)
    comment = Column(Text, nullable=True)
    files_url = Column(Text) # Здесь будут храниться ссылки из Cloudinary
    
    lesson = relationship("Lesson", back_populates="submissions")