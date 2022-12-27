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
MITMPORT = int(get_env("MITMPORT"))
CERT_PATH = "src/mitm-certs"


class Addon(object):
    def __init__(self, dq: deque) -> None:
        self.dq = dq

    def request(self, flow):
        # examine request here
        pass

    def response(self, flow):
        print(flow.request)
        self.dq.append(flow)


def run_mitm(dq: deque):
    async def process(dq):
        options = Options(
            listen_host=MITMHOST, listen_port=MITMPORT, confdir=CERT_PATH, http2=True
        )
        asyncio.set_event_loop(asyncio.new_event_loop())
        dumpmaster = DumpMaster(options, with_termlog=True, with_dumper=False)
        ad = Addon(dq)
        dumpmaster.addons.add(ad)
        dq = ad.dq

        try:
            log.info(f"mitmproxy start")
            await dumpmaster.run()
        except KeyboardInterrupt:
            dumpmaster.shutdown()

    asyncio.run(process(dq=dq))
