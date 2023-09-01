#!/usr/bin/env python3
'''
Created on 25 авг. 2023 г.

@author: demon
'''
import config
import requests
import json
import sys
import time
import datetime as dt
from iikoapi import Api_iiko
from iikobiz import Iiko_biz


class ProntoSMS():
    SERVER = 'https://clk.prontosms.ru/sendsmsjson.php'

    def __init__(self):
        self.iiko = Api_iiko()
        self.iikobiz = Iiko_biz()

    def request(self, cmd, * , headers={}, **payload):
        headers.setdefault('Content-Type', 'application/json; charset=utf-8')
        headers['Authorization'] = f'Bearer {config.PRONTO_TOKEN}'
        payload.setdefault('type', cmd)
        r = requests.post(self.SERVER, data=json.dumps(payload), headers=headers, timeout=10)
        r.raise_for_status()
        jdata = r.json()
        if 'error' in jdata:
            raise Exception(jdata['error'])
        return jdata

    def get_balance(self):
        return self.request('balance')

    def list_bases(self):
        r = self.request('list_bases')
        return r

    def make_birhday_delivery(self, days=0):
        pass

    def list_phones(self):
        id_base = self.get_id_base()
        page, num_pages = 1, 1
        phones = []
        if id_base:
            while page <= num_pages:
                print(f"request page {page}")
                r = self.request('list_phones', base={'id_base': id_base, 'page':page})
                page, num_pages = int(r.get('page', page)) + 1, int(r.get('num_pages', num_pages))
                phones.extend(r['phones'])
        return phones

    def add_base(self):
#         _index = int(dt.datetime.now().hour <= 12)
        _index = 0
        base = {"id_base":self.get_id_base(),
                "number_base":"1",
                "name_base":config.PRONTO_BASE,
                "local_time_birth":"yes",
                "on_birth":"yes",
                }
        base.update(config.PRONTO_BASE_CONFIG[_index])
        r = self.request('bases', bases=[base])
        return r['bases'][0]['id_base']

    def get_id_base(self):
        for b in self.list_bases()['base']:
            if b['name_base'] == config.PRONTO_BASE:
                return b['id_base']

    def name_surname(self, name):
        names = name.split()
        if len(names) > 1:
            return names[1], names[0]
        else:
            return names[0], None

    def import_clients_from_iiko(self):
        id_base = self.get_id_base()
        if id_base:
            clients = self.iikobiz.GuestList()
            phones = [{'phone': c['PhoneNumber'],
                       'name': self.name_surname(c['Name'])[0],
                       'surname': self.name_surname(c['Name'])[1],
                       'date_birth': f"{self.iikobiz.get_datetime(c['Birthday']):%Y-%m-%d}" if c['Birthday'] else None,
                       'male': c['Sex'],
                       'number_phone': i} for i, c in enumerate(clients['data']) if not c['IsDeleted']]
            return self.request('phones', id_base=id_base, phones=phones)

    def get_birthday_clients(self, days=0):
        clients = self.iikobiz.GuestList()
        phones = [{'phone': c['PhoneNumber'],
                       'name': self.name_surname(c['Name'])[0],
                       'surname': self.name_surname(c['Name'])[1],
                       'date_birth': f"{self.iikobiz.get_datetime(c['Birthday']):%Y-%m-%d}",
                       'male': c['Sex'],
                       'number_phone': i} for i, c in enumerate(clients['data']) if not c['IsDeleted'] and
                                c['Birthday'] and
                                f"{self.iikobiz.get_datetime(c['Birthday']):%m-%d}" == f"{dt.datetime.today()+dt.timedelta(days=days):%m-%d}"]
        return phones

    def send_sms(self, *, text, phones:list, sender='', name_delivery='', **params):
        senders = self.get_valid_senders()
        abonents = []
#         dict(params.copy() for i, p in enumerate(phones)
        for i, p in enumerate(phones):
            a = params.copy()
            a['phone'] = p
            a["number_sms"] = i + 1
            abonents.append(a)

        message = {
            "type":"sms",
            "text":text,
            "translite":0,
            "abonent":abonents
        }
        if senders:
            if not sender or sender not in senders:
                sender = self.get_valid_senders()[0]
        message['sender'] = sender
        if name_delivery:
            message['name_delivery'] = name_delivery
        print(message)
        return self.request('sms', message=[message])

    def add_one_client(self, **payload):
        id_base = self.get_id_base()
        if id_base:
            if 'birthday' in payload:
                try:
                    birthday = dt.datetime.strptime(payload['birthday'][:10], '%d-%m-%Y')
                except ValueError:
                    birthday = dt.datetime.strptime(payload['birthday'][:10], '%Y-%m-%d')
            payload['date_birth'] = f"{birthday:%Y-%m-%d}"
            payload['surname'] = payload.get('surName', '')
            payload['male'] = payload.get('sex', '')
            payload['number_phone'] = 1

            r = self.request('phones', id_base=id_base, phones=[payload])
            return r

    def list_stats(self, days=1):
        date_start = dt.datetime.today() - dt.timedelta(days=days)
        return self.request('list_stats', date_start=f"{date_start:%Y-%m-%d}")

    def add_to_stop(self, phones):
        return self.request('stop', add_stop=phones)

    def list_stop(self):
        return self.request('list_stop')

    def stop_undelivered(self):
        ls = self.list_stats()
        phones = [s['phone'] for s in ls['stats'] if s['status'] not in {'deliver', 'partly_deliver'}]
        self.add_to_stop(phones)
        for phone in phones:
            self.iiko.add_customer_to_categ(phone, 'удаленные')

    def del_clients(self):
        id_base = self.get_id_base()
        if id_base:
            ls = self.list_stats()
            phones = [{'phone': s['phone'], 'action': 'delete', 'number_phone': i + 1} for i, s in enumerate(ls['stats']) if s['status'] not in {'deliver', 'partly_deliver'}]
            return self.request('phones', id_base=id_base, phones=phones)

    def get_valid_senders(self):
        r = self.request('originator')
        return [s['originator'] for s in r['list_originator'] if s['state'] == 'completed']


if __name__ == '__main__':
    pronto = ProntoSMS()
    pronto.add_base()
#     sys.exit()
    while True:
        try:
            pronto.stop_undelivered()
        except Exception as e:
            print(e)
        finally:
            time.sleep(3600)
