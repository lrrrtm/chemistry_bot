from urllib.parse import urlparse, parse_qs
import flet as ft

def main(page: ft.Page):
    page.title = "ХимБот"
    page.add(ft.Text('Панель управления'))

    page.route = "/stats?uuid=8&tid=409801981&work=10"
    url_params = {key: int(value[0]) for key, value in parse_qs(urlparse(page.route).query).items()}

    if all(key in url_params for key in ['uuid', 'tid', 'work']):
        print('ok')
    else:
        print('url keys error')

if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir="D:/repos/chemistry_bot/flet_apps/assets",
        view=None,
        port=6001
    )