from fastapi import FastAPI, HTTPException
from typing import Union, List
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import numpy as np

# uvicorn mocked_api:app

class Coauthor(BaseModel):
    name: str
    surname: str
    patronymic: Union[str, None]

class Application(BaseModel):
    id: Union[int, None] = None
    telegram_id: Union[int, None] = None
    discord_id: Union[int, None] = None
    email: str
    phone: str
    name: str
    surname: str
    patronymic: Union[str, None]
    university: str
    student_group: str
    title: str
    adviser: str
    coauthors: List[Coauthor]

data = [
    Application.parse_obj({
        "id": 1,
        "telegram_id": 1008218722,
        "discord_id": 0,
        "email": "example@example.com",
        "phone": "+79001234567",
        "name": "Ivan",
        "surname": "Ivanov",
        "patronymic": "Ivanovich",
        "university": "SUAI",
        "student_group": "4031",
        "title": "Title of the report to be submitted to the conference",
        "adviser": "professor Sidorov A.B.",
        "coauthors": [
            {
                "name": "Petr",
                "surname": "Petrov",
                "patronymic": "Petrovich"
            },
            {
                "name": "Petr2",
                "surname": "Petrov2",
                "patronymic": "Petrovich2"
            }
        ]
    })
]

def find_application(email, telegram_id, discord_id):
    if email:
        return [item for item in data if item.email == email]
    elif telegram_id:
        return [item for item in data if item.telegram_id == int(telegram_id)]
    elif discord_id:
        return [item for item in data if item.discord_id == int(discord_id)]
    return []

def create_application(application):
    ids = [item.id for item in data]
    max_id = np.amax(np.array(ids))
    application.id = max_id + 1
    data.append(application)
    return application

# проверить
def update_application(application):
    to_delete = next(filter(lambda item: item.id == application.id, data))
    del data[data.index(to_delete)]
    data.append(application)
    return application




app = FastAPI()

@app.get("/applications")
async def get_application(email=None, telegram_id=None, discord_id=None) -> List[Application]:
    if not email and not telegram_id and not discord_id:
        raise HTTPException(status_code=400, detail="none of the parameters are specified")
    result = find_application(email, telegram_id, discord_id)
    print(result)
    return result

@app.post("/applications")
async def post_application(application: Application) -> Application:
    print(application)
    created_application = create_application(application)
    return created_application

@app.put("/applications")
async def put_application(application: Application) -> Application:
    print(application)
    updated_application = update_application(application)
    return updated_application
