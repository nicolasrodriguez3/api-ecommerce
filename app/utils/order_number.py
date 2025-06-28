import random
import datetime

def generate_order_number():
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d%H%M%S")
    rand_num = random.randint(1000, 9999)
    return f"ORD-{date_str}-{rand_num}"