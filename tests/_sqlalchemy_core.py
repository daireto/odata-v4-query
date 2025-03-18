from sqlalchemy import JSON, ForeignKey, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()
    addresses: Mapped[list[str]] = mapped_column(JSON)
    posts: Mapped[list['Post']] = relationship(back_populates='user')


class Post(Base):
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column()
    body: Mapped[str] = mapped_column()
    rating: Mapped[int] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='posts')


def get_engine():
    engine = create_engine('sqlite://', echo=False)
    Base.metadata.create_all(engine)
    return engine


def seed_users(session: Session):
    session.add_all(
        [
            User(
                name='John',
                email='john@example.com',
                age=25,
                addresses=['123 Main St', '456 Main St'],
            ),
            User(
                name='Jane',
                email='jane@example.com',
                age=30,
                addresses=['456 Main St', '789 Main St'],
            ),
            User(
                name='Alice',
                email='alice@example.com',
                age=35,
                addresses=['789 Main St', '101 Main St', '102 Main St'],
            ),
            User(
                name='Bob',
                email='bob1@example.com',
                age=28,
                addresses=['101 Main St'],
            ),
            User(
                name='Bob',
                email='bob2@example.com',
                age=40,
                addresses=['102 Main St'],
            ),
            User(
                name='Charlie',
                email='charlie@example.com',
                age=32,
                addresses=['103 Main St', '104 Main St'],
            ),
            User(
                name='David',
                email='david@example.com',
                age=41,
                addresses=['104 Main St'],
            ),
            User(
                name='Eve',
                email='eve@example.com',
                age=54,
                addresses=['105 Main St'],
            ),
            User(
                name='Frank',
                email='frank@example.com',
                age=29,
                addresses=['106 Main St', '107 Main St', '108 Main St'],
            ),
            User(
                name='Grace',
                email='grace@example.com',
                age=37,
                addresses=['107 Main St', '108 Main St'],
            ),
        ]
    )
    session.commit()


def seed_posts(session: Session):
    session.add_all(
        [
            Post(title='Post 1', body='Body 1', rating=5, user_id=1),
            Post(title='Post 2', body='Body 2', rating=4, user_id=1),
            Post(title='Post 3', body='Body 3', rating=3, user_id=2),
            Post(title='Post 4', body='Body 4', rating=2, user_id=2),
        ]
    )
    session.commit()


def seed_data(session: Session):
    seed_users(session)
    seed_posts(session)
