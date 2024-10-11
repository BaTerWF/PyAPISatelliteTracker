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

class Satellite:
    def __init__(self, name: str, norad_id: int, tle: tuple):
        """
        Инициализация объекта спутника
        :param name: Название спутника
        :param norad_id: NORAD ID спутника
        :param tle: Кортеж из двух строк, представляющих собой TLE (Two-Line Elements)
        """
        self.name = name
        self.norad_id = norad_id
        self.tle = tle

    def __str__(self):
        """
        Возвращает строковое представление объекта спутника.
        """
        return f"Satellite(name={self.name}, norad_id={self.norad_id}, TLE={self.tle})"

    def update_tle(self, new_tle: tuple):
        """
        Обновляет TLE координаты спутника.
        :param new_tle: Новый кортеж с TLE данными
        """
        self.tle = new_tle

    def get_tle(self):
        """
        Возвращает TLE координаты спутника.
        :return: Кортеж из двух строк (TLE)
        """
        return self.tle


# Пример использования
satellite = Satellite("Hubble", 20580, ("1 20580U 90037B   20264.90323330  .00000763  00000-0  36483-4 0  9993",
                                        "2 20580  28.4712 330.5330 0002872  32.2311 327.8690 15.09305817310739"))

print(satellite)  # Вывод информации о спутнике
print(satellite.get_tle())  # Получение TLE данных


    
    
    
