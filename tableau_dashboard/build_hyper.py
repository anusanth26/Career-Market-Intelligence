"""Converts every CSV in extracts/ to a Tableau extract (.hyper) in extracts/hyper/. Tableau Public only saves
workbooks whose data sources are extracts. Needs `pip install tableauhyperapi pandas`.

    python tableau_dashboard/build_hyper.py
"""
import datetime
import os

import pandas as pd
from tableauhyperapi import Connection, CreateMode, HyperProcess, Inserter, SqlType, TableDefinition, TableName, Telemetry

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(HERE, "extracts")
OUT = os.path.join(EXT, "hyper")
os.makedirs(OUT, exist_ok=True)


def sql_type(col, dtype):
    if col.endswith("_date") or col == "date":
        return SqlType.date()
    return SqlType.big_int() if str(dtype).startswith("int") else SqlType.double() if str(dtype).startswith("float") \
        else SqlType.bool() if dtype == bool else SqlType.text()


def cell(v, t):
    if pd.isna(v):
        return None
    if t == SqlType.date():
        d = pd.Timestamp(v)
        return datetime.date(d.year, d.month, d.day)
    if t == SqlType.big_int():
        return int(v)
    if t == SqlType.double():
        return float(v)
    return bool(v) if t == SqlType.bool() else str(v)


with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
    for name in sorted(f for f in os.listdir(EXT) if f.endswith(".csv")):
        df = pd.read_csv(os.path.join(EXT, name))
        types = {c: sql_type(c, df[c].dtype) for c in df.columns}
        table = TableDefinition(TableName("Extract", "Extract"), [TableDefinition.Column(c, types[c]) for c in df.columns])
        path = os.path.join(OUT, name.replace(".csv", ".hyper"))
        with Connection(hyper.endpoint, path, CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema("Extract")
            conn.catalog.create_table(table)
            with Inserter(conn, table) as ins:
                ins.add_rows([[cell(v, types[c]) for c, v in zip(df.columns, row)] for row in df.itertuples(index=False, name=None)])
                ins.execute()
        print(f"{name}: {len(df)} rows -> {os.path.relpath(path, HERE)}")
