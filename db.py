from models import Base
from models import Task, User

from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, insert, update, or_


class Database:
    def __init__(self):
        self.engine = create_async_engine(
            "postgresql+asyncpg://postgres:root@localhost/db_tensor_todo",
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

    async def fetch_tasks_by_user(self, user_id=1):
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

    async def add_new_task(self, task_name: str, desc: str, deadline: str, user_id: int):
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

    # async def update_task(self, task_id, task_name=None, description=None, deadline=None):
    #     async with self.async_session() as session:
    #         stmt = update(Task).\
    #             where(Task.id == task_id).\
    #             values(name='user #5')
    #         await session.execute(stmt)
    #
    #         await session.commit()
    #     await self.engine.dispose()

    async def fetch_user(self, email=None, user_id=None):
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
