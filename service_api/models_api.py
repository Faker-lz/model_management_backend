'''
Author: WLZ
Date: 2024-04-07 21:49:51
Description: 
'''
from data_schema import response_model, ResponseModel, StartModelTrain, ModelOnline, ModelOnlineUrl, \
                        TrainModelCommand, ModelManagementPydantic, ModelManagement as mm, ModelUrlMap as mup, \
                        ModelUrlMapPydantic, SshInfo as sif, SshInfoPydantic, ModelOffline
from util import connect_ssh, dict_to_cmd_args, ssh_exec_command, tortoise_upsert
from fastapi import Depends, APIRouter, Body
from starlette.status import HTTP_201_CREATED
# from tortoise.query_utils import Q
from custom_exception import ModelNotExist, ModelOnlineFail, ModelNotReady
from paramiko import SSHException
from datetime import time, datetime
from log import logger
import pytz
import json
import os

model_api_router = APIRouter()

@model_api_router.post("/model_train", response_model=ResponseModel)
async def model_start_train(model_info: StartModelTrain = Body(...)):
    try:
        with connect_ssh(**model_info.ssh.model_dump()) as ssh_client:
            command = f"source {model_info.conda_path} {model_info.conda_env} && cd {model_info.project_dir} &&"
            params = model_info.params
            train_model_command = TrainModelCommand(
                **params,
                experiment_name= params['dataset'] + '_'+ params['model_name'] + '_' + params['model_version']
            )
            command += ' nohup ' + model_info.train_cmd + dict_to_cmd_args(train_model_command.model_dump()) + f' >nohup_out_{train_model_command.experiment_name}.log 2>&1 &'
            logger.info(command)
            ssh_client.exec_command(command=command)
        data_resulat = await mm.create(
                dadp_project_name = model_info.dadp_project_name,
                model_name = params['model_name'],
                model_version = params['model_version'],
                address = model_info.ssh.hostname,
                model_project_dir = model_info.project_dir,
                model_log_path = os.path.normpath(os.path.join(train_model_command.output_dir, train_model_command.log_dir , train_model_command.experiment_name + '.log')).replace(os.sep, "/"),
                model_save_path = os.path.normpath(os.path.join(train_model_command.output_dir, train_model_command.experiment_name, './model/model_last.pth')).replace(os.sep, "/"),
                task_status = 0,
                task_duration = time(0, 0, 0),
                user = model_info.user,
                if_online = 0,
                capability = model_info.capability,
                command = command,
                ssh_hostname = model_info.ssh.hostname,
                ssh_port = model_info.ssh.ssh_port,
                ssh_user = model_info.ssh.username,
                ssh_password = model_info.ssh.password,
                conda_env = model_info.conda_env,
                conda_path = model_info.conda_path
        )
        pydantic_data_result = await ModelManagementPydantic.from_tortoise_orm(data_resulat)
        message = "Model training initiated successfully."
        code = 200
        return response_model(
            code=code,
            message=message,
            data=pydantic_data_result
        )
    except Exception as e:
        # Log the exception or handle it as needed
        logger.error(f"An error occurred: {str(e)}")
        return response_model(code=HTTP_201_CREATED, message=f"An error occurred: {str(e)}", data=None)

@model_api_router.post("/model_online", response_model=ResponseModel)
async def online_model(model_info: ModelOnline = Body(ModelOnline)):
    try:
        # query = None
        # for capability, model_version in model.capability_and_version:
        #     condition = Q(capability=capability, model_version=model_version)
        #     if query is None:
        #         query = condition
        #     else:
        #         query |= condition
        # online_model = mm.filter(query).all()
        # model_mapping_json = 
        # 查询目标模型是否存在且训练好
        # TODO 目前模型存在1对多的问题，所以先这么写，后续再提高普适性
        select_models = await mm.filter(model_name=model_info.model_name, 
                                       dadp_project_name=model_info.dadp_project_name,
                                       user=model_info.user,
                                       task_status=1,
                                    #    capability=model_info.capability,
                                    #    model_version=model_info.model_version
                                       ).all()
        
        if select_models is None:
            raise ModelNotExist()
        
        # 远程上线
        with connect_ssh(hostname=select_models[0].ssh_hostname, 
                        ssh_port=select_models[0].ssh_port, 
                        username=select_models[0].ssh_user, 
                        password=select_models[0].ssh_password) as ssh_client:
            online_command = f"source {select_models[0].conda_path} {select_models[0].conda_env} && cd {select_models[0].model_project_dir} && "
            online_command += model_info.online_command if model_info.online_command is not None else "nohup bash scripts/api_setup.sh >setup.log 2>&1 &"
            # 模型启动是耗时操作，不能够等待返回
            ssh_client.exec_command(command=online_command)
            online_result = await ssh_exec_command(client=ssh_client, command=f"ps -ef | grep '{online_command}' | grep -v grep")
            online_result = '111'
            sftp_client = ssh_client.open_sftp()
            sftp_file = sftp_client.open(os.path.normpath(os.path.join(select_models[0].model_project_dir, './config/api_list.json')).replace(os.sep, '/'))
            api_list = json.loads(sftp_file.read().decode())
            sftp_client.close()

        response_data_list = []
        # 如果上线命令成功运行则将URL和ssh数据入库, 并且更新对应模型的所有功能model都为上线状态
        if len(online_result) > 0:
            code=200
            message='Model successfully online'
            for api in api_list:
                # TODO 模型启动接口应该读出来，而不是指定
                api['url'] = 'http://' + select_models[0].ssh_hostname + ':10139' + api['url']
                api['model_name'] = model_info.model_name
                api['capacity_name'] = api.pop('name')
                # 这里的逻辑应该是更新插入而非直接插入
                update_api_result = await tortoise_upsert(mup, query_fields={'model_name': api['model_name'], 'capacity_name': api['capacity_name']},
                             update_fields={'url': api['url'], 'alias': api['alias']},
                             data=api)
                response_data_list.append(await ModelUrlMapPydantic.from_tortoise_orm(update_api_result))
            # ssh数据入库
            update_ssh_result = await tortoise_upsert(sif, query_fields={'hostname': select_models[0].ssh_hostname, 
                                                                         'ssh_port': select_models[0].ssh_port, 
                                                                         'username': select_models[0].ssh_user, 
                                                                         'user': model_info.user},
                                                            update_fields={'password': select_models[0].ssh_password})
            # 所有models上线状态更新
            online_time = datetime.now(pytz.utc)
            for select_model in select_models:
                await mm.filter(id=select_model.id).update(if_online=1, online_time=online_time, online_command=online_command)
            response_data_list.append(await SshInfoPydantic.from_tortoise_orm(update_ssh_result))                                            
            return response_model(
                message=message,
                code=code,
                data=response_data_list)
        else:
            raise ModelOnlineFail()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return response_model(code=HTTP_201_CREATED, message=f"An error occurred: {str(e)}", data=None)

