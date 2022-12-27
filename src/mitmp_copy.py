import asyncio
from collections import deque
from contextlib import suppress
import threading
import time
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
from log.logger import Logs
from dotenv import load_dotenv
from utils.util import get_env

log = Logs()
load_dotenv()
MITMHOST = get_env("MITMHOST")
MITMPORT = int(get_env("MITMPORT"))
CERT_PATH = "src/mitm-certs"


class Addon(object):
    def __init__(self, dq: deque) -> None:
        self.dq = dq

    def request(self, flow):
        # examine request here
        pass

    def response(self, flow):
        # print(flow.request)
        self.dq.append(flow)


class MitmManagement(threading.Thread):
    mitmhost = MITMHOST
    mitmport = MITMPORT
    confdir = CERT_PATH
    dumpmaster: DumpMaster

    def __init__(self, dq) -> None:
        super().__init__()
        self.dq = dq
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.options = Options(
            listen_host=self.mitmhost,
            listen_port=self.mitmport,
            confdir=self.confdir,
            http2=True,
        )
        self.dumpmaster = None

    async def run_mitm(self):
        self.dumpmaster = DumpMaster(
            self.options, with_termlog=False, with_dumper=False
        )
        ad = Addon(self.dq)
        self.dumpmaster.addons.add(ad)
        self.dq = ad.dq

        log.info(f"mitmproxy start")
        await self.dumpmaster.run()

    def shutdown(self):
        if self.dumpmaster is not None:
            self.dumpmaster.shutdown()
            log.info(f"mitmproxy shutdown\n")
        self.loop.stop()
        # time.sleep(1)
        self.loop.close()
        with suppress(SystemExit, RuntimeError):
            if self.loop.is_closed:
                return
        raise Exception("loop not closed")

    def run(self):
        print(f"Starting thread {self.name}")
        asyncio.set_event_loop(self.loop)
        with suppress(SystemExit, RuntimeError):
            self.loop.run_until_complete(self.run_mitm())
        print(f"The threads {self.name} is finished")


while True:
    dq = deque()
    mm = MitmManagement(dq)
    mm.daemon = True
    mm.start()

    time.sleep(2)

    mm.shutdown()
    mm.join()
    del mm
