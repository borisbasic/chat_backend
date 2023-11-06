from pydantic import BaseModel
from datetime import datetime


class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str


class UserBase(BaseModel):
    id: int
    username: str


class RoomNumber(BaseModel):
    id: int


class Login(BaseModel):
    username: str


class ChatImage(BaseModel):
    image_name: str
    sender_id: int
    receiver_id: int
    room_id: int


class ImageDisplay(BaseModel):
    image_name: str


class ChatDocuments(BaseModel):
    document_name: str
    sender_id: int
    receiver_id: int
    room_id: int


class DocumentDisplay(BaseModel):
    document_name: str


class ChatVideo(BaseModel):
    video_name: str
    sender_id: int
    receiver_id: int
    room_id: int

class VideoDisplay(BaseModel):
    video_name: str