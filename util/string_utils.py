def _prepare_title(text, char='-'):
    return f'{text.title()}\n{char * len(text)}'


YES = {'y', 'yes', 'yup'}


def _is_yes(should_update):
    return should_update.lower() in YES