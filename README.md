# Flomo to Markdown

[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个专为 [Flomo](https://flomoapp.com/) 用户设计的简洁、强大的笔记转换工具。它能将您导出的 HTML 文件连同所有图片，一键转换为一个按时间倒序排列、结构清晰的 Markdown 文件，方便您进行本地归档、二次编辑或迁移到其他平台。

---

## 🌟 核心功能

- **📥 智能解析**: 自动从 HTML 文件中提取每一条 MEMO，无需手动复制粘贴。
- **🖼️ 图片无忧**: 自动查找、复制并更新笔记中的图片路径，确保图片在新文件中完美显示。
- **🏷️ 唯一文件名**: 为所有图片添加日期前缀并重命名，彻底解决同名文件覆盖问题。
- **⏰ 倒序排列**: 所有笔记严格按时间倒序排列，最新的思考永远在最前面。
- **📄 格式优雅**: 输出的 Markdown 文件以日期为大标题，每日笔记清晰分组，格式干净统一。
- **⚙️ 简单配置**: 脚本顶部的配置项清晰明了，可轻松自定义输入和输出路径。

## 🚀 快速上手

只需三步，即可完成您的笔记转换。

### 1. 环境准备

确保您的电脑已安装 **Python 3.6** 或更高版本。在终端或命令行中运行以下命令进行检查：

```bash
python --version
# 或者在某些系统上使用
python3 --version
```

> **提示**: Windows 用户在安装 Python 时，请务必勾选 `Add Python to PATH` 选项。

### 2. 下载并安装依赖

首先，获取项目文件。您可以直接下载 ZIP 包，或使用 Git 克隆：

```bash
git clone https://github.com/Eyozy/flomo-to-markdown.git
cd flomo-to-markdown
```

然后，进入项目目录，使用 `pip` 安装所需的依赖库：

```bash
pip install -r requirements.txt
```

### 3. 运行转换

一切就绪！在运行脚本前，请按下图所示准备您的文件：

```plaintext
flomo-to-markdown/      <-- 项目根目录
├── flomo/              <-- 您的 Flomo 笔记文件夹 (默认源目录)
│   ├── 你的笔记.html    <-- 导出的 HTML 文件
│   └── file/           <-- 导出的图片文件夹
└── flomo_converter.py  <-- 转换脚本
```

最后，在项目根目录运行脚本：

```bash
python flomo_converter.py
```

转换完成后，您将在 `converted_notes` 文件夹中找到成果！

## ⚙️ 自定义配置

如果需要修改默认的文件夹名称，可以直接编辑 `flomo_converter.py` 文件顶部的配置区域：

```python
# --- 配置项 (Configuration) ---

# 1. 源文件夹：存放您 Flomo 笔记的地方
SOURCE_DIR = 'flomo'

# 2. 输出文件夹：转换结果的存放位置
OUTPUT_DIR = 'converted_notes'

# 3. 输出文件名：生成的 Markdown 文件的名字
MARKDOWN_FILENAME = 'flomo-output.md'

# 4. 图片子文件夹：存放所有图片的子文件夹的名字
IMAGE_SUBDIR_NAME = 'flomo-images'
```

## ❓ 常见问题

**Q1: 我的 HTML 笔记文件名不是固定的，脚本能找到吗？**

A: 可以。脚本会自动在 `flomo` 文件夹内查找第一个 `.html` 或 `.htm` 后缀的文件进行处理，所以您无需修改笔记文件名。

**Q2: 如果我的源文件夹里有多个 HTML 文件，会怎么样？**

A: 脚本会依次读取所有 HTML 文件，并将其中全部的笔记内容提取出来，然后统一进行排序，最后合并到同一个 Markdown 文件中。

**Q3: 如果我的笔记中没有图片，脚本会报错吗？**

A: 不会。脚本会智能检测是否存在图片，如果没有图片则会跳过相关处理步骤，不会影响正常转换。

**Q4: 为什么运行后 `flomo-images` 文件夹是空的？**

A: 这通常意味着脚本在您的 HTML 文件中没有找到任何 `<img>` 标签，或者图片的路径不正确。请确认：
1.  您的笔记中确实包含图片。
2.  从 Flomo 导出的 `file` 文件夹已正确放置在源文件夹 (`flomo/`) 内。
3.  脚本运行过程中没有出现 "图片文件未找到" 的警告信息。

**Q5: 脚本运行报错怎么办？**

A: 请优先检查以下两点：
1.  是否已按照“安装与配置”章节的说明，正确安装了 `requirements.txt` 中的依赖库。
2.  文件目录结构是否与文档中描述的完全一致。如果问题仍然存在，欢迎通过 [GitHub Issues](https://github.com/Eyozy/flomo-to-markdown/issues) 向我们报告。
  
## 🤝 参与贡献

欢迎任何形式的贡献，无论是报告问题、提出建议还是贡献代码！

### 报告问题

- 使用 [GitHub Issues](https://github.com/Eyozy/flomo-to-markdown/issues) 报告 Bug 或功能建议
- 提供详细的问题描述和复现步骤
- 包含您的操作系统和 Python 版本信息

### 贡献代码

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/Eyozy/flomo-to-markdown.git
cd flomo-to-markdown

# 安装开发依赖
pip install -r requirements.txt
```

## 📄 许可证

本项目基于 [MIT 许可证](https://opensource.org/licenses/MIT) 开源，查看 [LICENSE](LICENSE) 文件了解详情。