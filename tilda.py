#!/usr/bin/env python3
'''
Created on 25 июл. 2023 г.

@author: demon
'''
import uvicorn
from fastapi import FastAPI, Request
import config
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
                return iiko.create_or_update(**params)
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

        iiko = iikoapi.Api_iiko()
        text = []
        if 'customerId' in params:
            cinfo = iiko.get_customer_info(params['customerId'], atype='id')
            text.extend([f"Гость: {cinfo['name']} {cinfo.get('surname', '')}", f"Телефон: {cinfo['phone']}"])
            if cinfo.get('email'):
                text.append(f"Email: {cinfo['email']}")
            text.append(f"Действие: {params.get('transactionType', '')}")

        if set(['walletId', 'sum']) < set(params):
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
    uvicorn.run("tilda:app", host="127.0.0.1", port=23986, workers=2)

