import subprocess

services = [
    {
        'name': "База данных",
        'filename': "mysql.service"
    },
    {
        'name': "Сервер Nginx",
        'filename': "nginx.service"
    },
    {
        'name': "\nTelegram-бот",
        'filename': "chemistry_bot.service"
    },
    {
        'name': "Статистика",
        'filename': "chemistry_stats.service"
    },
    {
        'name': "Управление",
        'filename': "chemistry_control.service"
    }
]

service_status_translation = {
    "active": "✅ работает",
    "inactive": "⛔ остановлено",
    "failed": "⛔ завершено",
    "activating": "🟡 активируется",
    "deactivating": "🔴 останавливается",
    "reloading": "🔄 перезагружается",
    "unknown": "⛔ неизвестное состояние"
}


def get_system_status():
    result = []
    for service in services:
        try:
            status = subprocess.run(['systemctl', 'is-active', service['filename']], capture_output=True, text=True)
            service_status = status.stdout.strip()
            result.append(
                {
                    'name': service['name'],
                    'status': service_status_translation[service_status]
                }
            )
        except Exception as e:
            result.append(
                {
                    'name': service['name'],
                    'status': service_status_translation['unknown']
                }
            )
    return result