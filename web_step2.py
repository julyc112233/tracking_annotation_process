from pywebio.input import actions, input_group
from pywebio.output import clear, put_html, put_row
from pywebio.platform.tornado import start_server
import pandas as pd
import re
from collections import defaultdict
import typing
from dataclasses import dataclass
import uuid

token="sp=r&st=2021-12-30T07:26:27Z&se=2022-02-01T15:26:27Z&sv=2020-08-04&sr=c&sig=D78d1irOmMA3sEKRL%2FGaH88%2FwppCQlP0DNu2dndYzM0%3D"
@dataclass
class Row:
    id: str
    video: str
    duration:float
    thumbnail: str
    camera_id:int

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
    infos=url.split('?')
    res=infos[0]+"?"+token
    return res
def get_urls_from_str(content):
    Rowstrings = get_raw_string(content)
    res = []
    for row_string in Rowstrings:
        row_now = Row.from_str(row_string)
        res.append(trans_url(row_now.video))
    return res


def display(index1, index2, df):
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

    info = input_group(
        "Check video",
        [
            actions(
                "",
                [
                    {"label": "Yes", "value": 1},
                    {"label": "No", "value": 0, "color": "danger"},
                    {"label": "save", "value": -1},
                ],
                name="check",
            ),
        ],
    )
    return info



def update_file(df,book, path="step2.csv"):
    for index,row in df.iterrows():
        df.loc[index,"corrected_shopper_id"]=book[row["corrected_shopper_id"]]
    df.to_csv(path)

def get_unchecked_id(id_to_index, df):
    targ_id = None
    for key, value in id_to_index.items():
        status = df.loc[value[0], "checked"]
        if status == "NO":
            targ_id = key
            break
    # df_tmp=df[df["corrected_shopper_id"]==targ_id]
    # for index,row in df_tmp:
    #     df.loc[index,"checked"]="PENDING"
    return targ_id

def get_valid_pair(infos):
    res=[]
    for info in infos:
        strs=info.split(",")
        id1=strs[0][1:]
        id2=strs[1][1:-1]
        res.append((id1,id2))
    return res

def find(id,book):
    if book[id]==id:
        return id
    else:
        x=find(book[id],book)
        book[id]=x
        return x
def unite(id1,id2,book):
    id1=find(id1,book)
    id2=find(id2,book)
    book[id1]=id2
    return

def main(data_path,pair_path):
    df = pd.read_csv(data_path)
    df_pair=pd.read_csv(pair_path)
    valid_pair=get_valid_pair(df_pair["0"].tolist())
    id_to_index = defaultdict(list)
    book={}
    for index, row in df.iterrows():
        id = str(row["corrected_shopper_id"])
        id_to_index[id].append(index)
        book[id]=id
    for x,y in valid_pair:
        index1=id_to_index[x][0]
        index2=id_to_index[y][0]
        info=display(index1,index2,df)
        if info["check"]==1:
            unite(x,y)
        if info["check"]==-1:
            update_file(df,book)
        clear()
    update_file(df,book)


if __name__ == "__main__":
    path = "~/Downloads/merged_new_hat_table.csv"
    pair_path="~/Downloads/se.csv"
    main(path,pair_path)
    # start_server(main)
