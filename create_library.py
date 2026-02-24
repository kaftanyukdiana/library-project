from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    select
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from nicegui import ui
from datetime import datetime
from sqlalchemy import DateTime

Base = declarative_base()

# =======================
# МОДЕЛИ БАЗЫ ДАННЫХ
# =======================

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    books = relationship("Book", back_populates="author")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    books = relationship("Book", back_populates="user")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    # если True — книга в наличии
    # если False — книга на руках
    is_available = Column(Boolean, default=True)

    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    author = relationship("Author", back_populates="books")

    # пользователь, у которого книга на руках
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="books")
    
    
class Borrowing(Base):
    __tablename__ = "borrowings"

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    borrowed_at = Column(DateTime, default=datetime.utcnow)
    returned_at = Column(DateTime, nullable=True)

    book = relationship("Book")

# =======================
# ИНИЦИАЛИЗАЦИЯ БД
# =======================

engine = create_engine("sqlite:///db.sqlite")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

session = Session()

if not session.execute(select(Author).limit(1)).scalar_one_or_none():
    authors = {
        "Лев Толстой": Author(name="Лев Толстой"),
        "Фёдор Достоевский": Author(name="Фёдор Достоевский"),
        "Антон Чехов": Author(name="Антон Чехов"),
        "Александр Пушкин": Author(name="Александр Пушкин"),
    }

    users = {
        "Иванов И.И.": User(name="Иванов И.И."),
        "Петров П.П.": User(name="Петров П.П."),
    }

    session.add_all(authors.values())
    session.add_all(users.values())
    session.flush()

    books = [
        Book(
            title="Евгений Онегин",
            author=authors["Александр Пушкин"],
            is_available=False,
            user=users["Иванов И.И."]
        ),
        Book(
            title="Война и мир",
            author=authors["Лев Толстой"],
            is_available=True
        )
    ]

    session.add_all(books)
    session.commit()


# =======================
# ПУНКТ 1
# UI ВОЗМОЖНОСТЬ ДОБАВЛЕНИЯ КНИГ
# =======================

ui.label("➕ Добавление новой книги").classes("text-h5")

title_input = ui.input("Название книги")
author_select = ui.select(
    {a.name: a for a in session.execute(select(Author)).scalars()},
    label="Автор"
)

status_select = ui.select(
    {True: "В наличии", False: "На руках"},
    label="Статус книги",
    value=True
)

user_select = ui.select(
    {u.name: u for u in session.execute(select(User)).scalars()},
    label="Читатель (если книга на руках)"
)

def add_book():
    book = Book(
        title=title_input.value,
        author=author_select.value,
        is_available=status_select.value,
        user=None if status_select.value else user_select.value
    )
    session.add(book)
    session.commit()
    ui.notify("Книга добавлена")

ui.button("Добавить книгу", on_click=add_book)

ui.separator()

# =======================
# ПУНКТ 2
# ОТОБРАЖЕНИЕ КНИГ СО СТАТУСОМ
# (в наличии / на руках + кто взял)
# =======================

ui.label("📚 Список всех книг").classes("text-h5")

def refresh_books():
    table_rows.clear()
    for book in session.execute(select(Book)).scalars():
        status = (
            "В наличии"
            if book.is_available
            else f"На руках у {book.user.name}"
        )
        table_rows.append({
            "title": book.title,
            "author": book.author.name,
            "status": status
        })

table_rows = []

ui.table(
    columns=[
        {"name": "title", "label": "Название", "field": "title"},
        {"name": "author", "label": "Автор", "field": "author"},
        {"name": "status", "label": "Статус", "field": "status"},
    ],
    rows=table_rows
)

ui.button("Обновить список книг", on_click=refresh_books)

ui.separator()

# =======================
# ПУНКТ 3
# ВЫБОР ПОЛЬЗОВАТЕЛЯ И ПРОСМОТР
# ВСЕХ КНИГ, КОТОРЫЕ У НЕГО НА РУКАХ
# =======================

ui.label("👤 Книги выбранного читателя").classes("text-h5")

user_filter = ui.select(
    {u.name: u for u in session.execute(select(User)).scalars()},
    label="Выберите читателя"
)

user_books_rows = []

def show_user_books():
    user_books_rows.clear()
    books = session.execute(
        select(Book).where(Book.user == user_filter.value)
    ).scalars()

    for book in books:
        user_books_rows.append({
            "title": book.title,
            "author": book.author.name
        })

ui.table(
    columns=[
        {"name": "title", "label": "Название", "field": "title"},
        {"name": "author", "label": "Автор", "field": "author"},
    ],
    rows=user_books_rows
)

ui.button("Показать книги читателя", on_click=show_user_books)
ui.run()