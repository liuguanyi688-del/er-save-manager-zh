#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""er-save-manager 简体中文补丁

在不修改原程序逻辑的前提下，把界面字符串替换为中文。
原理：程序的模块以 .pyc 字节码形式存放在 lib/er_save_manager/ 下，
     本脚本用 marshal 反序列化 code object，替换 co_consts 中的
     界面字符串常量后重新序列化写回。

用法:
    python apply.py --app "C:\\path\\to\\er-save-manager_2.4.2"
    python apply.py --app "..." --dry-run      # 只统计，不写入
    python apply.py --app "..." --revert       # 还原英文

注意: 运行前请关闭 er-save-manager。
"""

import argparse
import marshal
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from zh_dict import ZH  # noqa: E402

# 数据/逻辑层：这些目录里的字符串可能是查找键，绝不翻译
DENY = ("parser/", "data/", "transfer/", "validation/",
        "platform/", "addons/", "fixes/", "backup/")

BACKUP_DIRNAME = "_zh_original_pyc"


def find_package(app: Path) -> Path:
    """在给定目录里定位 er_save_manager 包。"""
    candidates = [
        app / "lib" / "er_save_manager",
        app / "er_save_manager",
        app,
    ]
    for c in candidates:
        if (c / "ui").is_dir() and (c / "parser").is_dir():
            return c
    raise SystemExit(
        f"[错误] 在 {app} 下找不到 er_save_manager 包。\n"
        f"       请把 --app 指向解压后的 er-save-manager_<版本> 目录。"
    )


def walk(co, acc):
    acc.append(co)
    for c in co.co_consts:
        if hasattr(c, "co_code"):
            walk(c, acc)


def load_all(pkg: Path):
    out = {}
    for pyc in sorted(pkg.rglob("*.pyc")):
        try:
            data = pyc.read_bytes()
            co = marshal.loads(data[16:])
        except Exception as e:
            print(f"[跳过] 无法解析 {pyc.name}: {e}")
            continue
        out[str(pyc.relative_to(pkg)).replace("\\", "/")] = (pyc, data[:16], co)
    return out


def index_strings(codes):
    where = defaultdict(set)
    for rel, (_, _, co) in codes.items():
        acc = []
        walk(co, acc)
        for c in acc:
            for k in c.co_consts:
                if isinstance(k, str):
                    where[k].add(rel)
    return where


def cmd_revert(pkg: Path) -> None:
    bak = pkg.parent / BACKUP_DIRNAME
    if not bak.exists():
        raise SystemExit(f"[错误] 找不到备份目录 {bak}，无法还原。")
    n = 0
    for f in bak.rglob("*.pyc"):
        dst = pkg / f.relative_to(bak)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        n += 1
    print(f"[完成] 已还原 {n} 个模块，界面回到英文。")


def cmd_apply(pkg: Path, dry: bool) -> None:
    codes = load_all(pkg)
    if not codes:
        raise SystemExit("[错误] 没有找到任何 .pyc 模块。")
    where = index_strings(codes)

    safe_map, skipped = {}, []
    for k, v in ZH.items():
        mods = where.get(k, set())
        if any(m.startswith(DENY) for m in mods):
            skipped.append(k)
        elif mods:
            safe_map[k] = v

    print(f"模块 {len(codes)} 个 | 词典 {len(ZH)} 条 | 可安全替换 {len(safe_map)} 条")
    if skipped:
        print(f"因涉及数据层而跳过 {len(skipped)} 条（这些可能是查找键）")

    if dry:
        print("\n[预演] 未写入。去掉 --dry-run 实际执行。")
        return

    bak_root = pkg.parent / BACKUP_DIRNAME
    files, hits = 0, 0

    for rel, (pyc, header, co) in codes.items():
        count = [0]

        def rebuild(c):
            changed = False
            consts = []
            for k in c.co_consts:
                if isinstance(k, str) and k in safe_map:
                    consts.append(safe_map[k])
                    count[0] += 1
                    changed = True
                elif hasattr(k, "co_code"):
                    nk = rebuild(k)
                    if nk is not k:      # 子函数有改动，父级必须一并重建
                        changed = True
                    consts.append(nk)
                else:
                    consts.append(k)
            return c.replace(co_consts=tuple(consts)) if changed else c

        new_co = rebuild(co)
        if count[0] == 0:
            continue

        bak = bak_root / rel
        bak.parent.mkdir(parents=True, exist_ok=True)
        if not bak.exists():            # 只保留最初的原件
            shutil.copy2(pyc, bak)

        pyc.write_bytes(header + marshal.dumps(new_co))
        files += 1
        hits += count[0]

    print(f"[完成] 改写 {files} 个模块，替换 {hits} 处字符串")
    print(f"[备份] 原始字节码保存在 {bak_root}")
    print("       如需还原，运行: python apply.py --app ... --revert")


def main() -> None:
    ap = argparse.ArgumentParser(description="er-save-manager 简体中文补丁")
    ap.add_argument("--app", required=True,
                    help="解压后的 er-save-manager 目录，例如 ...\\er-save-manager_2.4.2")
    ap.add_argument("--dry-run", action="store_true", help="只统计不写入")
    ap.add_argument("--revert", action="store_true", help="还原为英文原版")
    args = ap.parse_args()

    # 拖拽进来的路径可能带引号，先去掉
    app = Path(args.app.strip().strip('"').strip("'")).expanduser().resolve()
    if not app.is_dir():
        raise SystemExit(f"[错误] 目录不存在: {app}")
    pkg = find_package(app)
    print(f"目标包: {pkg}\n")

    if args.revert:
        cmd_revert(pkg)
    else:
        cmd_apply(pkg, args.dry_run)


if __name__ == "__main__":
    main()
