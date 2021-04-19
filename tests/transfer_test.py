import json
import logging
import tempfile
import time
from collections import namedtuple
from functools import partial
from pathlib import Path
from threading import Thread
from netimpair import Netem
from file_transfer import receiver, sender

Factor = namedtuple(
    "Factor",
    ("name", "default", "min", "max", "jump", "type"),
    defaults=(0, 0, 100, 10, float),
)


def run_test():
    file = Path("test_file.pdf")
    orig_data = file.read_bytes()
    tempdir = Path(tempfile.mkdtemp("rudp-test"))
    params = {"address": "127.0.0.1", "port": 1060}
    result = {}
    t1 = Thread(target=receiver, kwargs=dict(directory=tempdir, result=result, **params))
    t2 = Thread(target=sender, kwargs=dict(file=file, **params))
    t1.start()
    time.sleep(0.5)
    t2.start()
    t1.join()
    t2.join()
    new_file = tempdir / file.name
    if not new_file.exists():
        raise FileNotFoundError("Destination file not found")
    if new_file.read_bytes() != orig_data:
        raise ValueError("Data mismatch")
    if not result:
        raise OSError("Unknown error")
    return result


def main():
    fold = Path("results")
    fold.mkdir(exist_ok=True)
    last_file = max(tuple(fold.iterdir()) or [Path("run_000.json")])
    last_num = int(last_file.stem[-3:])

    results = {}
    factors = {
        "loss_ratio": Factor("loss_ratio"),
        "dup_ratio": Factor("dup_ratio"),
        "delay": Factor("delay"),
        "jitter": Factor("jitter"),
        "corrupt_ratio": Factor("corrupt_ratio"),
    }
    for factor in factors.values():
        factor_res = {}
        for val in range(factor.min, factor.max, factor.jump):
            netem = Netem("lo")
            netem.initialize()
            manager = partial(netem.emulate, **{factor.name: val})
            with manager():
                try:
                    res = run_test()
                except Exception as e:
                    print(e)
                else:
                    factor_res[val] = res["time"]
            time.sleep(1)
        results[factor.name] = factor_res
    with open(fold / f"run_{last_num + 1:03}.json", "w") as f:
        json.dump(results, f, indent=4)


if __name__ == '__main__':
    for _ in range(10):
        main()
