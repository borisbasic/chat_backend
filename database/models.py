from .database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    receiver_id = Column(Integer, ForeignKey('users.id'))
    content = Column(String)
    message_uuid = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class Rooms(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer)
    receiver_id = Column(Integer)
    images = relationship('Images', back_populates='room')
    documents = relationship('Documents', back_populates='room')

class Images(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True, index=True)
    image_name = Column(String)
    sender_image = Column(Integer, ForeignKey('users.id'))
    receiver_image = Column(Integer, ForeignKey('users.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    room = relationship('Rooms', back_populates='images')


class Documents(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String)
    sender_document = Column(Integer, ForeignKey('users.id'))
    receiver_document = Column(Integer, ForeignKey('users.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    room = relationship('Rooms', back_populates='documents')