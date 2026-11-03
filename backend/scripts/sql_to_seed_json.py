# -*- coding: utf-8 -*-
"""从 Navicat MySQL dump 提取 INSERT 为方言无关的 JSON 种子。

用法（在 backend 目录）:
  python scripts/sql_to_seed_json.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SQL_FILE = BACKEND / "sql" / "db_init.sql"
OUT_DIR = BACKEND / "sql" / "seed"

# 启动所需的核心系统表（按依赖顺序在 initialize 中控制）
SEED_TABLES = [
    "sys_menu",
    "sys_role",
    "sys_dict_type",
    "sys_dict_data",
    "sys_user",
    "sys_user_role",
    "sys_role_menu",
]


def parse_create_columns(sql: str, table: str) -> list[str]:
    pattern = rf"CREATE TABLE `{re.escape(table)}`\s*\((.*?)\)\s*ENGINE"
    m = re.search(pattern, sql, re.DOTALL | re.IGNORECASE)
    if not m:
        raise RuntimeError(f"找不到 CREATE TABLE `{table}`")
    body = m.group(1)
    cols: list[str] = []
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if not line.startswith("`"):
            continue
        col = line.split("`")[1]
        cols.append(col)
    return cols


def parse_sql_values(values_sql: str) -> list:
    """解析 INSERT VALUES (...) 中的一行元组。"""
    values_sql = values_sql.strip()
    if values_sql.endswith(";"):
        values_sql = values_sql[:-1]
    # 去掉外层括号
    if values_sql.startswith("(") and values_sql.endswith(")"):
        values_sql = values_sql[1:-1]

    items: list = []
    i = 0
    n = len(values_sql)
    while i < n:
        while i < n and values_sql[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        if values_sql.startswith("NULL", i) and (i + 4 >= n or values_sql[i + 4] in ", \t\r\n"):
            items.append(None)
            i += 4
            continue
        if values_sql[i] in ("'", '"'):
            quote = values_sql[i]
            i += 1
            buf: list[str] = []
            while i < n:
                ch = values_sql[i]
                if ch == "\\" and i + 1 < n:
                    buf.append(values_sql[i + 1])
                    i += 2
                    continue
                if ch == quote:
                    # MySQL 转义 '' 
                    if i + 1 < n and values_sql[i + 1] == quote:
                        buf.append(quote)
                        i += 2
                        continue
                    i += 1
                    break
                buf.append(ch)
                i += 1
            items.append("".join(buf))
            continue
        # 数字 / 裸标识
        j = i
        while j < n and values_sql[j] not in ",":
            j += 1
        token = values_sql[i:j].strip()
        if re.fullmatch(r"-?\d+", token):
            items.append(int(token))
        elif re.fullmatch(r"-?\d+\.\d+", token):
            items.append(float(token))
        else:
            items.append(token)
        i = j
    return items


def extract_inserts(sql: str, table: str) -> list[str]:
    pattern = rf"INSERT INTO `{re.escape(table)}`\s+VALUES\s*(\(.*?\));"
    return re.findall(pattern, sql, re.DOTALL | re.IGNORECASE)


def coerce_json_field(col: str, value):
    if value is None:
        return None
    if col in {"tags"} and isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    # dump 偶发把 datetime 错位到 oauth_provider
    if col == "oauth_provider" and isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}", value):
        return None
    return value


def main() -> None:
    sql = SQL_FILE.read_text(encoding="utf-8")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for table in SEED_TABLES:
        cols = parse_create_columns(sql, table)
        rows_sql = extract_inserts(sql, table)
        records = []
        for row_sql in rows_sql:
            values = parse_sql_values(row_sql)
            if len(values) != len(cols):
                # 容错：截断或跳过
                if abs(len(values) - len(cols)) > 2:
                    print(f"[WARN] {table}: 列数不匹配 cols={len(cols)} values={len(values)}, 跳过一行")
                    continue
                # 补齐/截断
                if len(values) < len(cols):
                    values = values + [None] * (len(cols) - len(values))
                else:
                    values = values[: len(cols)]
            record = {c: coerce_json_field(c, v) for c, v in zip(cols, values)}
            records.append(record)

        # dump 偶发重复主键：按出现顺序重分配唯一 id（关联表不含 id 列则跳过）
        if records and "id" in records[0]:
            seen_ids: set = set()
            has_dup = False
            for r in records:
                rid = r.get("id")
                if rid in seen_ids:
                    has_dup = True
                    break
                if rid is not None:
                    seen_ids.add(rid)
            if has_dup:
                for i, r in enumerate(records, start=1):
                    r["id"] = i
                print(f"[FIX] {table}: 检测到重复 id，已重分配为 1..{len(records)}")

        out = OUT_DIR / f"{table}.json"
        out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] {table}: {len(records)} rows -> {out.relative_to(BACKEND)}")


if __name__ == "__main__":
    main()
