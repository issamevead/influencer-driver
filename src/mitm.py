import mitmproxy
import time
import threading
from copy import deepcopy
from collections import deque

data = {}


class Proxy:
    def response(self, flow):
        data[str(time.time())] = flow.request.url


addons = [Proxy()]


def main(data):
    print("In")
    while True:
        copy_data = deepcopy(data)
        for k in copy_data:
            print(data[k])
            del data[k]


t = threading.Thread(target=main, args=(data,))
t.daemon = True
t.start()
