import config
from models import Base
from models import Task, User

from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, insert, update, delete, or_


class Database:
    def __init__(self):
        self.engine = create_async_engine(
            config.ENGINE,
            echo=True,
        )
        self.async_session = sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    async def make_db(self):
        """
        WARNING!!!
        Method replaces all tables and deletes all data!
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await self.engine.dispose()

    async def fetch_user(self, email=None, user_id=None):
        """
        Fetch SQLAlchemy models.User object from database by the email or user id
        :param email: user's email
        :param user_id: user's id
        :return: SQLAlchemy models.User object
        """
        async with self.async_session() as session:
            stmt = (
                select(User).
                where(or_(User.email == email, User.id == user_id))
            )
            query_result = await session.execute(stmt)
            await session.commit()
        await self.engine.dispose()

        user = query_result.scalars().first()

        return user

    async def add_new_user(self, username, email, hashed_password):
        async with self.async_session() as session:
            stmt = (
                insert(User).
                values(
                    username=username,
                    email=email,
                    password=hashed_password
                )
            )
            await session.execute(stmt)
            await session.commit()
        await self.engine.dispose()

    async def fetch_tasks_list(self, user_id):
        """
        Fetch all user's task from DB by user_id
        :param user_id: user's id
        :return: list of tasks in dictionary format
        """
        async with self.async_session() as session:
            stmt = (
                select(Task).
                where(Task.user_id == user_id)
            )
            query_result = await session.execute(stmt)
            await session.commit()
        await self.engine.dispose()

        tasks = query_result.scalars().all()
        tasks_list = []
        for task in tasks:
            tasks_list.append({
                'task_id': task.id,
                'task_name': task.name,
                'task_desc': task.description,
                'deadline': task.deadline.isoformat()
            })

        return tasks_list

    async def add_new_task(self, user_id, task_name=None, desc=None, deadline=None):
        async with self.async_session() as session:
            stmt = (
                insert(Task).
                values(
                    name=task_name,
                    description=desc,
                    deadline=datetime.fromisoformat(deadline),
                    user_id=user_id
                )
            )
            await session.execute(stmt)

            await session.commit()
        await self.engine.dispose()

    async def delete_task(self, user_id: int, task_id: int):
        async with self.async_session() as session:
            stmt = (
                delete(Task).
                where(Task.id == task_id, Task.user_id == user_id)
            )
            await session.execute(stmt)

            await session.commit()
        await self.engine.dispose()


