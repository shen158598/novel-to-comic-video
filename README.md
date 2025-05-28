# 小说转漫画视频生成器

一个将小说文本转换为漫画视频的Web应用，支持多种漫画风格、AI配音和背景音乐。

## 功能特点

- **文本转漫画**：输入小说文本，自动转换为漫画风格的图像，支持多种风格选择
- **漫画视频生成**：将生成的漫画图像合成为视频，添加平滑过渡效果，提升观看体验
- **智能配音**：为视频添加AI配音，支持多种声音选择，增强视听体验
- **背景音乐**：可选择添加背景音乐，提升视频质量
- **多种风格**：支持默认漫画风格、动漫风格、写实风格、水彩风格和素描风格

## 技术栈

- **后端**：Flask (Python)
- **前端**：HTML, CSS, JavaScript, Bootstrap
- **图像生成**：Stable Diffusion
- **语音合成**：Azure TTS
- **视频处理**：MoviePy

## 安装与使用

1. 克隆仓库
```bash
git clone https://github.com/shen158598/novel-to-comic-video.git
cd novel-to-comic-video
```

2. 运行应用
```bash
# Windows
run.bat

# Linux/Mac
bash run.sh
```

3. 打开浏览器访问 http://localhost:5000

## 配置

在使用前，请确保配置以下内容：

1. 创建 `.env` 文件（参考 `.env.example`）
2. 配置 API 密钥（OpenAI、Azure TTS 等）
3. 下载背景音乐文件并放置在 `static/audio/background.mp3`

## 许可证

MIT
