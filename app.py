from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from nicegui import ui
from db import init_db, Author, Book, Reader

# Инициализация базы данных
engine = init_db(echo=False)
SessionLocal = sessionmaker(bind=engine)


@ui.page('/')
async def main_page():
    ui.label('📚 Библиотека').classes('text-3xl font-bold text-center mb-6')

    with ui.column().classes('w-full max-w-4xl mx-auto gap-6 p-4'):
         with ui.tabs().classes('w-full') as tabs:
              tab_add = ui.tab('Добавление книги')
              tab_authors = ui.tab('Авторы')
              tab_readers = ui.tab('Читатели')
              tab_books = ui.tab('Книги')

        with ui.tab_panels(tabs, value=tab_add).classes('w-full'):
            with ui.tab_panel(tab_add):

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
                    True: 'В библиотеке',
                     False: 'На руках'
                },
                value=True
            ).props('outlined')

            ui.button(
                'Добавить книгу',
                icon='add',
                on_click=lambda: add_book()
            ).classes('mt-4')
            
       with ui.tab_panel(tab_authors):
                ui.label('Все авторы').classes('text-2xl font-semibold')
                authors_list = ui.column().classes('w-full gap-3')

            with ui.tab_panel(tab_readers):
                ui.label('Все читатели и их книги на руках').classes('text-2xl font-semibold')
                readers_list = ui.column().classes('w-full gap-3')

            with ui.tab_panel(tab_books):
                ui.label('Все книги').classes('text-2xl font-semibold')

                with ui.row().classes('w-full items-center gap-4'):
                    search_input = ui.input(
                        label='Поиск книги',
                        placeholder='Название книги...',
                    ).classes('flex-grow').props('clearable outlined')

                    ui.button('Искать', icon='search') \
                        .props('flat color=primary') \
                        .on('click', lambda: perform_search(search_input.value))

                results_container = ui.column().classes('w-full gap-4')

                ui.label('Книги по статусу').classes('text-2xl font-semibold mt-8')
                with ui.row().classes('w-full gap-4 items-start'):
                    with ui.card().classes('w-full p-4'):
                        ui.label('📗 В библиотеке').classes('text-xl font-semibold mb-2')
                        library_books_list = ui.column().classes('w-full gap-2')

                    with ui.card().classes('w-full p-4'):
                        ui.label('📕 На руках').classes('text-xl font-semibold mb-2')
                        issued_books_list = ui.column().classes('w-full gap-2')

        # Заполняем список авторов
        with SessionLocal() as session:
            authors = session.scalars(
                select(Author).order_by(Author.name)
            ).all()
            author_select.options = {
                author.id: author.name for author in authors
            }
            if authors:
                author_select.value = authors[0].id

        def reader_name(book: Book) -> str:
            return book.reader.name if book.reader else 'Не указан'

        def status_text(book: Book) -> str:
            if book.is_available:
                return '✅ В библиотеке'
            return f'❌ На руках у: {reader_name(book)}'

        async def add_book():
            if not title_input.value or not author_select.value:
                ui.notify('Заполните все поля', color='negative')
                return

            normalized_title = title_input.value.strip()

            if not normalized_title:
                ui.notify('Введите название книги', color='negative')
                return

            with SessionLocal() as session:
                reader = None
                if not status_select.value:
                    reader = session.scalar(
                        select(Reader).where(Reader.name == 'Не указан')
                    )
                    if reader is None:
                        reader = Reader(name='Не указан')
                        session.add(reader)
                        session.flush()

                book = Book(
                    title=normalized_title,
                    author_id=author_select.value,
                    is_available=status_select.value,
                    reader_id=reader.id if reader else None,
                )
                session.add(book)
                session.commit()

            title_input.value = ''
            status_select.value = True

            ui.notify('Книга добавлена', color='positive')
            await refresh_authors()
            await refresh_readers()
            await refresh_book_lists()

        async def perform_search(query: str):
            results_container.clear()

            if not query or not query.strip():
                with results_container:
                    ui.label('Введите название книги').classes('text-gray-500 italic')
                return

            with results_container:
                with SessionLocal() as session:
                    books = session.scalars(
                        select(Book)
                        .where(Book.title.ilike(f'%{query.strip()}%'))
                        .order_by(Book.title)
                    ).all()

                    if not books:
                        ui.label('Ничего не найдено').classes('text-gray-500 italic')
                        return

                    for book in books:
                        author = session.get(Author, book.author_id)

                        with ui.row().classes('justify-between w-full p-2 border'):
                            ui.label(f'{book.title} — {author.name}')
                            ui.label(status_text(book))

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

        async def refresh_readers():
            readers_list.clear()
            with readers_list:
                with SessionLocal() as session:
                    readers = session.scalars(
                        select(Reader).order_by(Reader.name)
                    ).all()

                    if not readers:
                        ui.label('Читателей пока нет').classes('text-gray-500 italic')
                        return

                    for reader in readers:
                        borrowed_books = session.scalars(
                            select(Book)
                            .where(
                                Book.reader_id == reader.id,
                                Book.is_available.is_(False),
                            )
                            .order_by(Book.title)
                        ).all()

                        with ui.card().classes('w-full p-3'):
                            ui.label(reader.name).classes('text-lg font-semibold')
                            if not borrowed_books:
                                ui.label('Книг на руках нет').classes('text-gray-500 italic')
                            else:
                                for book in borrowed_books:
                                    ui.label(f'{book.title} — {book.author.name}')

        async def refresh_book_lists():
            library_books_list.clear()
            issued_books_list.clear()

            with SessionLocal() as session:
                books_in_library = session.scalars(
                    select(Book)
                    .where(Book.is_available.is_(True))
                    .order_by(Book.title)
                ).all()
                books_on_hands = session.scalars(
                    select(Book)
                    .where(Book.is_available.is_(False))
                    .order_by(Book.title)
                ).all()

                with library_books_list:
                    if not books_in_library:
                        ui.label('Книг в библиотеке нет').classes('text-gray-500 italic')
                    else:
                        for book in books_in_library:
                            ui.label(f'{book.title} — {book.author.name}')

                with issued_books_list:
                    if not books_on_hands:
                        ui.label('Книг на руках нет').classes('text-gray-500 italic')
                    else:
                        for book in books_on_hands:
                            ui.label(
                                f'{book.title} — {book.author.name} (у {reader_name(book)})'
                            )

        async def show_author_books(author: Author):
            with ui.dialog(value=True) as dialog, ui.card():
                ui.label(f'Книги автора: {author.name}').classes('text-xl font-bold')

                with SessionLocal() as session:
                    books = session.scalars(
                        select(Book)
                        .where(Book.author_id == author.id)
                        .order_by(Book.title)
                    ).all()

                    if not books:
                        ui.label('Книг нет')
                    else:
                        for book in books:
                            with ui.row().classes('justify-between w-full items-center'):
                                ui.label(book.title)

                                if book.is_available:
                                    ui.button(
                                        'Выдать',
                                        icon='person_add',
                                        on_click=lambda b=book: open_issue_dialog(b)
                                    ).props('flat color=primary')
                                else:
                                    ui.label(
                                        f'❌ На руках у: {reader_name(book)}'
                                    ).classes('text-red-500')

                ui.button('Закрыть', on_click=dialog.close)

        async def open_issue_dialog(book: Book):
            with ui.dialog() as dialog, ui.card():
                ui.label(f'Выдать книгу: {book.title}') \
                    .classes('text-xl font-bold mb-4')

                last_name = ui.input('Фамилия').props('outlined')
                first_name = ui.input('Имя').props('outlined')
                phone = ui.input('Телефон').props('outlined')
        
        async def issue():
            if not last_name.value or not first_name.value or not phone.value:
                ui.notify('Заполните все поля', color='negative')
                return
               with SessionLocal() as session:
                        full_name = f'{last_name.value.strip()} {first_name.value.strip()}'
                        reader = session.scalar(
                            select(Reader).where(Reader.name == full_name)
                        )
                        if reader is None:
                            reader = Reader(name=full_name)
                            session.add(reader)
                            session.flush()

                        book_in_db = session.get(Book, book.id)
                        if not book_in_db:
                            ui.notify('Книга не найдена', color='negative')
                            return

                        if not book_in_db.is_available:
                            ui.notify(
                                f'Книга уже на руках у: {reader_name(book_in_db)}',
                                color='warning',
                            )
                            return

                        book_in_db.is_available = False
                        book_in_db.reader_id = reader.id
                        session.commit()

                    ui.notify('Книга выдана', color='positive')
                    dialog.close()
                    await refresh_authors()
                    await refresh_readers()
                    await refresh_book_lists()

                ui.button('Выдать книгу', on_click=issue) \
                    .classes('mt-4')

            dialog.open()

        await refresh_authors()
        await refresh_readers()
        await refresh_book_lists()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Библиотека', port=8080, reload=True)