import asyncio
from collections import deque
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
from log.logger import Logs
from dotenv import load_dotenv
from utils.util import get_env

log = Logs()
load_dotenv()
MITMHOST = get_env("MITMHOST")
MITMPORT = get_env("MITMPORT")


class Addon(object):
    def __init__(self, dq: deque) -> None:
        self.dq = dq

    def request(self, flow):
        # examine request here
        pass

    def response(self, flow):
        # print(flow.request)
        self.dq.append(flow)


def run_mitm(dq: deque):
    async def process(dq):
        options = Options(
            listen_host=MITMHOST,
            listen_port=int(MITMPORT),
            http2=True,
            confdir="src/mitm-certs",
        )
        asyncio.set_event_loop(asyncio.new_event_loop())
        # r = asyncio.new_event_loop()
        # r.run_forever()
        m = DumpMaster(options, with_termlog=False, with_dumper=False)
        ad = Addon(dq)
        m.addons.add(ad)
        dq = ad.dq

        try:
            log.info(f"mitmproxy start")
            await m.run()
        except KeyboardInterrupt:
            m.shutdown()

    asyncio.run(process(dq=dq))
