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

Base = declarative_base()

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)

    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    author = relationship("Author", back_populates="books")


def init_db(db_url: str = "sqlite:///db.sqlite", echo: bool = False):
    """
    Создает таблицы и наполняет БД начальными данными,
    если они еще не существуют.
    """
    engine = create_engine(db_url, echo=echo)
    Session = sessionmaker(bind=engine)

    Base.metadata.create_all(engine)

    session = Session()

    try:
        author_exists = session.execute(
            select(Author).limit(1)
        ).scalar_one_or_none()

        if author_exists:
            print("📚 База данных уже инициализирована — пропускаем заполнение")
            return engine

        print("🛠 Инициализация базы данных...")

        authors = {
            "Лев Толстой": Author(name="Лев Толстой"),
            "Фёдор Достоевский": Author(name="Фёдор Достоевский"),
            "Антон Чехов": Author(name="Антон Чехов"),
            "Александр Пушкин": Author(name="Александр Пушкин"),
            "Николай Гоголь": Author(name="Николай Гоголь"),
        }

        session.add_all(authors.values())
        session.flush()

        books = [
            Book(title="Война и мир", author=authors["Лев Толстой"], is_available=True),
            Book(title="Анна Каренина", author=authors["Лев Толстой"], is_available=False),
            Book(title="Воскресение", author=authors["Лев Толстой"], is_available=True),

            Book(title="Преступление и наказание", author=authors["Фёдор Достоевский"], is_available=True),
            Book(title="Идиот", author=authors["Фёдор Достоевский"], is_available=True),
            Book(title="Братья Карамазовы", author=authors["Фёдор Достоевский"], is_available=False),
            Book(title="Бесы", author=authors["Фёдор Достоевский"], is_available=True),

            Book(title="Вишнёвый сад", author=authors["Антон Чехов"], is_available=True),
            Book(title="Чайка", author=authors["Антон Чехов"], is_available=False),
            Book(title="Дама с собачкой", author=authors["Антон Чехов"], is_available=True),

            Book(title="Евгений Онегин", author=authors["Александр Пушкин"], is_available=True),
            Book(title="Капитанская дочка", author=authors["Александр Пушкин"], is_available=True),
            Book(title="Борис Годунов", author=authors["Александр Пушкин"], is_available=False),

            Book(title="Мёртвые души", author=authors["Николай Гоголь"], is_available=True),
            Book(title="Ревизор", author=authors["Николай Гоголь"], is_available=True),
            Book(title="Шинель", author=authors["Николай Гоголь"], is_available=False),
            Book(title="Нос", author=authors["Николай Гоголь"], is_available=True),

            Book(title="Детство", author=authors["Лев Толстой"], is_available=True),
            Book(title="Отрочество", author=authors["Лев Толстой"], is_available=True),
            Book(title="Юность", author=authors["Лев Толстой"], is_available=False),
        ]

        session.add_all(books)
        session.commit()

        print("✅ База данных успешно создана и заполнена")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return engine