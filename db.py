from sqlalchemy  import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, Boolean, PickleType
from loguru import logger

class DB:
    @logger.catch
    def __init__(self,filename):
        self.engine = create_engine(f"sqlite:///{filename}")
        session = sessionmaker(bind=self.engine)
        self.Base = declarative_base()
        self.s = session()
        logger.success(F"база данных по адресу {filename} активирована")
    @logger.catch
    def setup(self):
        self.Base.metadata.create_all(self.engine)
        logger.success("таблицы базы данных созданы")
    @logger.catch
    def merge(self,data):
        self.s.merge(data)
        logger.info(f"в таблицу {data.__class__.__tablename__} были добавлены айди {data.id if data.id else data}")
    def commit(self):
        self.s.commit()
        logger.info("изменение базы данных были сохранены")
db = DB("db.db")

class Tablicha(db.Base):
    __tablename__ = "users"
    id =  Column(Integer,primary_key=True)
    name = Column(String)
    answers = Column(PickleType)
    admin = Column(Boolean)

class Questions(db.Base):
    __tablename__ = "questions"
    id = Column(Integer,primary_key=True)
    name = Column(String)
    question = Column(PickleType)

db.setup()