'''
Author: WLZ
Date: 2024-04-07 21:55:46
Description: 
'''
from pydantic import BaseModel, Field
from typing import Optional

class SSH(BaseModel):
    hostname: str 
    ssh_port: int
    username: str
    password: str

class Model(BaseModel):
    model_name: str
    user: str
    model_version: str
    project_dir: str
    capability: str
    dadp_project_name: str

class GetModelStatus(Model):
    ssh: SSH
    pass

class StartModelTrain(Model):
    ssh: SSH
    conda_path: str = Field(default='/root/miniconda3/bin/activate', description='target host conda path')
    conda_env: str
    train_cmd: str
    params: dict
    model_name: Optional[str] = Field(default=None)
    model_version: Optional[str] = Field(default=None)

    # class Config:
    #     schema_extra = {
    #         'exclude': ['model_name', 'model_version']
    #     }


class TrainModelCommand(BaseModel):
    output_dir: str = Field(default="./output", description="输出目录")
    train_epochs: int = Field(default=1)
    log_dir: str = Field(default="./logs", description="日志目录")      
    experiment_name: str
    checkpoint_dir: str = Field(default="./checkpoint")  
    model_save_dir: str = Field(default="./model")


class ModelOnline(Model):
    online_command: Optional[str] = Field(default=None)
    capability: Optional[str] = Field(default=None)
    # capability_and_version: dict

class ModelOffline(Model):
    pass

class ModelOnlineUrl(BaseModel):
    model_name: str
    capability_name: Optional[str] = Field(None)