'''
Author: WLZ
Date: 2024-04-07 19:19:06
Description: 
'''
from tortoise import fields
from tortoise.models import Model

class ModelManagement(Model):
    id = fields.IntField(pk=True)

    created_time = fields.DatetimeField(auto_now_add=True)                  # 创建时间，首次创建时自动设置为当前的时间
    dadp_project_name  = fields.CharField(max_length=255)                   # 项目名称
    model_name = fields.CharField(max_length=255)                           # 模型名称
    model_version = fields.CharField(max_length=255)                        # 模型版本
    address = fields.CharField(max_length=255)                              # 模型主机地址
    model_project_dir = fields.CharField(max_length=255)                    # 模型路径
    model_log_path = fields.CharField(max_length=1023)                      # 模型的日志存储路径
    model_save_path = fields.CharField(max_length=1023)                     # 模型存储路径
    task_status = fields.IntField(min_value=0, max_value=2)                 # 模型状态，0:正在训练 1:成功 2:失败
    task_duration = fields.TimeField()                                      # 模型运行时间，时分秒
    user = fields.CharField(max_length=64) 
    if_online = fields.IntField(min_value=0, max_value=1)                   # 模型是否上线，0:下线 1:上线
    capability = fields.CharField(max_length=255)                           # 模型功能
    command = fields.CharField(max_length=1023)                             # 模型启动时的命令
    online_command = fields.CharField(max_length=1023, null=True)           # 模型上线时在远程运行的命令

    ssh_hostname = fields.CharField(max_length=255)                         # 模型运行主机的远程地址
    ssh_port = fields.IntField()                                            # 模型运行主机的端口
    ssh_user = fields.CharField(max_length=255)                             # 模型运行主机的用户名

    conda_env = fields.CharField(max_length=255)                            # 模型环境的名称
    conda_path = fields.CharField(max_length=1023)                          # conda安装路径
    # TODO 密码加密
    ssh_password = fields.CharField(max_length=255)                         # 模型运行主机的密码

    online_time = fields.DatetimeField(auto_now_add=False, null=True)       # 上线时间
    gen_time = fields.DatetimeField(auto_now_add=False, null= True)         # 

    class Meta:
        # unique_together = ("dadp_project_name", "model_name", "model_version", "address", "user")
        table = 'model_management'

class ModelUrlMap(Model):
    capacity_name = fields.CharField(max_length=255, pk=True)         # 模型功能英文名称
    alias = fields.CharField(max_length=255)                          # 模型功能中文名称
    model_name = fields.CharField(max_length=255)                     # 模型名称
    url = fields.CharField(max_length=255)                            # 模型对应的url

    class Meta:
        table = 'model_url_map'

class SshInfo(Model):
    id = fields.IntField(pk=True)                                     # 主键id
    hostname = fields.CharField(max_length=50)                        # ssh主机
    ssh_port = fields.IntField()                                      # ssh端口
    username = fields.CharField(max_length=100)                       # ssh用户名
    password = fields.CharField(max_length=255)                       # ssh密码
    user = fields.CharField(max_length=100)                           # 用户

    class Meta:
        table = 'ssh_info'