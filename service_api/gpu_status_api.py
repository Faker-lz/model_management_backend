'''
Author: WLZ
Date: 2024-04-08 11:23:02
Description: 
'''
from util import connect_ssh, update_gpu_status_history, get_gpus_status
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from websockets.exceptions import ConnectionClosedOK
from data_schema import SSH, SshInfo as sif
from custom_exception import SshNotExist
from paramiko import SSHClient
from config import sys_conf
from log import logger
from util import shift
import asyncio
import json

gpu_api_router = APIRouter()

@gpu_api_router.websocket("/ws/gpu_status")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_ip, client_port = websocket.client
    try:
        ssh_data = await websocket.receive_text()
        ssh_data = json.loads(ssh_data)
        ssh_detail_data = await sif.filter(hostname=ssh_data['hostname'], ssh_port=ssh_data['port'], 
                                           username=ssh_data['username'], user=ssh_data['user']).first()
        
        if ssh_detail_data is None:
            raise SSHClient()
        
        ssh = SSH(hostname=ssh_detail_data.hostname,
                  ssh_port=ssh_detail_data.ssh_port,
                  username=ssh_detail_data.username,
                  password=ssh_detail_data.password)
        with connect_ssh(**ssh.model_dump()) as ssh_client:
            gpu_status_histories = {}
            history_length = sys_conf.gpu_history_length
            while True:
                gpus_status = await get_gpus_status(client=ssh_client)

                for gpu_status in gpus_status:
                    update_gpu_status_history(gpu_status_histories, gpu_status, history_length)
                
                # 将GPU状态发送给客户端
                await websocket.send_text(json.dumps(gpu_status_histories))
                
                # 每隔一定时间查询一次GPU状态
                await asyncio.sleep(5) 
    except WebSocketDisconnect:
        logger.info(f"\t{client_ip}:{client_port}连接异常断开")
    except ConnectionClosedOK:
        logger.info(f"\t{client_ip}:{client_port}客户端断开连接")


