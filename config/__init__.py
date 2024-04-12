from .conf import MysqlConfig, RunConfig, SystemConfig

my_conf = MysqlConfig()
run_conf = RunConfig()
sys_conf = SystemConfig()

__all__ = [
    'my_conf',
    'run_conf',
    'sys_conf'
]