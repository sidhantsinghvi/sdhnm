def is_int(x):
    try:
        int(x)
        return True
    except Exception:
        return False