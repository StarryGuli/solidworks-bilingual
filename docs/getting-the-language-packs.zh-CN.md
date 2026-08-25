# 获取两个语言包

本工具合并的是**你电脑上已有的**两个语言包。工具本身不附带语言包，本仓库也不提供：
语言包是 Dassault Systèmes 的软件，受你的 SOLIDWORKS 授权覆盖，不得再分发。

仓库里有一份合成的示例语言包放在 [`samples/`](../samples)，可以直接拿来试跑，
见下方[没有 SOLIDWORKS 也能试](#没有-solidworks-也能试)。

## 语言包在哪里

两个都在 SOLIDWORKS 安装目录的 `lang` 文件夹下：

```
C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\english
C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\chinese-simplified
```

盘符和路径可能不同——装在 `E:` 盘很常见。`locate` 会从注册表读取真实安装路径，
不会假定在 `C:` 盘。

列出本机已有的语言包及其构建号：

```
python swbilingual-cli.py locate
```

英文包一定存在。中文包只有在安装时勾选过中文才有，所以多数机器上需要另外添加。

## 添加中文包

用 SOLIDWORKS 安装管理程序（Installation Manager）。**优先走这条路**，
因为它会自动下载与你当前构建号匹配的语言包——而这正是本工具的硬性要求。

1. 打开 Windows **设置 → 应用 → 已安装的应用**，找到 SOLIDWORKS 条目，
   点右侧菜单选**修改（Modify）**。
2. 选择**修改您的单机安装**，然后连续点**下一步**，直到**产品选择**页面。
3. 展开 **SOLIDWORKS Languages**，勾选**简体中文（Chinese Simplified）**。
4. 会弹出提示说需要下载该语言包的安装文件，这是正常的，确认继续。
5. 确认「要添加的产品」里列出了该语言包，勾选左下角的许可协议，
   点**下载并修改（Download and Modify）**。
6. 完成后 `lang\` 下就会出现对应文件夹。

全程无需重装，也不会影响现有设置。

> **哪个文件夹才是简体？** SOLIDWORKS 把「中文」和「简体中文」作为两个独立语言提供，
> 所以 `lang` 下可能同时存在 `chinese` 和 `chinese-simplified` 两个文件夹——
> 而且不同机器的对应关系并不一致：名为 `chinese` 的文件夹，
> 在有些机器上是繁体，在另一些机器上是简体，还可能是空的。
>
> **不要靠名字判断。** `check` 会直接读取包内容并告诉你里面到底是什么：
>
> ```
> 简繁体：简体
> ```
>
> 如果你选了一个空的或不存在的文件夹，报错会列出它旁边确实含有语言包的文件夹，
> 并标明每个是简体还是繁体。

## 如果安装管理程序下载不了

安装程序需要连上 Dassault Systèmes 的下载服务器，且所用账号要有下载权限。
连不上或没权限时，可以手动下载安装介质：

- **[SOLIDWORKS 下载页](https://www.solidworks.com/support/downloads)** ——
  官方入口，从这里开始。
- 用 **3DEXPERIENCE ID** 登录。原来的 SOLIDWORKS Customer Portal
  （`customerportal.solidworks.com`）已于 **2024 年 10 月退役**，
  下载和许可管理都迁到了 Dassault Systèmes 的系统。
  在 `my.solidworks.com` 上用 SOLIDWORKS 账号登录**不是同一回事**，拿不到下载权限。
- 下载需要有效的订阅服务，或处于订阅覆盖下的序列号。两者都没有的话，
  正确途径是找你的代理商（VAR），他们能提供你所授权版本对应的安装介质。
- 一定要选**与你安装版本相同的版本和 Service Pack**。
  下成更新的 SP，拿到的中文包合并不了——工具会直接拒绝，但下载的流量就白费了。

学生和教育版用户请找所在院校的 SOLIDWORKS 管理员要安装介质，不要走公开下载页。

## 确认两个包匹配

```
python swbilingual-cli.py check "C:\...\lang\english" "C:\...\lang\chinese"
```

两个构建号必须完全一致，它们读自 `sldresu.dll` 的文件版本。
如果不一致，说明两个包来自不同构建：它们的资源 ID 指向的是不同的字符串，
强行合并会把中文标签贴到毫不相干的命令上。
请去补装匹配的中文包，不要尝试跨构建合并。

## 没有 SOLIDWORKS 也能试

仓库里带了一小对生成出来的语言包，任何人都能直接跑：

```
python swbilingual-cli.py --lang zh check   samples/english samples/chinese
python swbilingual-cli.py --lang zh preview samples/english samples/chinese
```

里面是为本项目编写的、某个虚构建模软件的标签，**没有任何内容来自 SOLIDWORKS**。
它们带有版本资源，字符串表格式与真实语言包一致，足以跑通 `check` 和 `preview`；
完整构建仍然需要真实语言包和 Windows。

重新生成：

```
python tools/make_sample_pack.py samples
```

示例里**故意放了几条规则必须拒绝的条目**——格式化字符串、文件过滤器、URL、
长句、以及中英相同的未翻译项——这样预览能同时展示「什么会被合并」和「什么保持原样」。
