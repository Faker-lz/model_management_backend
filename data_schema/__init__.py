'''
Author: WLZ
Date: 2024-04-08 18:53:30
Description: 
'''
from .model_api_schema import Model, GetModelStatus, StartModelTrain, TrainModelCommand, ModelOnline, ModelOnlineUrl, SSH, ModelOffline
from .model_api_response import ResponseModel, response_model
from tortoise.contrib.pydantic import pydantic_model_creator
from .model_mysql_schema import ModelManagement, ModelUrlMap, SshInfo
from pydantic import BaseModel, create_model
from typing import Type, Callable
from fastapi import Request


ModelManagementPydantic = pydantic_model_creator(ModelManagement)
ModelUrlMapPydantic = pydantic_model_creator(ModelUrlMap)
SshInfoPydantic = pydantic_model_creator(SshInfo)
