import re
import jieba
import nltk
from nltk.tokenize import sent_tokenize

# 尝试下载nltk数据，如果已存在则跳过
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def split_text_into_scenes(text, max_scenes=10):
    """
    将输入文本分割成场景列表
    
    Args:
        text (str): 输入的文本内容
        max_scenes (int): 最大场景数量
        
    Returns:
        list: 场景文本列表
    """
    # 移除多余空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 检测语言（简单判断是否为中文）
    is_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    
    if is_chinese:
        # 中文文本处理
        # 按句号、问号、感叹号分割，保留标点
        sentences = re.findall(r'[^。！？]+[。！？]', text)
        if not sentences and text:
            sentences = [text]  # 如果没有分割成功，则将整个文本作为一个句子
    else:
        # 英文文本处理
        sentences = sent_tokenize(text)
    
    # 如果句子数量少于max_scenes，直接返回每个句子作为一个场景
    if len(sentences) <= max_scenes:
        return sentences
    
    # 将句子合并为场景，尽量平均分配
    scenes = []
    sentences_per_scene = len(sentences) // max_scenes
    remainder = len(sentences) % max_scenes
    
    start_idx = 0
    for i in range(max_scenes):
        # 为前remainder个场景多分配一个句子
        end_idx = start_idx + sentences_per_scene + (1 if i < remainder else 0)
        scene = ' '.join(sentences[start_idx:end_idx])
        scenes.append(scene)
        start_idx = end_idx
    
    return scenes

def generate_scene_descriptions(scenes):
    """
    为每个场景生成描述，用于图像生成
    
    Args:
        scenes (list): 场景文本列表
        
    Returns:
        list: 场景描述列表，用于图像生成
    """
    descriptions = []
    
    for scene in scenes:
        # 移除多余空白字符
        scene = re.sub(r'\s+', ' ', scene).strip()
        
        # 检测语言
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', scene))
        
        if is_chinese:
            # 中文场景处理
            # 使用jieba提取关键词和短语
            words = jieba.cut(scene)
            # 过滤掉停用词和标点符号
            filtered_words = [w for w in words if len(w) > 1 and not re.match(r'[\W\d]+', w)]
            
            # 提取主要名词和动词作为描述
            if filtered_words:
                # 简单提取前10个有意义的词
                key_terms = filtered_words[:10]
                description = scene if len(scene) < 100 else ' '.join(key_terms)
            else:
                description = scene
        else:
            # 英文场景处理
            # 简化处理，直接使用原始场景文本
            description = scene if len(scene) < 100 else scene[:100] + '...'
        
        descriptions.append(description)
    
    return descriptions

def generate_prompts(scene_descriptions, style="default"):
    """
    根据场景描述和风格生成图像生成提示词
    
    Args:
        scene_descriptions (list): 场景描述列表
        style (str): 漫画风格
        
    Returns:
        list: 提示词列表
    """
    # 风格提示词映射
    style_prompts = {
        'default': ', comic style, detailed, vibrant colors',
        'anime': ', anime style, manga, detailed, vibrant colors',
        'realistic': ', realistic style, detailed, photorealistic',
        'watercolor': ', watercolor style, artistic, soft colors',
        'sketch': ', sketch style, pencil drawing, black and white'
    }
    
    # 获取风格提示词，如果不存在则使用默认风格
    style_prompt = style_prompts.get(style, style_prompts['default'])
    
    # 为每个场景描述生成提示词
    prompts = []
    for description in scene_descriptions:
        # 检测语言
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', description))
        
        if is_chinese:
            # 中文描述，添加英文翻译提示
            prompt = f"scene from a story: {description}, illustration{style_prompt}"
        else:
            # 英文描述
            prompt = f"scene from a story: {description}, illustration{style_prompt}"
        
        prompts.append(prompt)
    
    return prompts

def generate_negative_prompts(style="default"):
    """
    根据风格生成负面提示词
    
    Args:
        style (str): 漫画风格
        
    Returns:
        str: 负面提示词
    """
    # 风格负面提示词映射
    style_negative_prompts = {
        'default': 'blurry, low quality, distorted, deformed',
        'anime': 'blurry, low quality, distorted, deformed, photorealistic',
        'realistic': 'cartoon, anime, sketch, drawing, blurry',
        'watercolor': 'digital art, sharp edges, blurry, low quality',
        'sketch': 'color, painting, digital art, blurry, low quality'
    }
    
    # 获取风格负面提示词，如果不存在则使用默认风格
    negative_prompt = style_negative_prompts.get(style, style_negative_prompts['default'])
    
    # 添加通用负面提示词
    common_negative = "text, watermark, signature, logo, nsfw, nude, bad anatomy, bad hands, extra fingers"
    
    return f"{negative_prompt}, {common_negative}"
