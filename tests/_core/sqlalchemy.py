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


class Address(Base):
    __tablename__ = 'addresses'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city: Mapped[str] = mapped_column()
    country: Mapped[str] = mapped_column()
    profile_id: Mapped[int] = mapped_column(ForeignKey('profiles.id'))
    profile: Mapped['Profile'] = relationship(back_populates='address')


class Profile(Base):
    __tablename__ = 'profiles'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bio: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='profile')
    address: Mapped['Address'] = relationship(back_populates='profile', uselist=False)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()
    addresses: Mapped[list[str]] = mapped_column(JSON)
    posts: Mapped[list['Post']] = relationship(back_populates='user')
    profile: Mapped['Profile'] = relationship(back_populates='user', uselist=False)


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


def seed_profiles(session: Session):
    session.add_all(
        [
            Profile(id=1, bio='Software Engineer', user_id=1),
            Profile(id=2, bio='Data Scientist', user_id=2),
            Profile(id=3, bio='Product Manager', user_id=3),
            Profile(id=4, bio='Designer', user_id=4),
            Profile(id=5, bio='Marketing Manager', user_id=5),
        ]
    )
    session.commit()


def seed_addresses(session: Session):
    session.add_all(
        [
            Address(city='New York', country='USA', profile_id=1),
            Address(city='Chicago', country='USA', profile_id=2),
            Address(city='Boston', country='USA', profile_id=3),
            Address(city='London', country='UK', profile_id=4),
            Address(city='Paris', country='France', profile_id=5),
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
    seed_profiles(session)
    seed_addresses(session)
    seed_posts(session)
