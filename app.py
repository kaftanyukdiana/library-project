from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from nicegui import ui
from create_db import init_db, Author, Book

# Инициализация базы данных
engine = init_db(echo=False)
SessionLocal = sessionmaker(bind=engine)

# Основная страница
@ui.page('/')
async def main_page():
    ui.label('📚 Библиотека').classes('text-3xl font-bold text-center mb-6')

    with ui.column().classes('w-full max-w-4xl mx-auto gap-6 p-4'):
    
    # ─── Добавление новой книги ──────────────────────────
    ui.label('➕ Добавить новую книгу').classes('text-2xl font-semibold')

    with ui.card().classes('w-full p-4 gap-3'):

       title_input = ui.input(
           label='Название книги',
           placeholder='Введите название'
       ).props('outlined')

    (author_select = ui.select(
        label='Автор',
        options=={}
    ).props('outlined')
    with SessionLocal() as session:
    authors = session.scalars(
        select(Author).order_by(Author.name)
    ).all()
    author_select.options = {
        author.name: author.id for author in authors
    }
    
    status_select = ui.select(
        label='Статус',
        options={
            'В наличии': True,
            'Не в наличии': False
        },
        value=True
    ).props('outlined')

    ui.button(
        'Добавить книгу',
        icon='add',
        on_click=lambda: add_book()
    ).classes('mt-4')

        # ─── Поиск книг ───────────────────────────────────────
        with ui.row().classes('w-full items-center gap-4'):
            search_input = ui.input(
                label='Поиск книги',
                placeholder='Название книги...',
            ).classes('flex-grow').props('clearable outlined')

            ui.button('Искать', icon='search').props('flat color=primary') \
                .on('click', lambda: perform_search(search_input.value))

        # Контейнер для результатов поиска
        results_container = ui.column().classes('w-full gap-4')

        # ─── Список всех авторов ──────────────────────────────
        ui.label('Все авторы').classes('text-2xl font-semibold mt-8')

        async def refresh_authors():
            authors_list.clear()
            with authors_list:
                with SessionLocal() as session:
                    authors = session.scalars(
                        select(Author).order_by(Author.name)
                    ).all()

                    if not authors:
                        ui.label('Авторов пока нет в базе').classes('text-gray-500 italic')
                        return

                    for author in authors:
                        with ui.card().classes('w-full cursor-pointer hover:bg-gray-100 transition'):
                            ui.label(author.name).classes('text-xl font-medium')
                            ui.button('Посмотреть книги', icon='book').props('flat color=primary') \
                                .on('click', lambda a=author: show_author_books(a))

        authors_list = ui.column().classes('w-full gap-3')

        # Первоначальная загрузка авторов
        await refresh_authors()

        ui.separator().classes('my-8')

    # Функция поиска (только по книгам)
        async def perform_search(query: str):
        async def add_book():
    if not title_input.value or not author_select.value:
        ui.notify('Заполните все поля', color='negative')
        return

    with SessionLocal() as session:
        new_book = Book(
            title=title_input.value,
            author_id=author_select.value,
            is_available=status_select.value
        )
        session.add(new_book)
        session.commit()

    title_input.value = ''
    status_select.value = True

        ui.notify('Книга успешно добавлена', color='positive')
        
        if not query.strip():
            results_container.clear()
            with results_container:
                ui.label('Введите название книги для поиска').classes('text-gray-500 italic py-6 text-center')
            return

        results_container.clear()
        with results_container:
            with SessionLocal() as session:
                # Поиск книг по названию (регистронезависимо)
                books = session.scalars(
                    select(Book)
                    .where(Book.title.ilike(f'%{query}%'))
                    .order_by(Book.title)
                ).all()

                if not books:
                    ui.label(f'Книги с "{query}" не найдены').classes('text-gray-500 italic py-6 text-center')
                    return

                ui.label('📖 Найденные книги:').classes('text-xl font-semibold mt-4')
                with ui.column().classes('w-full gap-3'):
                    for book in books:
                        author = session.get(Author, book.author_id)
                        if book.is_available:
                            status = "✅ В наличии"
                            color = "text-green-600"
                        else:
                            user = book.user.name if book.user else "неизвестно"
                            status = f"❌ На руках у {user}"
                            color = "text-red-600"

                        with ui.row().classes('items-center justify-between w-full p-3 border rounded-lg'):
                            ui.label(f"{book.title} — {author.name if author else 'Автор неизвестен'}") \
                                .classes('text-lg font-medium')
                            ui.label(status).classes(f'font-semibold {color}')

    # Показ книг автора (модальное окно)
    async def show_author_books(author: Author):
        with ui.dialog(value=True).props('persistent') as dialog, ui.card().classes('w-full max-w-2xl'):
            ui.label(f'📚 Книги автора: {author.name}').classes('text-2xl font-bold mb-4')

            with SessionLocal() as session:
                books = session.scalars(
                    select(Book).where(Book.author_id == author.id).order_by(Book.title)
                ).all()

                if not books:
                    ui.label('У этого автора пока нет книг').classes('text-gray-500 italic py-8 text-center')
                else:
                    with ui.column().classes('w-full gap-3'):
                        for book in books:
                            status = "✅ В наличии" if book.is_available else "❌ Нет в наличии"
                            color = "text-green-600" if book.is_available else "text-red-600"
                            with ui.row().classes('items-center justify-between w-full p-3 border rounded-lg'):
                                ui.label(book.title).classes('text-lg font-medium')
                                ui.label(status).classes(f'font-semibold {color}')

            ui.separator()
            ui.button('Закрыть', icon='close').props('flat color=primary') \
                .on('click', dialog.close)


# Запуск приложения
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='Библиотека',
        favicon='📚',
        dark=False,
        port=8080,
        reload=True
    )