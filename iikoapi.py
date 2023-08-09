'''
Created on 25 июл. 2023 г.

@author: demon
'''
import requests
import json
from pathlib import Path
import time
import config
from datetime import datetime


class Api_iiko():
    API_SERVER = 'https://api-ru.iiko.services'

    def __init__(self):
        self.token_file = Path('/tmp/iiko/token')
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def token_is_expired(self):
        if self.token_file.is_file():
            return time.time() - self.token_file.stat().st_mtime >= 3600
        else:
            return True

    def request_iiko(self, cmd, * , headers={}, **payload):
        headers.setdefault('Content-Type', 'application/json')
        if not cmd == '/api/1/access_token':
            headers['Authorization'] = f'Bearer {self.get_token()}'
        payload.setdefault("organizationId", config.ORGANIZATION_ID)
        print(headers)
        print(payload)
        r = requests.post(f'{self.API_SERVER}{cmd}', data=json.dumps(payload), headers=headers, timeout=10)
        r.raise_for_status()
        return r

    def get_token(self):
        if not self.token_is_expired():
            with self.token_file.open(mode='r') as fp:
                token = json.load(fp)
        else:
            r = self.request_iiko('/api/1/access_token', apiLogin=config.API_KEY)
            token = r.json()['token']
            with self.token_file.open(mode='w') as fp:
                json.dump(token, fp)
        return token

    def get_organization_id(self):
        r = self.request_iiko('/api/1/organizations')
        return r.json()['organizations'][0]['id']

    def create_or_update(self, **payload):
        genders = ['Мужской', 'Женский']
        payload.setdefault("shouldReceivePromoActionsInfo", True)
        payload.setdefault("consentStatus", 1)
        if 'birthday' in payload:
            try:
                birthday = datetime.strptime(payload['birthday'][:10], '%d-%m-%Y')
            except ValueError:
                birthday = datetime.strptime(payload['birthday'][:10], '%Y-%m-%d')
            payload['birthday'] = f"{birthday:%Y-%m-%d} 00:00:00.000"
        if 'sex' in payload:
            payload['sex'] = genders.index(payload['sex']) + 1

        r = self.request_iiko('/api/1/loyalty/iiko/customer/create_or_update', **payload)
        return r.json()

    def get_terminal_groups(self):
        r = self.request_iiko('/api/1/terminal_groups', organizationIds=[config.ORGANIZATION_ID])
#         return r.json()['terminalGroups'][0]['items'][0]['id']
        return r.json()

    def create_order(self):
        r = self.request_iiko('/api/1/order/create', terminalGroupId=self.get_terminal_groups(), phone='+79998887770', items=[])

    def get_menu(self):
        r = self.request_iiko('/api/1/nomenclature')
        return r.json()

    def get_customer_info(self, phone):
        r = self.request_iiko('/api/1/loyalty/iiko/customer/info', type='phone', phone=phone)
        return r.json()


if __name__ == '__main__':
    iiko = Api_iiko()
#     print(iiko.get_terminal_groups())
#     print(iiko.create_or_update(phone="+79998887770", name="Test"*4, birthday="1985-09-01 00:00:00.000", sex=1, email=""))
    print(iiko.get_customer_info('+79998887775'))
#     print(iiko.get_menu())
