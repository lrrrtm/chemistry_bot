import subprocess
from flet import icons

services = [
    {
        'name': "База данных",
        'filename': "mysql.service",
        'flet_icon': icons.DATASET
    },
    {
        'name': "Сервер Nginx",
        'filename': "nginx.service",
        'flet_icon': icons.COMPUTER
    },
    {
        'name': "Telegram-бот",
        'filename': "chemistry_bot.service",
        'flet_icon': icons.TELEGRAM
    },
    {
        'name': "Статистика",
        'filename': "chemistry_stats.service",
        'flet_icon': icons.QUERY_STATS
    },
    # {
    #     'name': "Панель управления",
    #     'filename': "chemistry_control.service",
    #     'flet_icon': icons.CONTROL_CAMERA
    # }
]

service_status_translation = {
    "active": "🟢",
    "inactive": "⛔",
    "failed": "⛔",
    "activating": "🟡",
    "deactivating": "🔴",
    "reloading": "🔄",
    "unknown": "⛔"
}


def get_system_status():
    result = []
    for service in services:
        try:
            status = subprocess.run(['systemctl', 'is-active', service['filename']], capture_output=True, text=True)
            service_status = status.stdout.strip()
            result.append(
                {
                    'flet_icon': service['flet_icon'],
                    'filename': service['filename'],
                    'name': service['name'],
                    'status': service_status_translation[service_status]
                }
            )
        except Exception as e:
            result.append(
                {
                    'flet_icon': service['flet_icon'],
                    'filename': service['filename'],
                    'name': service['name'],
                    'status': service_status_translation['unknown']
                }
            )
    return result


def restart_service(filename: str):
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', filename], capture_output=True, text=True)
    except Exception as e:
        print(e)
