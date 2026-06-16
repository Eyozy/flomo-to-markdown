# flomo-to-markdown

将 [flomo](https://flomoapp.com/) 导出的 HTML 笔记一键转换为结构清晰的 Markdown 文件，帮你轻松实现笔记的本地归档、二次编辑或无缝迁移至其他平台。

在线使用：[flomo to Markdown](https://flomo-to-markdown.vercel.app/)

## 功能特性

- 自动解析 HTML，提取笔记内容、标签和链接
- 自动查找并复制图片，更新 Markdown 中的图片路径
- 图片以日期时间戳重命名，避免同名覆盖
- 笔记按时间倒序排列，最新内容置顶
- 三种导出模式：单一合并文件 / 单条 Memo 文件 / 按年归档
- 终端交互菜单，自动扫描 flomo 目录，零命令记忆
- Web 界面，浏览器上传即用，支持年份筛选和多种导出模式

## 快速开始

### 环境准备

确保你的电脑已安装 **Python 3.6** 或更高版本。在终端或命令行中运行以下命令进行检查：

```bash
python --version
# 或者在某些系统上使用
python3 --version
```

> **提示**：Windows 用户在安装 Python 时，请务必勾选 `Add Python to PATH` 选项。

### 安装

```bash
git clone https://github.com/Eyozy/flomo-to-markdown.git
cd flomo-to-markdown
```

CLI 版本：

```bash
pip install -r requirements-cli.txt
```

Web 版本：

```bash
pip install -r requirements.txt
```

### 使用

#### CLI

在运行脚本前，请按照以下结构准备你的 flomo 导出文件：

```
flomo-to-markdown/
├── flomo/              <- flomo 笔记文件夹（默认源目录）
│   ├── 笔记.html       <- 导出的 HTML（文件名无需固定）
│   └── file/           <- 图片文件夹（可选）
└── flomo_converter.py
```

运行：

```bash
python flomo_converter.py
```

进入交互式菜单，依次选择年份、导出模式，确认后自动转换输出到 `converted_notes` 目录。

#### Web

```bash
python app.py
```

打开浏览器访问 `http://127.0.0.1:5001`，上传 HTML 或 ZIP 文件，在线转换下载。

Web 界面支持功能：

- 上传 `.html` / `.htm` 文件，或包含 HTML 文件及图片文件夹的 `.zip` 压缩包
- 自动解析笔记中的年份，支持筛选特定年份
- 支持多种导出模式（单一合并文件、单条 Memo 文件、按年归档）
- 根据转换结果自动提供 `.md` 文件或 `.zip` 压缩包下载

## 常见问题

**HTML 文件名不固定能用吗？**

可以。脚本会自动在源目录下查找所有 `.html` / `.htm` 文件进行处理，无需修改文件名。

**有多个 HTML 文件怎么办？**

脚本会读取所有 HTML 文件，提取笔记后统一排序合并（单一文件模式下）。

**笔记里没图片会报错吗？**

不会。图片处理模块会自动跳过，不影响正常转换。

**`flomo-images` 文件夹为什么是空的？**

说明脚本未找到图片，请检查：
1. 笔记中确实包含图片
2. 从 flomo 导出的 `file` 文件夹已放在源目录下
3. 脚本运行过程中未出现「图片文件未找到」警告

**运行报错怎么办？**

请检查：
1. 是否已按照安装章节正确安装所有依赖
2. 文件目录结构是否与文档描述一致

如果问题仍然存在，请通过 [GitHub Issues](https://github.com/Eyozy/flomo-to-markdown/issues) 提交，附上错误信息、操作系统和 Python 版本。

## 贡献

我们非常欢迎任何形式的贡献，无论是报告问题、提出建议还是贡献代码！

### 报告问题

- 请在 [GitHub Issues](https://github.com/Eyozy/flomo-to-markdown/issues) 页面提交 Bug 报告或功能建议
- 提供详细的问题描述、复现步骤及预期结果
- 请务必包含你的操作系统和 Python 版本信息，以便更好地定位问题

### 贡献代码

1. Fork 本项目到你自己的 GitHub 仓库
2. 创建你的特性分支 (`git checkout -b feature/YourAmazingFeature`)
3. 提交你的更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 将分支推送到你的 Forked 仓库 (`git push origin feature/YourAmazingFeature`)
5. 在本项目仓库中开启一个 Pull Request，详细描述你的更改和解决的问题

### 开发环境设置

```bash
# 克隆项目到本地
git clone https://github.com/Eyozy/flomo-to-markdown.git
cd flomo-to-markdown

# 安装 CLI 版本开发依赖
# (建议使用虚拟环境，例如 `python -m venv venv` 然后 `source venv/bin/activate`)
pip install -r requirements-cli.txt

# 如果需要开发 Web 版本，安装所有依赖
pip install -r requirements.txt

# 注意：Web 开发需要确保 `static/` 文件夹存在，其中包含 CSS/JS 等 Web 资源
```

## 许可证

本项目基于 [MIT 许可证](https://opensource.org/licenses/MIT) 开源，查看 [LICENSE](LICENSE) 文件了解详情。
