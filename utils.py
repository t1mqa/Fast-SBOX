from datetime import datetime

AVAILABLE_PROXIES = []

def get_current_time() -> str:
    """
    Возвращает текущее время в формате [дд.мм.гггг чч:мм:сс].
    """
    now = datetime.now()
    return now.strftime("[%d.%m.%Y %H:%M:%S]")


def log(data: str):
    print(f"{get_current_time()} {data}")