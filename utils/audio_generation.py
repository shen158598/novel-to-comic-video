import os
import time
import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, DEFAULT_VOICE

def generate_speech(text, output_path, voice_name=None, rate=0, pitch=0):
    """
    使用Azure语音服务生成语音
    
    Args:
        text (str): 要转换为语音的文本
        output_path (str): 输出音频文件路径
        voice_name (str): 语音名称，默认使用配置中的DEFAULT_VOICE
        rate (int): 语速调整，范围-100到100
        pitch (int): 音调调整，范围-100到100
        
    Returns:
        bool: 是否成功生成语音
    """
    # 检查API密钥是否配置
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print("错误: 未配置Azure语音服务API密钥或区域")
        return False
    
    # 使用默认语音
    if voice_name is None:
        voice_name = DEFAULT_VOICE
    
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建语音配置
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY, 
            region=AZURE_SPEECH_REGION
        )
        
        # 设置语音
        speech_config.speech_synthesis_voice_name = voice_name
        
        # 创建音频配置
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
        
        # 创建语音合成器
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        # 构建SSML以控制语速和音调
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
            <voice name="{voice_name}">
                <prosody rate="{rate}%" pitch="{pitch}%">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        # 合成语音
        result = speech_synthesizer.speak_ssml_async(ssml).get()
        
        # 检查结果
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"语音生成成功: {output_path}")
            return True
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"语音合成取消: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"错误详情: {cancellation_details.error_details}")
            return False
    except Exception as e:
        print(f"语音生成失败: {e}")
        return False

def generate_audio_for_scenes(scenes, output_dir, voice_name=None):
    """
    为多个场景生成音频文件
    
    Args:
        scenes (list): 场景文本列表
        output_dir (str): 输出目录
        voice_name (str): 语音名称
        
    Returns:
        list: 生成的音频文件路径列表
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成音频
    audio_paths = []
    for i, scene in enumerate(scenes):
        # 构建输出路径
        audio_path = os.path.join(output_dir, f"scene_{i:03d}.mp3")
        
        # 生成语音
        success = generate_speech(
            text=scene,
            output_path=audio_path,
            voice_name=voice_name
        )
        
        if success:
            audio_paths.append(audio_path)
            print(f"生成音频 {i+1}/{len(scenes)}: {audio_path}")
        else:
            print(f"生成音频 {i+1}/{len(scenes)} 失败")
            # 如果生成失败，添加一个空路径
            audio_paths.append(None)
        
        # 添加短暂延迟，避免API限制
        time.sleep(0.5)
    
    return audio_paths

def get_available_voices():
    """
    获取可用的语音列表
    
    Returns:
        list: 语音信息列表
    """
    # 检查API密钥是否配置
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print("错误: 未配置Azure语音服务API密钥或区域")
        return []
    
    try:
        # 创建语音配置
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY, 
            region=AZURE_SPEECH_REGION
        )
        
        # 创建语音合成器
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=None
        )
        
        # 获取可用语音
        result = speech_synthesizer.get_voices_async().get()
        
        # 检查结果
        if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
            voices = []
            for voice in result.voices:
                # 只保留中文和英文语音
                if voice.locale.startswith('zh-') or voice.locale.startswith('en-'):
                    voices.append({
                        'name': voice.name,
                        'display_name': voice.short_name,
                        'locale': voice.locale,
                        'gender': voice.gender,
                        'style': voice.style_list
                    })
            return voices
        else:
            print(f"获取语音列表失败: {result.reason}")
            return []
    except Exception as e:
        print(f"获取语音列表失败: {e}")
        return []

def get_voice_duration(audio_path):
    """
    获取音频文件的持续时间（秒）
    
    Args:
        audio_path (str): 音频文件路径
        
    Returns:
        float: 音频持续时间（秒）
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # 毫秒转秒
    except Exception as e:
        print(f"获取音频持续时间失败: {e}")
        # 如果无法获取，返回估计值（每个中文字符约0.3秒）
        try:
            with open(audio_path, 'rb') as f:
                # 简单估计MP3文件大小与时长的关系
                file_size = len(f.read())
                estimated_duration = file_size / 10000  # 粗略估计
                return max(estimated_duration, 1.0)  # 至少1秒
        except:
            return 3.0  # 默认3秒
