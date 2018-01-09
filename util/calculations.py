def calculate_average(values):
    try:
        return sum(values) / len(values)
    except ZeroDivisionError:
        return None
