from data_schema import ModelManagement as mm
from util import check_project_status, connect_ssh
from datetime import datetime, timedelta
from log import logger
import os

async def check_and_update_projects():
    try:
        running_projects = await mm.filter(task_status=0)
        if len(running_projects) > 0:
            for project in running_projects:
                with connect_ssh(hostname=project.ssh_hostname, 
                                 ssh_port=project.ssh_port, 
                                 username=project.ssh_user, 
                                 password=project.ssh_password) as ssh_client:
                    model_log_path = os.path.normpath(os.path.join(project.model_project_dir, project.model_log_path)).replace(os.sep, '/')
                    new_status, date = check_project_status(ssh_client, project.command, model_log_path)
                total_duration_since_create  = date - project.created_time
                if new_status == 0:
                    await mm.filter(id=project.id).update(task_status=new_status, task_duration=total_duration_since_create)
                if new_status ==1:
                    await mm.filter(id=project.id).update(task_status=new_status, task_duration=total_duration_since_create, gen_time=date)
    except Exception as e:
        logger.error(f"when check and update project status an error occurred: {str(e)}")
