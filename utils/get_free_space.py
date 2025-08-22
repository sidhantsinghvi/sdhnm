import shutil


def get_free_space_in_gb(path):
    total, used, free = shutil.disk_usage(path)
    total = total // (2**30)
    used = used // (2**30)
    free = free // (2**30)
    return total,used,free
