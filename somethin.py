import requests
import json
import configparser
import time
from datetime import datetime

username = 's_robkanov@inbox.ru'
password = 'qwertyqwerty123'
NORAD_ID = '25544' #- ID for ISS

apiBase                = "https://www.space-track.org"
requestLogin           = "/ajaxauth/login"
requestLogout          = "/ajaxauth/logout')"
requestCmdAction       = "/basicspacedata/query" 
requestTLELines = f"/class/gp/NORAD_CAT_ID/{NORAD_ID}/format/tle/emptyresult/show"



## пытаюсь писать свои исключения


class MyError(Exception):
    def __init__(self,args):
        Exception.__init__(self,'my exception was raised with argiments {0}'.format(args))
        self.args = args 
        



Test_rec=requests.get('https://www.space-track.org/basicspacedata/query/class/boxscore/format/html',)
print(Test_rec)          ### должно выводить 400
## 'Response 401' means cant log to api


## try to log-in
##


# Start session
session = requests.Session()

# Log in to Space-Track
session.post('https://www.space-track.org/ajaxauth/login', data={'identity': username, 'password': password})

# Make a request to the API endpointp
response = session.get(apiBase + requestCmdAction + requestTLELines )

# Check response
if response.status_code == 200:
    data = response.text
    print(data)
else:
    print('Error:', response.status_code)


## also ... 
## 200 — «OK». Запрос прошёл успешно, и мы получили ответ.
##
## 400 — «Плохой запрос». Его получаем тогда, когда сервер не может понять запрос, отправленный клиентом. Как правило, это указывает на неправильный синтаксис запроса, неправильное оформление сообщения запроса и так далее.
## 401 — «Unauthorized». Для выполнения запроса необходимы актуальные учётные данные.
## 403 — «Forbidden». Сервер понял запрос, но не может его выполнить. Например, у используемой учётной записи нет достаточных прав для просмотра содержимого.
## 404 — «Не найдено». Сервер не нашёл содержимого, соответствующего запросу.

## try MyException
try:
    raise MyError([1, 2, 3])
except MyError as e:
    print(e)  # Выведет: my exception was raised with arguments [1, 2, 3]
    print(e.args)  # Выведет: [1, 2, 3]
    
    
    
    