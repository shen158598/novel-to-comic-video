import os
import torch
import numpy as np
from PIL import Image
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from config import IMAGE_WIDTH, IMAGE_HEIGHT, DEFAULT_MODEL, HF_API_KEY

# 检查是否有可用的GPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# 模型缓存
pipeline_cache = {}

def get_pipeline(model_id=None):
    """
    获取或加载Stable Diffusion模型管道
    
    Args:
        model_id (str): 模型ID，默认使用配置中的DEFAULT_MODEL
        
    Returns:
        StableDiffusionPipeline: 加载好的模型管道
    """
    if model_id is None:
        model_id = DEFAULT_MODEL
    
    # 如果模型已经加载，直接返回缓存的管道
    if model_id in pipeline_cache:
        return pipeline_cache[model_id]
    
    # 加载模型
    try:
        # 使用DPMSolverMultistepScheduler以获得更好的质量和速度平衡
        scheduler = DPMSolverMultistepScheduler.from_pretrained(
            model_id, 
            subfolder="scheduler",
            use_auth_token=HF_API_KEY if HF_API_KEY else None
        )
        
        pipeline = StableDiffusionPipeline.from_pretrained(
            model_id,
            scheduler=scheduler,
            use_auth_token=HF_API_KEY if HF_API_KEY else None
        )
        
        # 移动到设备
        pipeline = pipeline.to(device)
        
        # 启用注意力切片以减少内存使用
        if hasattr(pipeline, "enable_attention_slicing"):
            pipeline.enable_attention_slicing()
        
        # 如果是CUDA设备，启用内存高效的注意力
        if device == "cuda" and hasattr(pipeline, "enable_xformers_memory_efficient_attention"):
            try:
                pipeline.enable_xformers_memory_efficient_attention()
            except Exception as e:
                print(f"无法启用xformers优化: {e}")
        
        # 缓存管道
        pipeline_cache[model_id] = pipeline
        
        return pipeline
    except Exception as e:
        print(f"加载模型失败: {e}")
        # 如果加载失败，尝试使用默认模型
        if model_id != DEFAULT_MODEL:
            print(f"尝试加载默认模型: {DEFAULT_MODEL}")
            return get_pipeline(DEFAULT_MODEL)
        raise

def generate_image(prompt, negative_prompt=None, width=None, height=None, model_id=None, seed=None):
    """
    根据提示词生成图像
    
    Args:
        prompt (str): 图像生成提示词
        negative_prompt (str): 负面提示词
        width (int): 图像宽度
        height (int): 图像高度
        model_id (str): 模型ID
        seed (int): 随机种子
        
    Returns:
        PIL.Image: 生成的图像
    """
    # 使用配置中的默认值
    if width is None:
        width = IMAGE_WIDTH
    if height is None:
        height = IMAGE_HEIGHT
    
    # 获取模型管道
    pipeline = get_pipeline(model_id)
    
    # 设置随机种子
    if seed is None:
        seed = np.random.randint(0, 2147483647)
    generator = torch.Generator(device=device).manual_seed(seed)
    
    # 生成图像
    with torch.no_grad():
        result = pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=30,  # 推理步数，影响质量和速度
            guidance_scale=7.5,      # 提示词引导强度
            generator=generator
        )
    
    # 返回生成的图像
    image = result.images[0]
    
    # 记录生成信息
    generation_info = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "model_id": model_id or DEFAULT_MODEL,
        "seed": seed
    }
    
    return image, generation_info

def generate_images_for_scenes(prompts, negative_prompt, output_dir, style="default", model_id=None):
    """
    为多个场景生成图像
    
    Args:
        prompts (list): 提示词列表
        negative_prompt (str): 负面提示词
        output_dir (str): 输出目录
        style (str): 漫画风格
        model_id (str): 模型ID
        
    Returns:
        list: 生成的图像文件路径列表
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 根据风格调整图像尺寸
    width, height = IMAGE_WIDTH, IMAGE_HEIGHT
    if style == "anime":
        # 动漫风格通常使用16:9比例
        width, height = 768, 432
    elif style == "sketch":
        # 素描风格使用正方形
        width, height = 512, 512
    
    # 生成图像
    image_paths = []
    for i, prompt in enumerate(prompts):
        try:
            # 生成图像
            image, info = generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                model_id=model_id,
                seed=None  # 使用随机种子
            )
            
            # 保存图像
            image_path = os.path.join(output_dir, f"scene_{i:03d}.png")
            image.save(image_path)
            
            # 添加到路径列表
            image_paths.append(image_path)
            
            print(f"生成图像 {i+1}/{len(prompts)}: {image_path}")
        except Exception as e:
            print(f"生成图像 {i+1}/{len(prompts)} 失败: {e}")
            # 如果生成失败，创建一个空白图像
            blank_image = Image.new('RGB', (width, height), color='white')
            image_path = os.path.join(output_dir, f"scene_{i:03d}.png")
            blank_image.save(image_path)
            image_paths.append(image_path)
    
    return image_paths

def cleanup_resources():
    """
    清理资源，释放GPU内存
    """
    global pipeline_cache
    
    # 清空模型缓存
    for model_id, pipeline in pipeline_cache.items():
        del pipeline
    
    # 清空缓存字典
    pipeline_cache = {}
    
    # 清理CUDA缓存
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
