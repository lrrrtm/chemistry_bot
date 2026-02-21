import subprocess
import os

services = [
    {
        'name': "База данных",
        'container': "chemistry_db",
        'icon': "🗄️"
    },
    {
        'name': "Сервер Nginx",
        'container': "chemistry_nginx",
        'icon': "🌐"
    },
    {
        'name': "Telegram-бот",
        'container': "chemistry_bot",
        'icon': "🤖"
    },
    {
        'name': "API / Фронтенд",
        'container': "chemistry_api",
        'icon': "⚙️"
    },
]

service_status_translation = {
    "running": "🟢",
    "exited": "⛔",
    "stopped": "⛔",
    "restarting": "🔄",
    "paused": "🟡",
    "dead": "⛔",
    "created": "🟡",
    "unknown": "⛔"
}


def _get_container_status(container_name: str) -> str:
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", container_name],
            capture_output=True, text=True, timeout=5
        )
        status = result.stdout.strip()
        return status if status else "unknown"
    except Exception:
        return "unknown"


def get_system_status():
    result = []
    for service in services:
        status = _get_container_status(service['container'])
        emoji = service_status_translation.get(status, service_status_translation['unknown'])
        result.append({
            'icon': service['icon'],
            'filename': service['container'],  # container name used for restart
            'name': service['name'],
            'status': emoji,
            'status_text': status,
        })
    return result


def restart_service(container_name: str):
    try:
        subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True, text=True, timeout=30
        )
    except Exception as e:
        print(e)
