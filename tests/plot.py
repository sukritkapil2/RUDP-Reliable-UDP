import json
from pathlib import Path
import plotly.graph_objects as go
from collections import defaultdict
import chart_studio.plotly as py
from statistics import median


FILE_SIZE = "46,90,895"  # bytes


def read_results() -> dict:
    results = []
    for file in Path("results/data").iterdir():
        if file.name.startswith("run_") and file.suffix == ".json":
            results.append(json.loads(file.read_text()))
    return results


def merge_results(results: dict) -> dict:
    res = defaultdict(lambda: defaultdict(list))
    for run_result in results:
        for factor, data in run_result.items():
            for percent, time in data.items():
                res[factor][percent].append(time)

    return res


def plot(factor, data):
    fig = go.Figure()
    medians = {}
    for percent, values in data.items():
        medians[percent] = median(values)
        fig.add_trace(go.Box(y=values, name=percent))

    # add median line graph
    fig.add_trace(
        go.Scatter(
            x=tuple(medians.keys()),
            y=tuple(medians.values()),
            name="median_time",
            mode="lines+markers",
        )
    )

    fig.update_layout(
        yaxis_title="time (in seconds)",
        xaxis_title=factor + " (ms)" if factor in ("delay", "jitter") else "",
        title=go.layout.Title(text=f"YARU performance with varying {factor}"),
        annotations=[
            go.layout.Annotation(
                text=f"Transfer time for file of size {FILE_SIZE} bytes",
                showarrow=False,
                x=0.5,
                y=1,
                xref="paper",
                yref="paper",
            )
        ],
    )

    # for online, interactive chart
    print(py.plot(fig, filename=f"yaru_{factor}", auto_open=False))

    # for offline png
    fig.write_image(filename=f"results/yaru_{factor}.png")


def main():
    for factor, data in merge_results(read_results()).items():
        plot(factor, data)


if __name__ == '__main__':
    main()
