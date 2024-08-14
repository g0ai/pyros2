
from icecream import ic


def log(out, mode="default", pretty=False):
    if pretty:
        ic(out)
    else:
        print(out)

def log_p(out, mode="default"):
    log(out, mode, pretty=True)

