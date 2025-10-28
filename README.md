# flomo-to-markdown

[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个专为 [flomo](https://flomoapp.com/) 用户设计的笔记转换工具，一键将 flomo 导出的 HTML 文件（包含图片）转换为结构清晰、按时间倒序排列的 Markdown 文件，助你轻松实现笔记的本地归档、二次编辑或无缝迁移至其他平台。

在线预览及使用：[flomo to Markdown](https://flomo-to-markdown.vercel.app/)

---

## ✨ 项目亮点

🌟 **核心功能**

-   🤖 **智能解析：** 自动从 HTML 文件中精准提取 MEMO 内容，包括标签、链接。
-   🖼️ **图片处理：** 自动查找、拷贝图片并更新 Markdown 路径，支持非同级目录图片。
-   🏷️ **图片命名：** 添加日期时间戳前缀，避免同名覆盖。
-   ⏳ **倒序排列：** 笔记按时间倒序组织，最新内容置顶。
-   📂 **多样导出模式：** 支持单一合并文件、单条 Memo 文件或按年归档。
-   ✨ **Markdown 格式：** 输出文件以日期为标题，每日笔记清晰分组，美观易读。
-   ⚙️ **高度可配置：** 通过命令行参数或配置文件自定义路径、图片子文件夹等。
-   🚀 **增强型 CLI：** 命令行界面支持彩色输出、进度条、信息查询和交互式年份选择。
-   🌐 **Web 界面：** 提供网页应用，方便用户通过浏览器上传 HTML/ZIP 转换和下载，支持多种导出和年份筛选。

## 🚀 快速上手

### 1. 环境准备

确保你的电脑已安装 **Python 3.6** 或更高版本。在终端或命令行中运行以下命令进行检查：

```bash
python --version
# 或者在某些系统上使用
python3 --version
```

> **提示**：Windows 用户在安装 Python 时，请务必勾选 `Add Python to PATH` 选项。

### 2. 克隆项目并安装依赖

首先，获取项目文件。你可以直接下载 ZIP 包，或使用 Git 克隆：

```bash
git clone https://github.com/Eyozy/flomo-to-markdown.git
cd flomo-to-markdown
```

然后，进入项目目录，根据你想要使用的功能安装所需的依赖库：

**CLI 版本（本地命令行使用）**：

```bash
pip install -r requirements-cli.txt
```

**Web 版本（本地运行网页应用）**：

```bash
pip install -r requirements.txt
```

### 3. 运行转换

#### CLI 版本

在运行脚本前，请按照以下结构准备你的 flomo 导出文件：

```plaintext
flomo-to-markdown/      <-- 项目根目录
├── flomo/              <-- 你的 flomo 笔记文件夹 (默认源目录)
│   ├── 你的笔记.html    <-- flomo 导出的 HTML 文件 (文件名无需固定)
│   └── file/           <-- flomo 导出的图片文件夹 (可选，如果笔记包含图片)
└── flomo_converter.py  <-- 转换脚本
```

**基础用法：**

```bash
# 转换所有年份的笔记，使用默认的单一合并文件模式
python flomo_converter.py

# 转换特定年份（例如 2023 年）的笔记，使用默认的单一合并文件模式
python flomo_converter.py --year 2025
```

**高级功能：**

CLI 工具提供了丰富的参数，你可以通过 `python flomo_converter.py --help` 查看所有选项。

```bash
# 查看 HTML 文件中包含的可用笔记年份
python flomo_converter.py --list-years

# 查看文件详细信息，包括各年份笔记数量统计
python flomo_converter.py --info

# 交互式选择要转换的年份，系统会提示你进行选择
python flomo_converter.py --interactive

# 导出为单条 Memo 文件模式 (每个 Memo 生成一个独立的 .md 文件)
python flomo_converter.py --export-mode single_memos

# 导出为单条 Memo 文件模式，并指定年份（例如 2025 年）
python flomo_converter.py --export-mode single_memos --year 2025

# 导出为按年归档模式 (每年一个文件夹，内含该年份所有 Memo 文件)
python flomo_converter.py --export-mode yearly_archives

# 导出为按年归档模式，并指定年份（例如 2025 年）
python flomo_converter.py --export-mode yearly_archives --year 2025

# 自定义 flomo 源文件夹和 Markdown 输出文件夹
python flomo_converter.py --source ./my_flomo_exports --output ./my_markdown_notes
```

转换完成后，你将在 `converted_notes` 文件夹中找到转换后的结果。

#### Web 版本

```bash
# 本地运行：
python app.py
```
打开浏览器访问 `http://127.0.0.1:5001` 即可使用。

Web 界面支持功能：

-   **上传文件：** 可以上传单个 `.html` / `.htm` 文件，或包含 HTML 文件及 `file/` 图片文件夹的 `.zip` 压缩包。
-   **年份筛选：** 上传后会自动解析笔记中的年份，你可以选择转换特定年份的笔记。
-   **导出模式：** 支持与 CLI 版本相同的多种导出模式（单一合并文件、单条 Memo 文件、按年归档）。
-   **智能下载：** 根据转换结果（是否包含图片、导出模式），自动提供 `.md` 文件或 `.zip` 压缩包下载。
-   **速率限制：** 为防止滥用，Web 服务对文件上传和解析请求进行了速率限制。

## ⚙️ 自定义配置

本项目支持用户创建 `~/.flomo-converter.json` 配置文件来修改默认设置。

**如何创建配置文件：**

你需要手动在用户主目录创建一个名为 `.flomo-converter.json` 的文件，例如 macOS/Linux 上是 `/Users/你的用户名/`，Windows 上是 `C:\Users\你的用户名\`。

**配置文件示例 (`~/.flomo-converter.json`)：**

```json
{
  "source_dir": "my_flomo_data",         // flomo 笔记源文件夹名称
  "output_dir": "my_converted_notes",    // 转换结果输出文件夹名称
  "image_subdir_name": "my-flomo-images",// 存放所有图片的子文件夹名称
  "enable_colors": true,                 // CLI 输出是否启用彩色
  "show_progress": true                  // CLI 输出是否显示进度条
}
```

**配置项说明：**

-   `source_dir`：存放你 flomo 笔记的源文件夹名称 (默认：`flomo`)。
-   `output_dir`：转换结果的存放位置 (默认：`converted_notes`)。
-   `image_subdir_name`：存放所有图片的子文件夹名称 (默认：`flomo-images`)。
-   `enable_colors`：CLI 输出是否启用彩色 (默认：`true`)。
-   `show_progress`：CLI 输出是否显示进度条 (默认：`true`)。

> **注意**：命令行参数的优先级高于配置文件。如果同时设置，命令行参数将覆盖配置文件中的值。

## ❓ 常见问题

**Q1: 我的 HTML 笔记文件名不是固定的，脚本能找到吗？**

A: 可以。脚本会自动在 `source_dir` (默认 `flomo`) 文件夹内查找第一个 `.html` 或 `.htm` 后缀的文件进行处理，所以你无需修改笔记文件名。

**Q2: 如果我的源文件夹里有多个 HTML 文件，会怎么样？**

A: 脚本会依次读取所有 HTML 文件，并将其中全部的笔记内容提取出来，然后统一进行排序，最后合并到同一个 Markdown 文件中（如果采用 `single_file` 模式）。

**Q3: 如果我的笔记中没有图片，脚本会报错吗？**

A: 不会。脚本会智能检测是否存在图片，如果没有图片则会跳过相关的图片处理步骤，不会影响正常转换。

**Q4: 为什么运行后 `flomo-images` 文件夹是空的？**

A: 这通常意味着脚本在你的 HTML 文件中没有找到任何 `<img>` 标签，或者图片路径不正确。请确认：
1.  你的 flomo 笔记中确实包含图片。
2.  从 flomo 导出的 `file` 文件夹已正确放置在源文件夹 (`flomo/` 或你自定义的 `source_dir/`) 内。脚本会尝试在 `file/YYYY-MM-DD/` 结构中查找图片。
3.  脚本运行过程中没有出现 "图片文件未找到" 的警告信息。

**Q5: 脚本运行报错怎么办？**

A: 请优先检查以下两点：
1.  是否已按照“安装与配置”章节的说明，正确安装了 `requirements-cli.txt` 或 `requirements.txt` 中的所有依赖库。
2.  文件目录结构是否与文档中描述的完全一致。
如果问题仍然存在，欢迎通过 [GitHub Issues](https://github.com/Eyozy/flomo-to-markdown/issues) 向我们报告。请提供详细的错误信息、你的操作系统和 Python 版本。

## 🤝 参与贡献

我们非常欢迎任何形式的贡献，无论是报告问题、提出建议还是贡献代码！

### 报告问题

-   请在 [GitHub Issues](https://github.com/Eyozy/flomo-to-markdown/issues) 页面提交 Bug 报告或功能建议。
-   提供详细的问题描述、复现步骤及预期结果。
-   请务必包含你的操作系统和 Python 版本信息，以便我们更好地定位问题。

### 贡献代码

1.  Fork 本项目到你自己的 GitHub 仓库。
2.  创建你的特性分支 (`git checkout -b feature/YourAmazingFeature`)。
3.  提交你的更改 (`git commit -m 'feat: Add some AmazingFeature'`)。
4.  将分支推送到你的 Forked 仓库 (`git push origin feature/YourAmazingFeature`)。
5.  在本项目仓库中开启一个 Pull Request，详细描述你的更改和解决的问题。

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

# 注意：Web 开发需要确保 `static/` 文件夹存在，其中包含 CSS/JS 等 Web 资源。
```

## 📄 许可证

本项目基于 [MIT 许可证](https://opensource.org/licenses/MIT) 开源。查看 [LICENSE](LICENSE) 文件了解详情。