# 命令行参考

```
python swbilingual-cli.py [-q] [-l {en,zh}] <命令> ...
```

`--lang zh` 让所有信息以中文输出。不指定时，依次取环境变量 `SWBILINGUAL_LANG`
和系统区域设置。

`--quiet` 不显示进度条，日志照常打印。

成功退出码为 `0`，命令报告问题时为 `1`，便于写进脚本。

---

## check

```
python swbilingual-cli.py check <英文包> <中文包>
```

比对两个语言包而不写入任何文件：DLL 数量、从 `sldresu.dll` 读取的构建号、
两侧同名文件数量，以及 XAML 字典是否齐全。不能合并时退出码为 `1`。

可在任意操作系统上运行。

## preview

```
python swbilingual-cli.py preview <英文包> <中文包> [-n 25] [-t 关键词] [-f 文件名]
```

预览合并结果。直接从文件中读取字符串表，不写入任何内容，也不需要 Windows。

| 选项 | 含义 |
|---|---|
| `-n`, `--limit` | 打印多少条示例，默认 25 |
| `-t`, `--term` | 只显示英文原文含该词的条目 |
| `-f`, `--file` | 只预览指定的一个 DLL，例如 `sldresu.dll` |

首行会给出共检查了多少对字符串、其中多少条会变成双语。

## build

```
python swbilingual-cli.py build <英文包> <中文包> <输出文件夹>
```

先把英文包复制到输出文件夹，再对副本执行三步合并。来源文件夹只读不写。
除非指定 `--no-verify`，构建后会自动执行校验。

| 选项 | 含义 |
|---|---|
| `--no-copy` | 输出文件夹中已有一份英文包副本 |
| `--no-verify` | 构建后不执行检查 |

需要 Windows。

## verify

```
python swbilingual-cli.py verify <英文包> <输出文件夹>
```

对已生成的语言包执行三项检查：资源清单、对话框布局、逐个加载 DLL。需要 Windows。

## install

```
python swbilingual-cli.py install <来源> <目标> [-y]
```

先把 `<目标>` 的当前内容复制为 `<目标>.backup-YYYYmmdd-HHMMSS`，
再把生成的语言包覆盖到 `<目标>`。未加 `-y` 时会先询问。

请先关闭 SOLIDWORKS，并在管理员命令提示符下运行。

## restore

```
python swbilingual-cli.py restore <备份> <目标>
```

把备份复制回语言文件夹。

## locate

```
python swbilingual-cli.py locate
```

列出常见安装位置下找到的 SOLIDWORKS 语言文件夹及其构建号。

---

## 完整流程示例

```
python swbilingual-cli.py --lang zh locate
python swbilingual-cli.py --lang zh check   "C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\english" ^
                                            "C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\chinese"
python swbilingual-cli.py --lang zh preview "C:\...\lang\english" "C:\...\lang\chinese" -t Fillet
python swbilingual-cli.py --lang zh build   "C:\...\lang\english" "C:\...\lang\chinese" D:\bilingual
python swbilingual-cli.py --lang zh install D:\bilingual "C:\...\lang\english"
```
