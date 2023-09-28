#!/usr/bin/env python3
'''
Created on 25 июл. 2023 г.

@author: demon
'''
import uvicorn
from fastapi import FastAPI, Request
import datetime

import config
from prontosms import ProntoSMS

app = FastAPI(openapi_url=None, root_path='/service')


@app.get("/User/GetOwnBalance")
async def user_getownbalance(apiKey:str):
    if apiKey == config.MOBIZON_API_KEY:
        pronto = ProntoSMS()
        r = pronto.get_balance()
        return {
            "code":0,
            "data":{
                "balance":r['money']['value'],
                "currency":r['money']['currency']
            },
            "message":""
        }


@app.get('/Message/SendSmsMessage')
@app.post('/Message/SendSmsMessage')
async def send_message(req:Request):
    params = req.query_params._dict
    if  'application/x-www-form-urlencoded' in req.headers.get('content-type', ''):
        fdata = await req.form()
        params.update(fdata)
    elif 'application/json' in req.headers.get('content-type', ''):
        jdata = await req.json()
        params.update(jdata)
    print(params)
    if params['apiKey'] == config.MOBIZON_API_KEY:
        phones = params['recipient']
        text = params['text']
        sender = params['from']
        name_delivery = params.get('params', {}).get('name')
        time_send = params.get('params', {}).get('deferredToTs')
        if time_send:
            time_send = datetime.datetime.strptime(time_send, "%Y-%m-%d %H:%M:%S")
        else:
            time_send = datetime.datetime.now()
        validity_period = params.get('params', {}).get('validity', 1440)
        if validity_period:
            validity_period = time_send + datetime.timedelta(minutes=int(validity_period))

        pronto = ProntoSMS()
        r = pronto.send_sms(text=text, phones=[phones], sender=sender, name_delivery=name_delivery,
                        time_send=f"{time_send:%Y-%m-%d %H:%M}", validity_period=f"{validity_period:%Y-%m-%d %H:%M}")
        return {'campaignId': 1,
                'messageId': r['sms'][0].get('id_sms'),
                'status': 2 if r['sms'][0]['action'] == 'send' else 1
                }


if __name__ == "__main__":
    uvicorn.run("mobizon:app", port=23987)

