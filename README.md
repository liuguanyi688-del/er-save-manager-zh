# er-save-manager 简体中文补丁

给 [er-save-manager](https://github.com/Hapfel1/er-save-manager) 加简体中文界面的补丁脚本。

> **本仓库不包含原程序的任何二进制或源码。** 请自行到
> [GitHub Releases](https://github.com/Hapfel1/er-save-manager/releases) 或
> [Nexus Mods](https://www.nexusmods.com/eldenring/mods/9271) 下载原版，
> 然后用本脚本给自己的副本打补丁。

## 为什么是"补丁"而不是"汉化版"

原项目使用 **Source-Available License**，其中明确规定：

- 允许：查看源码、自行构建、**修改后个人使用**、fork 后向上游提交 PR
- 禁止：**在授权分发点之外再分发**（原始或修改形式、源码或编译产物）、用 fork 独立发布构建

所以直接分发改好的程序是违规的。本仓库只提供脚本，脚本在你的机器上作用于你自己的副本，
不构成再分发。

## 原理

程序用 cx_Freeze 冻结打包，业务模块以 `.pyc` 字节码形式存放在：

```
er-save-manager_<版本>/lib/er_save_manager/**/*.pyc
```

这些字节码的 magic number 与 Python 3.13 一致（`f30d0d0a`），因此可以直接
`marshal.loads()` 反序列化成 code object，替换 `co_consts` 里的界面字符串，
再 `marshal.dumps()` 写回，并保留原 16 字节文件头。

**只改字符串常量，不改任何一行逻辑。**

## 用法

1. 关闭 er-save-manager
2. 双击 `apply.bat`，把 `er-save-manager_<版本>` 文件夹拖进去，回车
3. 启动程序，界面即为中文

命令行方式：

```bash
python apply.py --app "C:\path\to\er-save-manager_2.4.2"
python apply.py --app "..." --dry-run    # 只统计，不写入
python apply.py --app "..." --revert     # 还原英文
```

原始字节码会备份到 `er-save-manager_<版本>/lib/_zh_original_pyc/`，随时可还原。

## 安全规则

并非所有英文都能替换。有些字符串是**内部查找键** —— 界面上显示 `Vigor`，
代码里也用 `"Vigor"` 去字典取属性值，把键翻译掉就会取不到数据，甚至写坏存档。

脚本的判断依据：

> 只要某个词同时出现在 `parser/`、`data/`、`transfer/`、`validation/`
> 这些数据层目录里，就判定它可能是键，跳过不译。

被这条规则拦下的词包括 `Vigor`、`Inventory`、`Talismans`、`Armor`、`Gestures`
—— 它们保持英文是**故意的**，不是漏翻。

同理，拼接片段（`' is not '`、`' save file.'`）和长句也全部跳过：
中英语序不同，硬替换会拼出病句。

## 覆盖范围

| 已汉化 | 未汉化 |
|---|---|
| 主窗口标题、副标题 | 运行时拼接的长句提示 |
| 10 个标签页名称 | 部分弹窗正文 |
| 按钮、字段名、表头 | 游戏名 `Elden Ring`（内部键名） |
| 菜单项、状态提示标题 | `Gestures`（出现在 parser，疑似键） |

约 640 条词条，覆盖 96 个模块、1300+ 处字符串。

## 属性英文对照

| 英文 | 中文 | 说明 |
|---|---|---|
| Vigor | 生命值 | 血条长度，最优先 |
| Mind | 集中力 | 蓝条 |
| Endurance | 耐力 | 绿条 + 负重 |
| Strength | 力气 | 重型武器主属性 |
| Dexterity | 灵巧 | 轻型武器主属性 |
| Intelligence | 智力 | 法术 |
| Faith | 信仰 | 祷告 |
| Arcane | 感应 | 出血/中毒/发现力 |
| Runes | 卢恩 | 经验值兼货币 |
| Level | 等级 | |
| Poise | 韧性 | 抗打断 |
| Equip Load | 负重 | |
| Great Rune | 大卢恩 | |
| Rune Arc | 卢恩圆弧 | 激活大卢恩的道具 |
| Site of Grace | 赐福点 | 存档点兼传送点 |
| Spirit Ash | 骨灰 | 召唤物 |
| Ash of War | 战灰 | 武器战技 |
| Smithing Stone | 锻造石 | 普通武器强化 |
| Somber Smithing Stone | 失色锻造石 | 特殊武器强化 |
| Scadutree Blessing | 幽影树祝福 | DLC 独立强化 |
| Revered Spirit Ash | 崇敬骨灰 | DLC 骨灰强化 |

## 风险提示

- 改过的存档**不要上线**。EAC 不加载不等于服务器不校验存档，
  会触发 `INVALID GAME DATA DETECTED` 被送进隔离服务器（约 180 天）。
- 只改数值（属性 / 卢恩 / 物品 / 强化），**不要碰事件标志和世界状态**，
  会破坏 NPC 任务线。
- 打补丁前先备份存档。

## 许可

`apply.py`、`zh_dict.py` 为本仓库作者原创，MIT。
原程序版权归 [Hapfel1](https://github.com/Hapfel1) 所有，本项目与其无隶属关系。

如果你觉得这个工具有用，请去原仓库点个 star，或通过程序里的「支持作者」按钮赞助原作者。
