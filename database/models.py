from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    is_authorized = Column(Boolean, default=False)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    # Armazena como string separada por vírgulas: "18:00,19:00"
    schedule_times = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    def set_schedule_times(self, times_list):
        """Converte lista para string e armazena."""
        self.schedule_times = ','.join(times_list)

    def get_schedule_times(self):
        """Converte string armazenada de volta para lista."""
        return self.schedule_times.split(',')
        
class Group(Base):
    __tablename__ = "groups"
    __table_args__ = {'extend_existing': True}  # <--- adiciona isso

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)  # Se for usar esse campo