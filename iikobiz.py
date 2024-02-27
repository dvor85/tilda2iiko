'''
Created on 23 авг. 2023 г.

@author: demon
'''
import config
import requests
import datetime


class Iiko_biz:
    SERVER = 'https://m1.iiko.cards/ru-RU'

    def __init__(self):
        '''
        Constructor
        '''

    def get_datetime(self, s) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(int(s[6:-2]) / 1000)

    def request(self, cmd, * , headers={}, **payload):
        headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
        headers.setdefault('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0')
        headers.setdefault('Origin', 'https://iiko.biz')
        headers.setdefault('X-Requested-With', 'XMLHttpRequest')
        headers.setdefault('Referer', 'https://iiko.biz/ru-RU/CorporateNutrition/Guests')
        cookie = {'iikoBiz': config.IIKOBIZ_COOKIE}
        print(headers)
        print(payload)
        r = requests.post(f"{self.SERVER}{cmd}", data=payload, headers=headers, cookies=cookie, timeout=15)
        r.raise_for_status()
        return r

    def GuestList(self):
        return self.request('/Guests/GuestsListAjax', orderBy='WhenCreated-desc', ShowInactive=False, OrganizationOrNetworkId=config.IIKOBIZ_NETWORK_ID).json()

    def get_birthdays(self, days=14):
        pass


if __name__ == '__main__':
    iiko = Iiko_biz()
    print(iiko.GuestList())
