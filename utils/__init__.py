# 小说转漫画视频应用 - 工具包

# 导入所有工具模块，方便从utils包直接导入
from utils.text_processing import (
    split_text_into_scenes,
    generate_scene_descriptions,
    generate_prompts_for_style
)

from utils.image_generation import (
    generate_image,
    generate_images_for_scenes,
    cleanup_resources
)

from utils.audio_generation import (
    generate_audio_for_text,
    generate_audio_for_scenes,
    get_available_voices,
    estimate_audio_duration
)

from utils.video_creation import (
    create_video,
    create_video_with_transitions,
    create_video_from_images_and_audio
)

__all__ = [
    'split_text_into_scenes',
    'generate_scene_descriptions',
    'generate_prompts_for_style',
    'generate_image',
    'generate_images_for_scenes',
    'cleanup_resources',
    'generate_audio_for_text',
    'generate_audio_for_scenes',
    'get_available_voices',
    'estimate_audio_duration',
    'create_video',
    'create_video_with_transitions',
    'create_video_from_images_and_audio'
]
