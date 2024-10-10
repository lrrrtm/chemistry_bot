from flet import ScrollMode

screens_config = {
    'login': {
        'scroll': None,
        'appbar': {
            'visible': True,
            'title': "Авторизация",
            'leading': {
                'visible': False,
                'action': None,
                'action_context': None
            }
        }
    },
    'users': {
        'scroll': ScrollMode.AUTO,
        'appbar': {
            'visible': True,
            'title': "Пользователи",
            'leading': {
                'visible': True,
                'action': "drawer",
                'action_context': None
            }
        }
    },
    'system_status': {
        'scroll': ScrollMode.AUTO,
        'appbar': {
            'visible': True,
            'title': "Состояние системы",
            'leading': {
                'visible': True,
                'action': "drawer",
                'action_context': None
            }
        }
    },
    'app_info': {
        'scroll': None,
        'appbar': {
            'visible': True,
            'title': "О приложении",
            'leading': {
                'visible': True,
                'action': "drawer",
                'action_context': None
            }
        }
    },
    'ege': {
        'scroll': None,
        'appbar': {
            'visible': True,
            'title': "Вопросы КИМ ЕГЭ",
            'leading': {
                'visible': True,
                'action': "drawer",
                'action_context': None
            }
        }
    },
    'topics': {
        'scroll': None,
        'appbar': {
            'visible': True,
            'title': "Вопросы тренировок",
            'leading': {
                'visible': True,
                'action': "drawer",
                'action_context': None
            }
        }
    },

}
