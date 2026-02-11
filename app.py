from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from nicegui import ui
from create_db import init_db, Author, Book

# Инициализация базы данных
engine = init_db(echo=False)
SessionLocal = sessionmaker(bind=engine)


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

            author_select = ui.select(
                label='Автор',
                options={}
            ).props('outlined')

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

        # Заполняем список авторов
        with SessionLocal() as session:
            authors = session.scalars(
                select(Author).order_by(Author.name)
            ).all()
            author_select.options = {
                author.name: author.id for author in authors
            }

        # ─── Поиск книг ───────────────────────────────────────
        with ui.row().classes('w-full items-center gap-4'):
            search_input = ui.input(
                label='Поиск книги',
                placeholder='Название книги...',
            ).classes('flex-grow').props('clearable outlined')

            ui.button('Искать', icon='search') \
                .props('flat color=primary') \
                .on('click', lambda: perform_search(search_input.value))

        results_container = ui.column().classes('w-full gap-4')

        # ─── Список авторов ──────────────────────────────────
        ui.label('Все авторы').classes('text-2xl font-semibold mt-8')

        authors_list = ui.column().classes('w-full gap-3')

        async def refresh_authors():
            authors_list.clear()
            with authors_list:
                with SessionLocal() as session:
                    authors = session.scalars(
                        select(Author).order_by(Author.name)
                    ).all()

                    if not authors:
                        ui.label('Авторов пока нет').classes('text-gray-500 italic')
                        return

                    for author in authors:
                        with ui.card().classes('w-full'):
                            ui.label(author.name).classes('text-xl font-medium')
                            ui.button(
                                'Посмотреть книги',
                                icon='book'
                            ).props('flat color=primary') \
                             .on('click', lambda a=author: show_author_books(a))

        await refresh_authors()

        # ─── ФУНКЦИИ ──────────────────────────────────────────

        async def add_book():
            if not title_input.value or not author_select.value:
                ui.notify('Заполните все поля', color='negative')
                return

            with SessionLocal() as session:
                book = Book(
                    title=title_input.value,
                    author_id=author_select.value,
                    is_available=status_select.value
                )
                session.add(book)
                session.commit()

            title_input.value = ''
            status_select.value = True

            ui.notify('Книга добавлена', color='positive')
            await refresh_authors()

        async def perform_search(query: str):
            results_container.clear()

            if not query.strip():
                with results_container:
                    ui.label('Введите название книги').classes('text-gray-500 italic')
                return

            with results_container:
                with SessionLocal() as session:
                    books = session.scalars(
                        select(Book)
                        .where(Book.title.ilike(f'%{query}%'))
                        .order_by(Book.title)
                    ).all()

                    if not books:
                        ui.label('Ничего не найдено').classes('text-gray-500 italic')
                        return

                    for book in books:
                        author = session.get(Author, book.author_id)
                        status = '✅ В наличии' if book.is_available else '❌ Нет в наличии'

                        with ui.row().classes('justify-between w-full p-2 border'):
                            ui.label(f'{book.title} — {author.name}')
                            ui.label(status)

        async def show_author_books(author: Author):
            with ui.dialog(value=True) as dialog, ui.card():
                ui.label(f'Книги автора: {author.name}').classes('text-xl font-bold')

                with SessionLocal() as session:
                    books = session.scalars(
                        select(Book).where(Book.author_id == author.id)
                    ).all()

                    if not books:
                        ui.label('Книг нет')
                    else:
                        for book in books:
                            ui.label(book.title)

                ui.button('Закрыть', on_click=dialog.close)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Библиотека', port=8080, reload=True)