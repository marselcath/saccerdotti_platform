from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./saccerdotti_final.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Course(Base):
    __tablename__ = "courses"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    
    # Связь с уроками: если удаляем курс, удаляются и уроки
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    video_url = Column(String)
    board_link = Column(String)
    meeting_link = Column(String, nullable=True) # Поле для онлайн-занятий
    classwork_pdf = Column(String, nullable=True) # Ссылка на PDF классной
    homework_pdf = Column(String, nullable=True)  # Ссылка на PDF домашки
    course_id = Column(Integer, ForeignKey("courses.id"))
    
    # Связи
    course = relationship("Course", back_populates="lessons")
    submissions = relationship("StudentSubmission", back_populates="lesson")

class StudentSubmission(Base):
    __tablename__ = "submissions"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    student_name = Column(String)
    comment = Column(Text, nullable=True)
    files_url = Column(Text) # Здесь хранятся ссылки из Cloudinary
    
    lesson = relationship("Lesson", back_populates="submissions")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Integer, default=0) # 1 для тебя, 0 для учеников

