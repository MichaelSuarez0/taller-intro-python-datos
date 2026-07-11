import time
from functools import wraps


def medir_tiempo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fin = time.time()
        print(f"La función '{func.__name__}' tardó {fin - inicio:.6f} segundos")
        return resultado

    return wrapper
