import os
import random
import numpy as np
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, VideoFileClip
from moviepy.editor import vfx, transfx
from config import FPS, VIDEO_CODEC, AUDIO_CODEC
from utils.audio_generation import get_voice_duration

def create_video(image_paths, audio_paths, output_path, fps=None, use_transitions=False, add_background_music=False):
    """
    创建视频，将图像和音频合成为视频
    
    Args:
        image_paths (list): 图像文件路径列表
        audio_paths (list): 音频文件路径列表，可以为None
        output_path (str): 输出视频文件路径
        fps (int): 帧率，默认使用配置中的FPS
        use_transitions (bool): 是否使用过渡效果
        add_background_music (bool): 是否添加背景音乐
        
    Returns:
        str: 输出视频文件路径
    """
    # 使用默认帧率
    if fps is None:
        fps = FPS
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 创建视频片段列表
    video_clips = []
    
    # 处理每个场景
    for i, image_path in enumerate(image_paths):
        # 加载图像
        try:
            img = Image.open(image_path)
            # 确保图像是RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_array = np.array(img)
        except Exception as e:
            print(f"加载图像失败 {image_path}: {e}")
            # 创建空白图像
            img_array = np.zeros((512, 768, 3), dtype=np.uint8)
            img_array.fill(255)  # 白色背景
        
        # 确定片段持续时间
        duration = 3.0  # 默认3秒
        if audio_paths and i < len(audio_paths) and audio_paths[i]:
            # 如果有对应的音频，使用音频持续时间
            duration = get_voice_duration(audio_paths[i])
            # 确保最短持续时间
            duration = max(duration, 2.0)
        
        # 创建图像片段
        image_clip = ImageClip(img_array).set_duration(duration)
        
        # 添加音频（如果有）
        if audio_paths and i < len(audio_paths) and audio_paths[i]:
            try:
                audio_clip = AudioFileClip(audio_paths[i])
                image_clip = image_clip.set_audio(audio_clip)
            except Exception as e:
                print(f"加载音频失败 {audio_paths[i]}: {e}")
        
        # 添加到视频片段列表
        video_clips.append(image_clip)
    
    # 如果启用过渡效果，添加过渡
    if use_transitions and len(video_clips) > 1:
        video_clips = create_video_with_transitions(video_clips)
    
    # 合并所有片段
    final_clip = concatenate_videoclips(video_clips, method="compose")
    
    # 添加背景音乐（如果启用）
    if add_background_music:
        try:
            # 检查背景音乐文件是否存在
            bg_music_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'audio', 'background.mp3')
            if os.path.exists(bg_music_path):
                # 加载背景音乐
                bg_music = AudioFileClip(bg_music_path)
                
                # 循环背景音乐以匹配视频长度
                if bg_music.duration < final_clip.duration:
                    bg_music = bg_music.loop(duration=final_clip.duration)
                else:
                    # 裁剪音乐以匹配视频长度
                    bg_music = bg_music.subclip(0, final_clip.duration)
                
                # 降低背景音乐音量
                bg_music = bg_music.volumex(0.3)
                
                # 混合原始音频和背景音乐
                if final_clip.audio is not None:
                    final_audio = CompositeAudioClip([final_clip.audio, bg_music])
                    final_clip = final_clip.set_audio(final_audio)
                else:
                    final_clip = final_clip.set_audio(bg_music)
        except Exception as e:
            print(f"添加背景音乐失败: {e}")
    
    # 写入视频文件
    final_clip.write_videofile(
        output_path,
        fps=fps,
        codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC,
        threads=4,
        preset='medium'
    )
    
    # 清理资源
    final_clip.close()
    
    return output_path

def create_video_with_transitions(video_clips):
    """
    为视频片段添加过渡效果
    
    Args:
        video_clips (list): 视频片段列表
        
    Returns:
        list: 添加了过渡效果的视频片段列表
    """
    # 可用的过渡效果列表
    transitions = [
        transfx.crossfadein,
        transfx.crossfadeout,
        transfx.fade_in_color,
        transfx.fade_out_color
    ]
    
    # 过渡持续时间（秒）
    transition_duration = 0.5
    
    # 结果片段列表
    result_clips = []
    
    for i, clip in enumerate(video_clips):
        # 第一个片段不需要入场过渡
        if i > 0:
            # 随机选择一个入场过渡效果
            transition_in = random.choice(transitions)
            
            if transition_in == transfx.fade_in_color or transition_in == transfx.crossfadein:
                # 应用入场过渡
                if transition_in == transfx.fade_in_color:
                    # 随机颜色
                    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    clip = clip.fx(transition_in, transition_duration, color)
                else:
                    clip = clip.fx(transition_in, transition_duration)
        
        # 最后一个片段不需要出场过渡
        if i < len(video_clips) - 1:
            # 随机选择一个出场过渡效果
            transition_out = random.choice(transitions)
            
            if transition_out == transfx.fade_out_color or transition_out == transfx.crossfadeout:
                # 应用出场过渡
                if transition_out == transfx.fade_out_color:
                    # 随机颜色
                    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    clip = clip.fx(transition_out, transition_duration, color)
                else:
                    clip = clip.fx(transition_out, transition_duration)
        
        result_clips.append(clip)
    
    return result_clips

# 为了兼容性，保留原始函数名但调用新函数
def create_video_from_images_and_audio(image_paths, audio_paths, output_path, fps=None):
    """
    兼容性函数，调用create_video
    """
    return create_video(image_paths, audio_paths, output_path, fps)

# 添加CompositeAudioClip类，用于混合多个音频
class CompositeAudioClip:
    def __init__(self, audio_clips):
        self.audio_clips = audio_clips
        self.duration = max([c.duration for c in audio_clips])
    
    def to_soundarray(self, tt):
        # 混合所有音频片段
        arrays = [c.to_soundarray(tt) for c in self.audio_clips]
        # 确保所有数组具有相同的形状
        shapes = [a.shape for a in arrays]
        if not all(s == shapes[0] for s in shapes):
            # 如果形状不同，调整为最大形状
            max_shape = max(shapes, key=lambda s: s[0])
            for i, a in enumerate(arrays):
                if a.shape != max_shape:
                    new_array = np.zeros(max_shape)
                    new_array[:a.shape[0]] = a
                    arrays[i] = new_array
        # 混合音频（简单相加，然后归一化）
        result = sum(arrays)
        # 防止音频过载
        result = np.clip(result, -1.0, 1.0)
        return result
