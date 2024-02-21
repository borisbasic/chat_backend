# CHAT FASTAPI
 - chat backend
 - websocket
 - sqlalchemy
 - chat text, images, documents

## INSTALL

1) python (3.10.12, include PATH)
2) install pip (https://pip.pypa.io/en/stable/installation/)
3) install virtual env (https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)

## CLONE

git clone https://github.com/borisbasic/chat_backend

cd chat_backend

## Install virtual enviroment (venv)

start virtual env 
 - windows, venv\Scripts\activate
 - linux, source venv/bin/activate

pip install -r requirements.txt

## START SERVER

uvicorn main:app --reload

## DOCUMENTATION

http://localhost:8000/docs#/


 - /quites need to be called every half our
 