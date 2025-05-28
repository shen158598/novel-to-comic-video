import os
import time
import uuid
import threading
import logging
import shutil
import random
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from utils.text_processor import process_text
from utils.image_generator import generate_images, preload_model
from utils.audio_generator import generate_audio, get_available_voices
from utils.video_creator import create_video, create_video_with_transitions
import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB上传限制
CORS(app)

# 全局任务字典，用于跟踪任务状态
tasks = {}

# 确保输出目录存在
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
os.makedirs(config.STATIC_FOLDER, exist_ok=True)
os.makedirs(config.TEMPLATE_FOLDER, exist_ok=True)

# 在后台线程中预加载模型
threading.Thread(target=preload_model, daemon=True).start()

# 主页路由
@app.route('/')
def index():
    # 获取可用的语音列表
    voices = get_available_voices()
    # 获取可用的漫画风格
    styles = config.COMIC_STYLES
    return render_template('index.html', voices=voices, styles=styles)

# 关于页面
@app.route('/about')
def about():
    return render_template('about.html')

# API路由 - 生成漫画视频
@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        # 获取请求数据
        data = request.json
        text = data.get('text', '')
        style = data.get('style', 'default')
        voice = data.get('voice', config.DEFAULT_VOICE)
        use_transitions = data.get('use_transitions', True)  # 是否使用过渡效果
        add_background_music = data.get('add_background_music', False)  # 是否添加背景音乐
        
        # 验证输入
        if not text:
            return jsonify({'error': '请提供文本内容'}), 400
        
        if len(text) > config.MAX_TEXT_LENGTH:
            return jsonify({'error': f'文本长度超过限制（{config.MAX_TEXT_LENGTH}字）'}), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务输出目录
        task_output_folder = os.path.join(config.OUTPUT_FOLDER, task_id)
        os.makedirs(task_output_folder, exist_ok=True)
        
        # 初始化任务状态
        tasks[task_id] = {
            'status': 'processing',
            'progress': 0,
            'start_time': time.time(),
            'output_folder': task_output_folder,
            'text': text[:100] + '...' if len(text) > 100 else text,  # 存储截断的文本用于历史记录
            'style': style
        }
        
        # 在会话中保存最近的任务ID
        if 'recent_tasks' not in session:
            session['recent_tasks'] = []
        
        recent_tasks = session['recent_tasks']
        if task_id not in recent_tasks:
            recent_tasks.insert(0, task_id)
        
        # 只保留最近的10个任务
        session['recent_tasks'] = recent_tasks[:10]
        
        # 启动后台处理线程
        threading.Thread(target=process_task, args=(task_id, text, style, voice, use_transitions, add_background_music)).start()
        
        # 返回任务ID
        return jsonify({
            'task_id': task_id,
            'status': 'processing'
        })
        
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 后台处理任务
def process_task(task_id, text, style, voice, use_transitions=True, add_background_music=False):
    try:
        task_output_folder = tasks[task_id]['output_folder']
        
        # 处理文本
        logger.info(f"处理文本，任务ID: {task_id}")
        segments = process_text(text)
        tasks[task_id]['progress'] = 10
        
        # 生成提示词
        logger.info(f"生成提示词，任务ID: {task_id}")
        prompts = generate_prompts(segments, style)
        tasks[task_id]['progress'] = 20
        
        # 生成图像
        logger.info(f"生成图像，任务ID: {task_id}")
        image_paths = generate_images(prompts, task_output_folder)
        tasks[task_id]['progress'] = 60
        
        # 生成音频
        logger.info(f"生成音频，任务ID: {task_id}")
        audio_data = generate_audio(segments, voice, task_output_folder)
        tasks[task_id]['progress'] = 80
        
        # 创建视频
        logger.info(f"创建视频，任务ID: {task_id}")
        if use_transitions:
            video_path = create_video_with_transitions(image_paths, audio_data, segments, task_output_folder, add_background_music)
        else:
            video_path = create_video(image_paths, audio_data, segments, task_output_folder, add_background_music)
        
        if not video_path:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = '视频生成失败'
            return
        
        # 更新任务状态
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['video_url'] = f'/outputs/{task_id}/output.mp4'
        tasks[task_id]['completion_time'] = time.time()
        
    except Exception as e:
        logger.error(f"任务处理失败: {str(e)}")
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)

# API路由 - 获取任务状态
@app.route('/api/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task = tasks[task_id]
    response = {
        'status': task['status'],
        'progress': task['progress']
    }
    
    if task['status'] == 'completed':
        response['video_url'] = task['video_url']
    elif task['status'] == 'failed':
        response['error'] = task.get('error', '未知错误')
    
    return jsonify(response)

# API路由 - 获取历史任务
@app.route('/api/history', methods=['GET'])
def get_history():
    # 获取最近的10个任务
    recent_tasks = []
    for task_id, task in sorted(tasks.items(), key=lambda x: x[1].get('start_time', 0), reverse=True)[:10]:
        recent_tasks.append({
            'task_id': task_id,
            'text': task.get('text', ''),
            'style': task.get('style', ''),
            'status': task.get('status', ''),
            'start_time': task.get('start_time', 0),
            'completion_time': task.get('completion_time', 0) if task.get('status') == 'completed' else 0
        })
    
    return jsonify(recent_tasks)

# API路由 - 获取可用语音
@app.route('/api/voices', methods=['GET'])
def get_voices():
    voices = get_available_voices()
    return jsonify(voices)

# 清理旧任务
def cleanup_tasks():
    # 随机触发清理，避免每次请求都检查
    if random.random() < 0.01:  # 1%的概率触发清理
        current_time = time.time()
        to_remove = []
        
        for task_id, task in tasks.items():
            # 清理超过24小时的任务
            if current_time - task.get('start_time', current_time) > 86400:  # 24小时 = 86400秒
                to_remove.append(task_id)
                # 删除任务输出目录
                task_output_folder = task.get('output_folder')
                if task_output_folder and os.path.exists(task_output_folder):
                    try:
                        shutil.rmtree(task_output_folder)
                    except Exception as e:
                        logger.error(f"删除任务目录失败: {str(e)}")
        
        # 从任务字典中移除
        for task_id in to_remove:
            tasks.pop(task_id, None)

# 生成提示词函数
def generate_prompts(segments, style):
    prompts = []
    for segment in segments:
        # 根据文本内容生成提示词
        # 这里可以接入更复杂的提示词生成逻辑，如使用OpenAI API
        prompt = segment
        prompts.append(prompt)
    return prompts

if __name__ == '__main__':
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
