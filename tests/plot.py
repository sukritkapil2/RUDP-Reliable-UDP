"""
Group Members

Sukrit 2018A7PS0205H
Kumar Pranjal 2018A7PS0163H
Sneh Lohia 2018A7PS0171H
Pranay Pant 2018A7PS0161H
Dhiraaj Desai 2018A7PS0146H

"""

import json
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt


FILE_SIZE = "46,90,895"  # bytes


def read_results() -> dict:
    results = []
    for file in Path("results").iterdir():
        if file.name.startswith("run_") and file.suffix == ".json":
            results.append(json.loads(file.read_text()))
    return results


def make_dict(data):
    res = defaultdict(lambda: defaultdict(list))
    for result in data:
        for test, info in result.items():
            for percent, time in info.items():
                res[test][percent].append(time)

    return res

def plot(test, data):
    x = [0, 10, 20,30, 40, 50,60, 70,80, 90]
    y = []

    plt.title(f'Netem Test of RUDP - File Size: {FILE_SIZE} bytes')

    for percent, values in data.items():
        for val in values:
            y.append(val)

    plt.plot(x, y)
  
    # naming the x axis
    plt.xlabel(f'Percentage of {test}')
    # naming the y axis
    plt.ylabel('Time in seconds')

    plt.savefig(f'{test}')
    plt.close()



def main():
    for test, data in make_dict(read_results()).items():
        plot(test, data)


if __name__ == '__main__':
    main()
