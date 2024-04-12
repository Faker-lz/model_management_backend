'''
Author: WLZ
Date: 2024-04-07 18:39:51
Description: 
'''

class MysqlConfig:
    # host = '127.0.0.1'
    host = '10.245.143.74'
    prot = 3306
    user = 'root'
    password = 'root'
    # databse = 'machine_learing_service'
    databse = 'test'

class RunConfig:
    host = '10.245.143.71'
    port = 8088

class SystemConfig:
    max_workers = 20
    bt_exec_interval = 30       # 后台轮询检查模型状态的时间间隔
    gpu_history_length = 35     # gpu状态历史长度