'''
Author: WLZ
Date: 2024-04-07 19:14:59
Description: 
'''
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from tortoise.models import Model
from typing import Optional
from tortoise import Tortoise
from log import logger
from config import my_conf, sys_conf
from datetime import datetime
import paramiko
import asyncio
import pytz
import os

class TortoiseManager:
    async def init() -> None:
        await Tortoise.init(
        db_url=f'mysql://{my_conf.user}:{my_conf.password}@{my_conf.host}:{my_conf.prot}/{my_conf.databse}',
        modules={'model_mysql_schema': ['data_schema.model_mysql_schema']}
    )
        await Tortoise.generate_schemas()
    
    async def close() -> None:
        await Tortoise.close_connections()


class ThreadPoolExecutorSingleton:
    _instance: Optional[ThreadPoolExecutor] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ThreadPoolExecutor(max_workers=sys_conf.max_workers)
        return cls._instance

    @classmethod
    def shutdown(cls):
        if cls._instance is not None:
            cls._instance.shutdown(wait=True)
            cls._instance = None

def get_thread_pool_executor():
    return ThreadPoolExecutorSingleton.get_instance()

async def tortoise_upsert(model: Model, query_fields: dict, update_fields: dict, data: dict=None):
    # 尝试获取已存在的记录
    obj = await model.get_or_none(**query_fields)
    
    if obj:
        # 如果存在，更新指定的字段
        for field, value in update_fields.items():
            setattr(obj, field, value)
        await obj.save()
    else:
        # 如果不存在，创建新的记录
        if data is None:
            data = query_fields | update_fields
        obj = await model.create(**data)
    
    return obj


@contextmanager
def connect_ssh(hostname: str, ssh_port: int, username: str, password:str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname, ssh_port, username, password
        )
        yield client
    except paramiko.AuthenticationException:
        logger.info("\t认证失败，请检查用户名和密码！")
    except paramiko.SSHException as sshException:
        logger.info("\t无法建立SSH连接：%s" % sshException)
    finally:
        client.close()

async def ssh_exec_command(client: paramiko.SSHClient, command:str):
    loop = asyncio.get_running_loop()
    _, stdout, _  = await loop.run_in_executor(
        get_thread_pool_executor(),
        client.exec_command,
        command
    )
    return stdout.read().decode()

def dict_to_cmd_args(params: dict) -> str:
    args = []
    for key, value in params.items():
        args.append(f" --{key} {value}")
    return ''.join(args)

def shift(array, size, push):
    if len(array) < size:
        array.append(push)
    else:
        array.pop(0)
        array.append(push)

def update_gpu_status_history(gpu_status_histories, gpu_status, history_length):
    uuid = gpu_status["uuid"]
    if uuid not in gpu_status_histories:
        gpu_status_histories[uuid] = {
            # "gpuUtil": [0] * history_length,
            "memTotal": [0] * history_length,
            "memUsed": [0] * history_length,
            "memFree": [0] * history_length,
            "temp_gpu": [0] * history_length
        }
    for key in gpu_status_histories[uuid].keys():
        shift(gpu_status_histories[uuid][key], history_length, gpu_status[key])


def check_project_status(client: paramiko.SSHClient, run_command, log_path):
    # log_path路径一定要是绝对路径
    cmd = f"""
    if grep -q "Logger exited(0)." {log_path}; then
    echo 1
    else
    if ps aux | grep -v grep | grep "{run_command}" > /dev/null; then
        echo 0
    else
        echo 2
    fi
    fi
    """

    try:
        _, status_stdout, _ = client.exec_command(cmd)
        status = int(status_stdout.read().decode().strip())
        assert status in [0, 1, 2], f"Unexpected status value: {status}"
        _, time_stdout, _ = client.exec_command(f"tail -n 1 {log_path}")
        date_str = time_stdout.read().decode().split('|')[0].strip()
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        date = date.replace(tzinfo=pytz.utc)
        logger.info(f'get status {status}, finished time:{date_str}')
        return status, date
    except ValueError as e:
        # 处理可能的转换错误，可能需要根据你的具体需求来决定如何处理这种情况
        raise ValueError(f"Fail to check model status, {str(e)}")

def safeFloatCast(strNumber):
    try:
        number = float(strNumber)
    except ValueError:
        number = float('nan')
    return number

async def get_gpus_status(client: paramiko.SSHClient):
    command = "nvidia-smi --query-gpu=index,uuid,utilization.gpu,memory.total,memory.used,memory.free,driver_version,name,gpu_serial,display_active,display_mode,temperature.gpu --format=csv,noheader,nounits"

    gpus_result = await ssh_exec_command(client=client, command=command)
    keys = ["deviceIds", "uuid", "gpuUtil", "memTotal", "memUsed", "memFree", "driver", 
            "gpu_name", "serial", "display_active", "display_mode", "temp_gpu"]
    gpus_result_lines = gpus_result.split(os.linesep)
    num_devices = len(gpus_result_lines)

    gpus_status_list = []

    for line in range(num_devices):
        gpus_result_line = gpus_result_lines[line].split(', ')
        deviceInfo = {
            keys[i]: safeFloatCast(gpus_result_line[i])/100 if i == 2 else
                    safeFloatCast(gpus_result_line[i]) if i in [3, 4, 5, 11] else
                    gpus_result_line[i]
            for i in range(len(keys))
        }
        gpus_status_list.append(deviceInfo)
    return gpus_status_list
    