@model_api_router.get("/model_offline", response_model=ResponseModel)
async def offline_model(model_info: ModelOffline=Depends(ModelOffline)):
    try:
        # TODO 目前模型存在1对多的问题，所以先这么写，后续再提高普适性
        select_models = await mm.filter(model_name=model_info.model_name, 
                                        dadp_project_name=model_info.dadp_project_name,
                                        user=model_info.user,
                                        task_status=1,
                                    #    capability=model_info.capability,
                                    #    model_version=model_info.model_version
                                        ).all()
        
        if select_models is None:
            raise ModelNotExist()
        
        with connect_ssh(hostname=select_models[0].ssh_hostname, 
                            ssh_port=select_models[0].ssh_port, 
                            username=select_models[0].ssh_user, 
                            password=select_models[0].ssh_password) as ssh_client:
            online_command = select_models[0].online_command
            find_online_pid_cmd = f"pgrep -f '{online_command}'"
            _, run_command_stdout, _ = ssh_client.exec_command(find_online_pid_cmd)
            pids = run_command_stdout.read().decode().strip().split('\n')

            for pid in pids:
                logger.info(f'Kill run command process in in {select_models[0].ssh_hostname}...')
                if pid.isdigit():
                    logger.info(f"Killing PID {pid}...")
                    kill_cmd = f"kill -9 {pid}"
                    ssh_client.exec_command(kill_cmd)
                    logger.info(f"PID {pid} has been killed.")
            
            logger.info(f'Kill webserver process in {select_models[0].ssh_hostname}...')

            # TODO 额外获取服务启动端口
            webserver_port = 10139
            find_webserver_pid_cmd = f"ss -ltnp | grep :{webserver_port} | awk '{{print $6}}' | cut -d',' -f2 | cut -d'=' -f2"
            _, find_webserver_stdout, _ = ssh_client.exec_command(find_webserver_pid_cmd)
            pid = find_webserver_stdout.read().decode().strip()

            if pid:
                logger.info(f"Killing PID {pid}...")
                kill_cmd = f"kill -9 {pid}"
                ssh_client.exec_command(kill_cmd)
                logger.info(f"PID {pid} has been killed.")
            else:
                logger.info(f"No process found listening on port {webserver_port}.")
        for select_model in select_models:
                    await mm.filter(id=select_model.id).update(if_online=0, online_time=None, online_command=None)
        return response_model(
            data=None,
            message="Model successfully offline",
            code=200
        )
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return response_model(
            data=None,
            message=f"An error occurred: {str(e)}",
            code=HTTP_201_CREATED
        )

    
@model_api_router.get("/model_online_url", response_model=ResponseModel)
async def online_model(model_info: ModelOnlineUrl = Depends(ModelOnlineUrl)):
    try:
        filters = {'model_name': model_info.model_name}
        if model_info.capability_name is not None:
            filters['capacity_name'] = model_info.capability_name
        model_url_map = await mup.filter(**filters).all()
        model_url_map_serialization = [await ModelUrlMapPydantic.from_tortoise_orm(data) for data in model_url_map]
        return response_model(
            data=model_url_map_serialization,
            message="Get urls successfully",
            code=200
        )
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return response_model(
            data=None,
            message=f"An error occurred: {str(e)}",
            code=HTTP_201_CREATED
        )


