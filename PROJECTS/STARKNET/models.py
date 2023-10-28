import asyncio
import datetime
import time

from constants import ErrorCodes

from typing import List, Tuple
from sqlalchemy import ForeignKey, TIMESTAMP, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from dotenv import dotenv_values

env_values = dotenv_values(".env")
login, password = env_values["POSTGRES_USER"], env_values["POSTGRES_PASSWORD"]

# Создание объекта Engine для соединения с базой данных
engine = create_engine(url=f"postgresql://{login}:{password}@localhost:5432/postgres", echo=True)

session = sessionmaker(engine)
Base = declarative_base()

class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_name: Mapped[str]

    route: Mapped['Route'] = relationship(back_populates="project")


class Route(Base):
    __tablename__ = "route"

    id: Mapped[int] = mapped_column(primary_key=True)
    route_name: Mapped[str]
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))

    project: Mapped["Project"] = relationship(back_populates="route")
    action: Mapped[List["Action"]] = relationship(back_populates="route", uselist=True)


class Action(Base):
    __tablename__ = 'action'

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    action_list_id: Mapped[int] = mapped_column(ForeignKey("action_list.id"))

    action_list: Mapped['ActionList'] = relationship(back_populates="action")
    route: Mapped['Route'] = relationship(back_populates="action")
    action_wallet: Mapped['ActionWallet'] = relationship(back_populates="action", uselist=True)


class ActionList(Base):
    __tablename__ = 'action_list'

    id: Mapped[int] = mapped_column(primary_key=True)
    action_name: Mapped[str]

    action: Mapped[List["Action"]] = relationship(back_populates="action_list")


class ActionWallet(Base):
    __tablename__ = 'action_wallet'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[str]

    action_id: Mapped[int] = mapped_column(ForeignKey('action.id'))
    wallet_id: Mapped[int] = mapped_column(ForeignKey('wallet.id'))
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=datetime.datetime.now)

    wallet: Mapped['Wallet'] = relationship(back_populates="action_wallet")
    action: Mapped['Action'] = relationship(back_populates="action_wallet")


class Wallet(Base):
    __tablename__ = 'wallet'

    id: Mapped[int] = mapped_column(primary_key=True)
    primary_key: Mapped[str]
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=datetime.datetime.now)

    client: Mapped['Client'] = relationship(back_populates="wallet")
    action_wallet: Mapped['ActionWallet'] = relationship(back_populates="wallet")


class Client(Base):
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=datetime.datetime.now)

    wallet: Mapped["Wallet"] = relationship(back_populates="client")


class Status(Base):
    __tablename__ = "status"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[int]
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=datetime.datetime.now)
    desc: Mapped[str]
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"))
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"))
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    action_id: Mapped[int] = mapped_column(ForeignKey("action.id"))

    client: Mapped['Client'] = relationship(backref="status")
    wallet: Mapped['Wallet'] = relationship(backref="status")
    project: Mapped['Project'] = relationship(backref="status")
    route: Mapped['Route'] = relationship(backref="status")
    action: Mapped['Action'] = relationship(backref="status")


class CRUD():
    def __init__(self, session = None) -> None:
        if not session:
            self.session = sessionmaker(engine)
        else:
            self.session = session

    def create_table(self):
        x = input('Вы уверены, что хотите удалить все таблицы бд? (y/n): ')

        if x == 'y':
            Base.metadata.drop_all(engine)

        Base.metadata.create_all(engine)


    async def insert_data(self, *obj, **kwargs):
        with self.session() as session:
            session.add_all(obj)
            session.commit()
            session.refresh(obj)

            return obj

    async def create_client(self, name: str) -> Client:
        client = Client(client_name=name)
        result = await self.insert_data(obj=client)

        return result

    async def create_wallet(self, private_key: str, client: Client) -> Wallet:
        wallet = Wallet(primary_key=private_key, client=client)
        result = await self.insert_data(obj=wallet)

        return result

    async def create_action_wallet(self, wallet: Wallet, action: Action, status: str) -> ActionWallet:
        action_wallet = ActionWallet(wallet=wallet, action=action, status=status)
        result = await self.insert_data(obj=action_wallet)

        return result

    def prepare_data(self, data) -> tuple:
        private_key = data.get("private_key")
        client_name = data.get("client_name")

        return private_key, client_name

    async def create_client_wallet(self, data) -> Tuple[Client, Wallet]:
        private_key, client_name = self.prepare_data(data)

        client = await self.create_client(client_name)
        wallet = await self.create_wallet(private_key, client)

        return client, wallet

    async def create_status(
            self, 
            code: ErrorCodes | int, 
            desc: str,
            client: Client,
            wallet: Wallet,
            project: Project,
            route: Route,
            action: Action,
            data: datetime = None    
        ) -> Status:
        
        status = Status(
            code=code, 
            desc=desc, 
            date=data,
            client=client,
            wallet=wallet,
            project=project,
            route=route,
            action=action
        )
        result = await self.insert_data(obj=status)

        return result

    def get_actions(self, route_id) -> ActionList:
        with self.session() as session:
            actions_list = []
            raw_sql = select(Route).where(Route.id == route_id)
            route = session.scalars(raw_sql).first()
            for item in route.action:
                raw_action = select(ActionList).where(ActionList.id == item.action_list_id)
                action = session.scalars(raw_action).first()
                actions_list.append(action)

            return actions_list
    
    async def get_single_action(self, route_id, action_id) -> Action:
        with self.session() as session:
            raw_sql = select(Action).where(Action.route_id == route_id, Action.id == action_id)
            action = session.scalars(raw_sql).first()
            
            return action
    
    async def get_project(self, project_id) -> Project:
        with self.session() as session:
            raw_sql = select(Project).where(Project.id == project_id)
            project = session.scalars(raw_sql).first()
            
            return project


# crud = CRUD()
# crud.create_table()

# client = Client(client_name="jj")
# wallet = Wallet(primary_key="0x123", client=client)
# project = Project(project_name="test")
# route = Route(route_name="test", project=project)
# action_list = ActionList(action_name="myswap")
# action = Action(route=route, action_list=action_list)
# # action_wallet = ActionWallet(wallet=wallet, action=action, status="IN_PROGRESS")
# asyncio.run(crud.create_action_wallet(wallet, action, "IN_PROGRESS"))
# # asyncio.run(crud.insert_data(client, wallet, project, route, action, action_wallet))

# status = Status(
#     code=200,
#     desc="test",
#     date=datetime.datetime.now(),
#     client=client,
#     wallet=wallet,
#     project=project,
#     route=route,
#     action=action
# )
# # asyncio.run(crud.insert_data(status))

# asyncio.run(crud.insert_data(client, wallet, project, route, action, status))

