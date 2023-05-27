import config
import requests

application = {
        "id":"1",
        "telegram_id": "1234",
        "discord_id": "4321",
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
    }

#response = requests.post(config.BACKEND_BASE_URL + '/applications', json=application)
#print(response.json())

response = requests.get(config.BACKEND_BASE_URL + '/applications', params={
    'email': 'example@example.com'
})
print(response.json())
