def first(iterable, condition):
    return next(x for x in iterable if condition(x))
