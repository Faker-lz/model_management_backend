'''
Author: WLZ
Date: 2024-04-08 18:55:25
Description: 
'''
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from back_ground_tasks import check_and_update_projects
from util import ThreadPoolExecutorSingleton
from contextlib import asynccontextmanager
from util import TortoiseManager as tm
from fastapi import FastAPI
from config import sys_conf
from service_api import *

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # init tortoise
    await tm.init()
    scheduler.start()
    scheduler.add_job(
        check_and_update_projects,
        trigger=IntervalTrigger(seconds=sys_conf.bt_exec_interval),
        id="project_status_check",                                       # 给任务一个ID
        replace_existing=True,                                           # 如果任务已经存在，则替换它的配置
    )
    yield
    await tm.close()
    ThreadPoolExecutorSingleton.shutdown()

app = FastAPI(lifespan=lifespan)

app.include_router(gpu_api_router, prefix='/gpu', tags=['获取gpu状态的路由'])
app.include_router(model_api_router, prefix='/model', tags=['模型相关路由'])