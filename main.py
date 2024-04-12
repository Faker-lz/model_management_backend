'''
Author: WLZ
Date: 2024-04-07 17:31:42
Description: 
'''
from fastapi.middleware.cors import CORSMiddleware
from routes import app
from config import *
import uvicorn


origins = [
    "10.245.142.71"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False, 
    allow_methods=["*"], 
    allow_headers=["*"], 
)

if __name__ == '__main__':
    uvicorn.run(app, host=run_conf.host, port=run_conf.port)