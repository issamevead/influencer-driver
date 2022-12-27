from contextlib import suppress
import subprocess
from enum import Enum
import sched
import time
from log.logger import Logs
from utils.util import get_env, kill_process
from dotenv import load_dotenv

load_dotenv()

PATH_PROFILES = get_env("PATH_PROFILES")
PROXYCHAINS_CONF_PATH = "/etc/proxychains4.conf"
LOCAL_CONF_PATH = get_env("LOCAL_CONF_PATH")
MAIN = get_env("MAIN")
s = sched.scheduler(time.time, time.sleep)
logs = Logs()


class Network(Enum):
    FACEBOOK: 1
    INSTAGRAM: 2


def get_profiles(data_path: str):
    print(data_path)
    with open(data_path, "r") as f:
        data = []
        for line in f.readlines():
            splitedline = line.split(" ")
            data.append(
                {
                    "network": splitedline[0],
                    "username": splitedline[1],
                    "password": splitedline[2],
                    "proxy": splitedline[3],
                }
            )
    return data


def update_pchain_conf(config_path, proxy):
    with suppress(PermissionError):
        proxyparsed = proxy.split(":")

        conf = f"""\ndynamic_chain\nproxy_dns\nremote_dns_subnet 224\ntcp_read_time_out 15000\ntcp_connect_time_out 8000\nlocalnet 127.0.0.0/255.0.0.0\n[ProxyList]\nsocks5 {proxyparsed[0]} {proxyparsed[1]}\n"""

        with open(config_path, "w") as f:
            f.write(conf)
        with open(LOCAL_CONF_PATH, "w") as f:
            f.write(conf)

        with open(config_path, "r") as f:
            print(f.read())
        return True
    return False


def run_c():
    print(f"RUN_C {time.time()}")
    profiles = get_profiles(PATH_PROFILES)
    print(profiles)
    for profile in profiles:
        updated = update_pchain_conf(PROXYCHAINS_CONF_PATH, profile.get("proxy"))
        # time.sleep(20)
        if updated:
            p = subprocess.run(
                [
                    "proxychains4",
                    "python3",
                    MAIN,
                    profile.get("network"),
                    profile.get("username"),
                    profile.get("password"),
                ]
            )

    logs.info("next cycle will be in 2Hrs")
    s.enter(60 * 60 * 2, 0, run_c)


if __name__ == "__main__":
    s.enter(0, 0, run_c)
    s.run()
