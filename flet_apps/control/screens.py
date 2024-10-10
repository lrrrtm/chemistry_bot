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
            'title': "Ученики",
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
    'ege_questions': {
        'scroll': ScrollMode.AUTO,
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
    'topics_questions': {
        'scroll': ScrollMode.AUTO,
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
    'change_password': {
        'scroll': True,
        'appbar': {
            'visible': True,
            'title': "Изменение пароля",
            'leading': {
                'visible': True,
                'action': "drawer",
                'action_context': None
            }
        }
    },
    'user_info': {
        'scroll': ScrollMode.AUTO,
        'appbar': {
            'visible': True,
            'title': "Профиль ученика",
            'leading': {
                'visible': True,
                'action': "change_screen",
                'action_context': "users"
            }
        }
    },
    'topics_list': {
        'scroll': ScrollMode.AUTO,
        'appbar': {
            'visible': True,
            'title': "Темы тренировок",
            'leading': {
                'visible': True,
                'action': "drawer",
                'action_context': None
            }
        }
    },

}
