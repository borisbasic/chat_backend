from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.sql import or_, and_
from schemas import (
    MessageCreate,
    UserBase,
    RoomNumber,
    Login,
    ImageDisplay,
    ChatImage,
    DocumentDisplay,
    ChatDocuments,
    VideoDisplay,
    ChatVideo,
)
from database.database import get_db
from database.models import User, Message, Rooms, Images, Documents, Videos
from database import models
from database.database import engine
from typing import List
import json
import uuid
import shutil
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

ALLOWED_IMAGES_EXT = ["jpg", "png", "gif", "jpeg"]
ALLOWED_DOCUMENTS_EXT = ["doc", "docx", "pdf", "txt"]
ALLOWED_VIDEOS_EXT = ["mp4", "divx"]

origins = ["http://localhost:3000"]  # we use this for our web application

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebsocketManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = WebsocketManager()
client = []


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_id: int, db: Session = Depends(get_db)
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(data["sender_id"])
            message = {"message": data["message"], "sender_id": data["sender_id"]}

            new_room_message = Message(
                sender_id=data["sender_id"],
                receiver_id=data["receiver_id"],
                content=data["message"],
                type_of_message=data["type_of_message"],
            )
            db.add(new_room_message)
            db.commit()
            db.refresh(new_room_message)

            await manager.broadcast(json.dumps(message))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


models.Base.metadata.create_all(engine)


@app.post("/register")
def register_user(request: UserBase, db: Session = Depends(get_db)):
    new_user = User(username=request.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    new_user = db.query(User).filter(User.username == request.username).first()

    users = db.query(User).all()
    for user in users:
        if new_user.id != user.id:
            new_room = Rooms(sender_id=new_user.id, receiver_id=user.id)
            db.add(new_room)
            db.commit()
            db.refresh(new_room)
    return {"message": "New user registered!"}


@app.post("/messages", response_model=MessageCreate)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    db_message = Message(
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        type_of_message=message.type_of_message,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@app.get("/messages/{sender_id}/{receiver_id}", response_model=List[MessageCreate])
async def get_messages(sender_id: int, receiver_id: int, db: Session = Depends(get_db)):
    sender = db.query(User).filter(User.id == sender_id).first()
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {sender_id} not found.",
        )

    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {sender_id} not found.",
        )

    messages = (
        db.query(Message)
        .filter(
            or_(
                and_(
                    Message.sender_id == sender_id, Message.receiver_id == receiver_id
                ),
                and_(
                    Message.sender_id == receiver_id, Message.receiver_id == sender_id
                ),
            )
        )
        .all()
    )

    return messages


@app.get("/users/{id}", response_model=List[UserBase])
def get_users(id: int, db: Session = Depends(get_db)):
    users_ = []
    users = db.query(User).all()
    for user in users:
        if user.id != id:
            users_.append(user)
    return users_


@app.get("/room_number/{sender_id}/{receiver_id}", response_model=RoomNumber)
def get_room_number(sender_id: int, receiver_id: int, db: Session = Depends(get_db)):
    room = (
        db.query(Rooms)
        .filter(
            or_(
                and_(Rooms.sender_id == sender_id, Rooms.receiver_id == receiver_id),
                and_(Rooms.sender_id == receiver_id, Rooms.receiver_id == sender_id),
            )
        )
        .first()
    )
    if room:
        return room
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Room not found"
        )


@app.post("/login", response_model=UserBase)
def login(request: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found!"
        )
    return user


@app.get("/message/{message_uuid}")
def get_message_uuid(message_uuid: str, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.message_uuid == message_uuid).first()
    if message:
        return {"check": True}
    else:
        return {"check": False}


@app.post("/image")
def upload_image(image: UploadFile = File(...)):
    filename = uuid.uuid4().hex + "."
    ext = image.filename.split(".")[-1]
    print(ext)
    if ext not in ALLOWED_IMAGES_EXT:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"Image with extension {ext} not acceptable",
        )
    full_name = filename.join(image.filename.rsplit(".", 1))
    path = f"images/{filename}{ext}"
    with open(path, "w+b") as buffer:
        shutil.copyfileobj(image.file, buffer)
    return {"filename": path}


@app.post("/chat_image", response_model=ImageDisplay)
def post_chat_image(request: ChatImage, db: Session = Depends(get_db)):
    new_image = Images(
        image_name=request.image_name,
        sender_image=request.sender_id,
        receiver_image=request.receiver_id,
        room_id=request.room_id,
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


@app.post("/documents")
def upload_image(document: UploadFile = File(...)):
    filename = uuid.uuid4().hex + "."
    ext = document.filename.split(".")[-1]
    if ext not in ALLOWED_DOCUMENTS_EXT:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"Document with extension {ext} not acceptable",
        )
    full_name = filename.join(document.filename.rsplit(".", 1))
    path = f"documents/{filename}{ext}"
    with open(path, "w+b") as buffer:
        shutil.copyfileobj(document.file, buffer)
    return {"filename": path}


@app.post("/chat_documents", response_model=DocumentDisplay)
def post_chat_image(request: ChatDocuments, db: Session = Depends(get_db)):
    new_document = Documents(
        document_name=request.document_name,
        sender_document=request.sender_id,
        receiver_document=request.receiver_id,
        room_id=request.room_id,
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    return new_document


@app.post("/videos")
def upload_image(video: UploadFile = File(...)):
    filename = uuid.uuid4().hex + "."
    ext = video.filename.split(".")[-1]
    if ext not in ALLOWED_VIDEOS_EXT:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"Document with extension {ext} not acceptable",
        )
    full_name = filename.join(video.filename.rsplit(".", 1))
    path = f"videos/{filename}{ext}"
    with open(path, "w+b") as buffer:
        shutil.copyfileobj(video.file, buffer)
    return {"filename": path}


@app.post("/chat_video", response_model=VideoDisplay)
def post_chat_image(request: ChatVideo, db: Session = Depends(get_db)):
    new_video = Videos(
        video_name=request.video_name,
        sender_video=request.sender_id,
        receiver_video=request.receiver_id,
        room_id=request.room_id,
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    return new_video


@app.get("/check_exist_image/{image_name}")
def chceck_exist_image(image_name: str):
    list_dir = os.listdir("images")
    if image_name in list_dir:
        print(f"CHECKED {image_name}")
        return {"message": "E"}
    else:
        return {"message": "NE"}


@app.get("/check_exist_document/{document_name}")
def chceck_exist_document(document_name: str):
    list_dir = os.listdir("documents")
    if document_name in list_dir:
        print(document_name)
        return {"message": 1}
    return {"message": 0}


@app.get("/check_exist_video/{video_name}")
def chceck_exist_video(video_name: str):
    list_dir = os.listdir("videos")
    if video_name in list_dir:
        print(video_name)
        return {"message": 1}
    return {"message": 0}


app.mount("/documents", StaticFiles(directory="documents"), name="documents")
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
