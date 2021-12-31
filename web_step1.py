from pywebio.input import actions, input_group
from pywebio.output import clear, put_html, put_row, put_text
from pywebio.platform.tornado import start_server
import pandas as pd
import re
from collections import defaultdict
import typing
from dataclasses import dataclass
import uuid
import logging
import time
import os


token = "sp=r&st=2021-12-30T07:26:27Z&se=2022-02-01T15:26:27Z&sv=2020-08-04&sr=c&sig=D78d1irOmMA3sEKRL%2FGaH88%2FwppCQlP0DNu2dndYzM0%3D"


@dataclass
class Row:
    id: str
    video: str
    duration: float
    thumbnail: str
    camera_id: int

    @classmethod
    def from_str(cls, str):
        if len(str) <= 5:
            return None
        content = str[4:-1]
        if len(content) == 0:
            return None
        info = content.split(", ")
        if len(info) < 6:
            return None
        return cls(
            id=info[0][4:-1],
            video=info[1][5:-1],
            duration=float(info[2][9:]),
            thumbnail=info[3][11:-1],
            camera_id=int(info[4][10:]),
        )


def get_raw_string(encode: str):
    starts = []
    targ = "Row"
    for a in re.finditer(targ, encode):
        starts.append(a.span())
    res = []
    starts_len = len(starts)
    for i in range(len(starts)):
        if i == starts_len - 1:
            res.append(encode[starts[i][0] : -1])
        else:
            res.append(encode[starts[i][0] : starts[i + 1][0] - 2])
    return res


def trans_url(url):
    infos = url.split("?")
    res = infos[0] + "?" + token
    return res


def get_urls_from_str(content):
    Rowstrings = get_raw_string(content)
    res = []
    for row_string in Rowstrings:
        row_now = Row.from_str(row_string)
        res.append(trans_url(row_now.video))
    return res


def display(index1, index2, df, text="Unchecked!"):
    urls_first = get_urls_from_str(df.loc[index1, "videos"])
    urls_second = get_urls_from_str(df.loc[index2, "videos"])
    put_row(
        [
            put_html(
                '<video width="100%" controls="controls" src="{url}"></video>'.format(
                    url=url
                )
            )
            for index, url in enumerate(urls_first)
            if index < 3
        ],
        size="50% 10px 50%",
    )
    put_row(
        [
            put_html(
                '<video width="100%" controls="controls" src="{url}"></video>'.format(
                    url=url
                )
            )
            for index, url in enumerate(urls_second)
            if index < 3
        ],
        size="50% 10px 50%",
    )
    put_text(text)
    info = input_group(
        "Check video",
        [
            actions(
                "",
                [
                    {"label": "Next", "value": 2},
                    {"label": "Yes", "value": 1},
                    {"label": "No", "value": 0, "color": "danger"},
                    {"label": "save", "value": -1},
                ],
                name="check",
            ),
        ],
    )

    return info


def get_unannotate_hat_case(path=".csv"):
    df = pd.read_excel(path)
    for index, row in df.iterrows():
        if row["checked"] == "NO":
            return index
    return None


def update_file(df, path="step1.csv"):
    print("write to ", path)
    df.to_csv(path)


def get_unchecked_id(id_to_index, df):
    targ_id = None
    for key, value in id_to_index.items():
        status = df.loc[value[0], "checked"]
        if status == "NO":
            targ_id = key
            return targ_id
    return targ_id


def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    rq = time.strftime("%Y%m%d%H%M", time.localtime(time.time()))
    log_path = os.path.dirname(os.getcwd()) + "/Logs/"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log_name = os.path.join(log_path + rq + "log_step1.log")
    logfile = log_name
    fh = logging.FileHandler(logfile, mode="w")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def main(path):
    logger = get_logger()
    df = pd.read_csv(path)
    if not "checked" in df.columns.values:
        df["checked"] = "NO"

    id_to_index = defaultdict(list)
    for index, row in df.iterrows():
        id = row["corrected_shopper_id"]
        id_to_index[id].append(index)

    while True:
        targ_id = get_unchecked_id(id_to_index, df)
        if targ_id is None:
            break
        index_list = id_to_index[targ_id]
        index_tmp = index_list[0]
        for i, index in enumerate(index_list):
            if i == 0:
                df.loc[index, "checked"] = "YES"
                continue
            if df.loc[index, "checked"] == "YES":
                continue
            Flag = None
            while True:
                if Flag == None:
                    text = "Unchecked!"
                elif Flag == False:
                    text = "Not Same person!"
                else:
                    text = "Same person!"
                info = display(index, index_tmp, df, text)
                logger.info(
                    "index1:"
                    + str(index)
                    + " index2:"
                    + str(index_tmp)
                    + " info:"
                    + str(info)
                )
                # print(index,index_tmp,info)
                clear()
                if info["check"] == 0:
                    Flag = False
                if info["check"] == -1:
                    if Flag == False:
                        df.loc[index, "corrected_shopper_id"] = uuid.uuid1()
                    update_file(df)
                if info["check"] == 1:
                    Flag = True
                if info["check"] == 2:
                    if Flag == False:
                        df.loc[index, "corrected_shopper_id"] = uuid.uuid1()
                    break
        update_file(df)


if __name__ == "__main__":
    path = "~/Downloads/merged_new_hat_table.csv"
    main(path)
    # start_server(main)
