
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options


class Addon(object):
    def __init__(self):
        pass

    def request(self, flow):
        # examine request here
        pass

    def response(self, flow):
        # examine response here
        pass


def process():
    options = Options(
        listen_host="0.0.0.0",
        listen_port=4141,
        http2=True,
    )
    m = DumpMaster(options, with_termlog=False, with_dumper=False)
    m.addons.add(Addon())

    try:
        print("starting mitmproxy")
        m.run()
    except KeyboardInterrupt:
        m.shutdown()


if __name__ == "__main__":
    process()
