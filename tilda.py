#!/usr/bin/env python3
'''
Created on 25 июл. 2023 г.

@author: demon
'''
import uvicorn
from fastapi import FastAPI, Request
import config
from datetime import datetime
import json
from pathlib import Path
import iikoapi
from prontosms import ProntoSMS
import telega
from fastapi.exceptions import HTTPException

app = FastAPI(openapi_url=None, root_path='/service')


@app.post("/iiko")
async def iiko(req:Request):
    if req.headers.get('Authorization', '') == config.TILDA2IIKO_TOKEN:
        params = req.query_params._dict
        if  'application/x-www-form-urlencoded' in req.headers.get('content-type', ''):
            fdata = await req.form()
            params.update(fdata)
        elif 'application/json' in req.headers.get('content-type', ''):
            jdata = await req.json()
            params.update(jdata)
        if 'test' not in params:
            iiko = iikoapi.Api_iiko()
            if 'Ресторан' in params:
                try:
                    ci = iiko.get_customer_info(params['Phone'])
                    if any('Черный список' in categ['name'] for categ in ci['categories']):
                        await telega.send_message(f"Гость {ci['name']} тел. {ci['phone']} в \"Черном списке\"!")
                except:
                    print(f"client with phone: {params['Phone']} not exists")
            else:
                iiko.create_or_update(**params)
#                 text = iiko.format_guest_info(iiko.get_customer_info(params['Phone']))
#                 text.append(f"Действие: Регистрация в системе лояльности")
#                 await telega.send_message('\n'.join(text))
    else:
        raise HTTPException(status_code=401, detail='Unauthorized')


@app.post("/pronto")
async def pronto(req:Request):
    if req.headers.get('Authorization', '') == config.TILDA2PRONTO_TOKEN:
        params = req.query_params._dict
        if  'application/x-www-form-urlencoded' in req.headers.get('content-type', ''):
            fdata = await req.form()
            params.update(fdata)
        elif 'application/json' in req.headers.get('content-type', ''):
            jdata = await req.json()
            params.update(jdata)
        if 'test' not in params:
            pronto = ProntoSMS()
            return pronto.add_one_client(**params)
    else:
        raise HTTPException(status_code=401, detail='Unauthorized')


@app.post("/webhook")
async def webhook(req:Request):

    params = req.query_params._dict
    if  'application/x-www-form-urlencoded' in req.headers.get('content-type', ''):
        fdata = await req.form()
        params.update(fdata)
    elif 'application/json' in req.headers.get('content-type', ''):
        jdata = await req.json()
        params.update(jdata)

    if params['subscriptionPassword'] == config.WEBHOOK_PASSWORD:
        print(params)
#         filter doubles
        if {'changedOn', 'customerId'} < set(params):
            cached_file = Path("/tmp/iiko/webhook")
            try:
                isodt = lambda f: datetime.fromisoformat('+'.join(a if i else a[:-1] for i, a in enumerate(f.split('+'))))
                cached_file.parent.mkdir(parents=True, exist_ok=True)
                cached_params = json.loads(cached_file.read_text()) if cached_file.is_file() else []
                cached_params = list(filter(lambda m: isodt(params['changedOn']).timestamp() - isodt(m['changedOn']).timestamp() < 3600, cached_params))
                if any(map(lambda m: m['changedOn'] == params['changedOn'] and m['customerId'] == params['customerId'], cached_params)):
                    return

                cached_params.append(params)
                cached_file.write_text(json.dumps(cached_params))
            except Exception as e:
                print('Error in filter doubles:', e)
                cached_file.unlink(missing_ok=True)

        iiko = iikoapi.Api_iiko()
        text = []
        if 'customerId' in params:
            cinfo = iiko.get_customer_info(params['customerId'], atype='id')
            text = iiko.format_guest_info(cinfo)
            text.append(f"Действие: {params.get('transactionType', '')}")

        if {'walletId', 'sum'} < set(params):
            if abs(params['sum']) < 1:
                return
            wallet = next((w for w in cinfo['walletBalances'] if w['id'] == params['walletId']), None)
            if wallet:
                text.append(f"{wallet['name']}: {params['sum']}")
                text.append(f"Баланс: {wallet['balance']}")

        text.append(params.get('text', ''))
        await telega.send_message('\n'.join(text))
    else:
        raise HTTPException(status_code=401, detail='Unauthorized')


if __name__ == "__main__":
    uvicorn.run("tilda:app", host="127.0.0.1", port=23986, workers=1)

