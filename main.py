#!/usr/bin/env python3
'''
Created on 25 июл. 2023 г.

@author: demon
'''
import uvicorn
from fastapi import FastAPI, Request

import iikoapi

app = FastAPI(openapi_url=None)


@app.get("/iiko")
@app.post("/iiko")
async def tilda(req:Request):
    params = req.query_params._dict
    if  'application/x-www-form-urlencoded' in req.headers['content-type']:
        fdata = await req.form()
        params.update(fdata)
    elif 'application/json' in req.headers['content-type']:
        jdata = await req.json()
        params.update(jdata)
    if 'test' not in params:
        iiko = iikoapi.Api_iiko()
        return iiko.create_or_update(**params)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080)

