/**
 * 小说转漫画视频应用 - 前端交互脚本
 */

// 当文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const generateForm = document.getElementById('generate-form');
    const storyInput = document.getElementById('story-text');
    const charCounter = document.getElementById('char-counter');
    const maxChars = parseInt(storyInput.getAttribute('maxlength') || 2000);
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const resultContainer = document.getElementById('result-container');
    const videoPlayer = document.getElementById('video-player');
    const downloadBtn = document.getElementById('download-btn');
    const newGenerationBtn = document.getElementById('new-generation-btn');
    const submitBtn = document.getElementById('submit-btn');
    const voiceSelect = document.getElementById('voice-select');
    
    // 任务ID和轮询间隔
    let taskId = null;
    let pollInterval = null;
    const POLL_FREQUENCY = 3000; // 3秒
    
    // 初始化字符计数器
    updateCharCounter();
    
    // 监听文本输入，更新字符计数
    storyInput.addEventListener('input', updateCharCounter);
    
    // 监听表单提交
    generateForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitGeneration();
    });
    
    // 监听新建生成按钮
    if (newGenerationBtn) {
        newGenerationBtn.addEventListener('click', resetForm);
    }
    
    // 加载可用的语音列表
    loadVoices();
    
    /**
     * 更新字符计数器
     */
    function updateCharCounter() {
        const currentLength = storyInput.value.length;
        const remaining = maxChars - currentLength;
        
        charCounter.textContent = `${currentLength}/${maxChars} 字符`;
        
        // 根据剩余字符数更新样式
        charCounter.className = 'char-counter';
        if (remaining < maxChars * 0.2) {
            charCounter.classList.add('warning');
        }
        if (remaining < maxChars * 0.1) {
            charCounter.classList.add('danger');
        }
    }
    
    /**
     * 提交生成请求
     */
    function submitGeneration() {
        // 获取表单数据
        const formData = new FormData(generateForm);
        const storyText = formData.get('story_text');
        
        // 验证输入
        if (!storyText || storyText.trim().length < 10) {
            showAlert('请输入至少10个字符的故事文本', 'danger');
            return;
        }
        
        // 禁用提交按钮，显示加载状态
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> 处理中...';
        
        // 显示进度条，初始化为0%
        progressContainer.style.display = 'block';
        updateProgress(0, '正在初始化...');
        
        // 隐藏结果区域
        resultContainer.style.display = 'none';
        
        // 发送API请求
        axios.post('/api/generate', {
            story_text: storyText,
            comic_style: formData.get('comic_style') || 'default',
            voice_name: formData.get('voice_name') || 'zh-CN-XiaoxiaoNeural',
            use_transitions: formData.get('use_transitions') === 'on',
            add_background_music: formData.get('add_background_music') === 'on'
        })
        .then(function(response) {
            // 保存任务ID并开始轮询状态
            taskId = response.data.task_id;
            startPolling();
        })
        .catch(function(error) {
            // 处理错误
            console.error('生成请求失败:', error);
            let errorMessage = '生成请求失败';
            if (error.response && error.response.data && error.response.data.error) {
                errorMessage = error.response.data.error;
            }
            showAlert(errorMessage, 'danger');
            resetSubmitButton();
        });
    }
    
    /**
     * 开始轮询任务状态
     */
    function startPolling() {
        // 清除可能存在的轮询
        if (pollInterval) {
            clearInterval(pollInterval);
        }
        
        // 设置新的轮询
        pollInterval = setInterval(function() {
            checkTaskStatus();
        }, POLL_FREQUENCY);
        
        // 立即检查一次状态
        checkTaskStatus();
    }
    
    /**
     * 检查任务状态
     */
    function checkTaskStatus() {
        if (!taskId) return;
        
        axios.get(`/api/status/${taskId}`)
            .then(function(response) {
                const data = response.data;
                
                // 更新进度
                updateProgress(data.progress, data.status);
                
                // 如果任务完成
                if (data.state === 'completed') {
                    stopPolling();
                    showResult(data.result);
                    resetSubmitButton();
                }
                // 如果任务失败
                else if (data.state === 'failed') {
                    stopPolling();
                    showAlert(`生成失败: ${data.error || '未知错误'}`, 'danger');
                    resetSubmitButton();
                }
            })
            .catch(function(error) {
                console.error('状态检查失败:', error);
                // 如果连续几次检查失败，可以停止轮询
                // 这里简化处理，直接停止
                stopPolling();
                showAlert('无法获取任务状态', 'warning');
                resetSubmitButton();
            });
    }
    
    /**
     * 停止轮询
     */
    function stopPolling() {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }
    
    /**
     * 更新进度条
     */
    function updateProgress(percent, statusText) {
        // 确保百分比在0-100之间
        percent = Math.min(100, Math.max(0, percent));
        
        // 更新进度条
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        
        // 更新状态文本
        if (statusText) {
            progressText.textContent = `${statusText} (${Math.round(percent)}%)`;
        } else {
            progressText.textContent = `${Math.round(percent)}%`;
        }
    }
    
    /**
     * 显示结果
     */
    function showResult(result) {
        if (!result || !result.video_url) {
            showAlert('生成结果无效', 'danger');
            return;
        }
        
        // 显示结果容器
        resultContainer.style.display = 'block';
        resultContainer.classList.add('fade-in');
        
        // 设置视频播放器
        videoPlayer.src = result.video_url;
        videoPlayer.poster = result.thumbnail_url || '';
        videoPlayer.load();
        
        // 设置下载链接
        if (downloadBtn) {
            downloadBtn.href = result.video_url;
            downloadBtn.download = result.filename || 'comic-video.mp4';
        }
        
        // 滚动到结果区域
        resultContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * 重置表单
     */
    function resetForm() {
        // 停止任何正在进行的轮询
        stopPolling();
        
        // 重置表单
        generateForm.reset();
        
        // 更新字符计数
        updateCharCounter();
        
        // 重置提交按钮
        resetSubmitButton();
        
        // 隐藏进度和结果
        progressContainer.style.display = 'none';
        resultContainer.style.display = 'none';
        
        // 滚动到表单顶部
        generateForm.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * 重置提交按钮状态
     */
    function resetSubmitButton() {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '生成漫画视频';
    }
    
    /**
     * 显示警告/提示消息
     */
    function showAlert(message, type = 'info') {
        // 创建警告元素
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
        `;
        
        // 查找警告容器
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            // 添加到容器
            alertContainer.appendChild(alertDiv);
            
            // 5秒后自动关闭
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }, 5000);
        } else {
            // 如果没有容器，使用控制台
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    /**
     * 加载可用的语音列表
     */
    function loadVoices() {
        // 如果没有语音选择器，直接返回
        if (!voiceSelect) return;
        
        // 显示加载中
        voiceSelect.innerHTML = '<option value="">加载中...</option>';
        
        // 请求语音列表
        axios.get('/api/voices')
            .then(function(response) {
                const voices = response.data.voices || [];
                
                // 如果没有语音，显示提示
                if (voices.length === 0) {
                    voiceSelect.innerHTML = '<option value="">无可用语音</option>';
                    return;
                }
                
                // 清空选择器
                voiceSelect.innerHTML = '';
                
                // 添加语音选项
                voices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.name;
                    option.textContent = `${voice.display_name} (${voice.locale})`;
                    // 如果是默认语音，设为选中
                    if (voice.name === 'zh-CN-XiaoxiaoNeural') {
                        option.selected = true;
                    }
                    voiceSelect.appendChild(option);
                });
            })
            .catch(function(error) {
                console.error('获取语音列表失败:', error);
                voiceSelect.innerHTML = '<option value="zh-CN-XiaoxiaoNeural">小小 (中文)</option>';
            });
    }
});
