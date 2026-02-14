const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    sessionId: null,
    messages: [],
    isRecording: false,
    isAIThinking: false,
    isAISpeaking: false,
    statusText: '正在初始化...',
    recordingTime: 0,
    scrollToMessage: '',
    mode: 'push',
    isListening: false,
    volumeLevel: 0,
    audioBuffer: [],
    currentTranscript: ''
  },

  recorderManager: null,
  innerAudioContext: null,
  recordingTimer: null,
  wsClient: null,
  audioQueue: [],
  isPlayingAudio: false,
  frameBuffer: [],
  lastSendTime: 0,

  async onLoad() {
    this.initRecorder();
    this.initAudioPlayer();
    await this.createSession();
  },

  onUnload() {
    this.stopRealtimeSession();
    if (this.data.sessionId) {
      api.endSession(this.data.sessionId);
    }
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
    }
    if (this.innerAudioContext) {
      this.innerAudioContext.destroy();
    }
  },

  initRecorder() {
    this.recorderManager = wx.getRecorderManager();

    this.recorderManager.onStart(() => {
      this.setData({ isRecording: true, isListening: true });
      this.startRecordingTimer();
    });

    this.recorderManager.onStop((res) => {
      this.setData({ isRecording: false, isListening: false });
      this.stopRecordingTimer();
      if (this.data.mode === 'push') {
        this.uploadVoice(res.tempFilePath);
      }
    });

    this.recorderManager.onFrameRecorded((res) => {
      const { frameBuffer } = res;
      console.log('[Chat] 收到音频帧, 大小:', frameBuffer.byteLength);
      this.handleAudioFrame(frameBuffer);
    });

    this.recorderManager.onError((err) => {
      console.error('录音错误:', err);
      wx.showToast({
        title: '录音失败，请重试',
        icon: 'none'
      });
      this.setData({ isRecording: false, isListening: false });
    });
  },

  initAudioPlayer() {
    this.innerAudioContext = wx.createInnerAudioContext();
    this.innerAudioContext.onPlay(() => {
      this.setData({ isAISpeaking: true });
    });
    this.innerAudioContext.onEnded(() => {
      this.setData({ isAISpeaking: false });
      this.playNextInQueue();
    });
    this.innerAudioContext.onStop(() => {
      this.setData({ isAISpeaking: false });
    });
    this.innerAudioContext.onError((err) => {
      console.error('播放错误:', err);
      this.setData({ isAISpeaking: false });
    });
  },

  startRecordingTimer() {
    let seconds = 0;
    this.recordingTimer = setInterval(() => {
      seconds++;
      this.setData({ recordingTime: seconds });
    }, 1000);
  },

  stopRecordingTimer() {
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
      this.recordingTimer = null;
    }
    this.setData({ recordingTime: 0 });
  },

  async createSession() {
    try {
      const openId = app.globalData.openId;
      const res = await api.createSession(openId);
      if (res.code === 0) {
        this.setData({
          sessionId: res.data.session_id,
          statusText: '按住按钮开始讲述'
        });

        const welcomeMessage = {
          id: Date.now(),
          role: 'ai',
          content: '您好！我是您的AI回忆录助手。请按住下方的麦克风按钮，开始讲述您的故事。',
          timestamp: new Date().toISOString()
        };
        this.addMessage(welcomeMessage);
      }
    } catch (error) {
      console.error('创建会话失败:', error);
      wx.showToast({
        title: '连接失败，请重试',
        icon: 'none'
      });
    }
  },

  async initWebSocket() {
    const openId = app.globalData.openId;
    
    this.wsClient = api.createWebSocket({
      onConnect: () => {
        console.log('[Chat] WebSocket已连接');
        this.setData({ statusText: '已连接，请开始讲述' });
      },
      
      onUserSpeech: (data) => {
        console.log('[Chat] 用户说话:', data.text);
        if (data.text && data.text.trim()) {
          const userMessage = {
            id: Date.now(),
            role: 'user',
            content: data.text,
            timestamp: new Date().toISOString()
          };
          this.addMessage(userMessage);
          this.setData({ currentTranscript: '' });
        }
      },
      
      onAIResponse: (data) => {
        console.log('[Chat] AI回复:', data.text);
        if (data.text) {
          const aiMessage = {
            id: Date.now() + 1,
            role: 'ai',
            content: data.text,
            timestamp: new Date().toISOString()
          };
          this.addMessage(aiMessage);
          this.setData({ statusText: 'AI正在回复...', isAIThinking: false });
        }
      },
      
      onAIAudio: (data) => {
        if (data.audio) {
          this.queueAudio(data.audio);
        }
      },
      
      onAIAudioComplete: (data) => {
        console.log('[Chat] AI音频完成');
        this.setData({ statusText: '请继续讲述' });
      },
      
      onSessionStarted: (data) => {
        console.log('[Chat] 实时会话已开始');
        this.setData({ statusText: '实时对话已开始，请讲述您的故事' });
        console.log('[Chat] 准备启动录音...');
        this.startRealtimeRecording();
        console.log('[Chat] 录音启动命令已发送');
      },
      
      onSessionStopped: (data) => {
        console.log('[Chat] 实时会话已停止');
        this.setData({ statusText: '对话已结束', isListening: false });
      },
      
      onInterruptAck: (data) => {
        console.log('[Chat] 打断确认');
        this.stopAudioPlayback();
      },
      
      onError: (err) => {
        console.error('[Chat] WebSocket错误:', err);
        this.setData({ statusText: 'WebSocket连接失败，已切换到按住说话模式' });
        this.fallbackToPushMode();
      },
      
      onClose: () => {
        console.log('[Chat] WebSocket已关闭');
        this.setData({ isListening: false });
      }
    });

    try {
      await this.wsClient.connect(this.data.sessionId, openId);
    } catch (err) {
      console.error('[Chat] WebSocket连接失败:', err);
      this.setData({ statusText: 'WebSocket连接失败，已切换到按住说话模式' });
      this.fallbackToPushMode();
    }
  },

  fallbackToPushMode() {
    this.setData({ 
      mode: 'push', 
      statusText: '按住按钮开始讲述',
      isListening: false 
    });
    if (this.wsClient) {
      const client = this.wsClient;
      this.wsClient = null;
      try {
        client.stopSession();
        client.close();
      } catch (e) {
        console.log('[Chat] 关闭WebSocket时出错:', e);
      }
    }
  },

  handleAudioFrame(frameBuffer) {
    if (!this.wsClient || !this.wsClient.isConnected()) {
      return;
    }

    const now = Date.now();
    this.frameBuffer.push(frameBuffer);
    
    if (now - this.lastSendTime >= 100) {
      this.sendBufferedFrames();
      this.lastSendTime = now;
    }

    const volume = this.calculateVolume(frameBuffer);
    this.setData({ volumeLevel: volume });

    if (volume > 30 && this.data.isAISpeaking) {
      this.interruptAI();
    }
  },

  sendBufferedFrames() {
    if (this.frameBuffer.length === 0) return;

    const totalLength = this.frameBuffer.reduce((sum, buf) => sum + buf.byteLength, 0);
    const combined = new ArrayBuffer(totalLength);
    const view = new Uint8Array(combined);
    
    let offset = 0;
    for (const buf of this.frameBuffer) {
      const bufView = new Uint8Array(buf);
      view.set(bufView, offset);
      offset += buf.byteLength;
    }
    
    const base64 = this.arrayBufferToBase64(combined);
    console.log('[Chat] 发送音频帧, base64长度:', base64.length);
    this.wsClient.sendAudioFrame(base64);
    
    this.frameBuffer = [];
  },

  arrayBufferToBase64(buffer) {
    return wx.arrayBufferToBase64(buffer);
  },

  calculateVolume(frameBuffer) {
    const data = new Int16Array(frameBuffer);
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      sum += Math.abs(data[i]);
    }
    return Math.floor(sum / data.length / 327.68);
  },

  interruptAI() {
    console.log('[Chat] 用户打断AI');
    if (this.wsClient) {
      this.wsClient.sendInterrupt();
    }
    this.stopAudioPlayback();
  },

  stopAudioPlayback() {
    if (this.innerAudioContext) {
      this.innerAudioContext.stop();
    }
    this.audioQueue = [];
    this.isPlayingAudio = false;
    this.setData({ isAISpeaking: false });
  },

  queueAudio(audioBase64) {
    this.audioQueue.push(audioBase64);
    if (!this.isPlayingAudio) {
      this.playNextInQueue();
    }
  },

  playNextInQueue() {
    if (this.audioQueue.length === 0) {
      this.isPlayingAudio = false;
      this.setData({ isAISpeaking: false });
      return;
    }

    this.isPlayingAudio = true;
    const audioBase64 = this.audioQueue.shift();
    
    const fs = wx.getFileSystemManager();
    const tempPath = `${wx.env.USER_DATA_PATH}/ai_audio_${Date.now()}.mp3`;
    
    try {
      const audioData = wx.base64Decode(audioBase64);
      fs.writeFileSync(tempPath, audioData, 'binary');
      
      this.innerAudioContext.src = tempPath;
      this.innerAudioContext.play();
    } catch (err) {
      console.error('[Chat] 播放音频失败:', err);
      this.playNextInQueue();
    }
  },

  startRealtimeRecording() {
    console.log('[Chat] startRealtimeRecording 被调用');
    const options = {
      duration: 600000,
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 48000,
      format: 'pcm',
      frameSize: 5
    };
    
    console.log('[Chat] 录音配置:', options);
    this.recorderManager.start(options);
    console.log('[Chat] recorderManager.start() 已调用');
    this.setData({ statusText: '正在聆听...' });
  },

  stopRealtimeSession() {
    if (this.recorderManager && this.data.isRecording) {
      this.recorderManager.stop();
    }
    
    if (this.wsClient) {
      const client = this.wsClient;
      this.wsClient = null;
      try {
        client.stopSession();
        client.close();
      } catch (e) {
        console.log('[Chat] 停止实时会话时出错:', e);
      }
    }
    
    this.stopAudioPlayback();
  },

  onTouchStart() {
    if (this.data.mode === 'realtime') {
      return;
    }
    this.startRecording();
  },

  onTouchEnd() {
    if (this.data.mode === 'realtime') {
      return;
    }
    this.stopRecording();
  },

  startRecording() {
    const options = {
      duration: 60000,
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 48000,
      format: 'mp3'
    };
    this.recorderManager.start(options);
  },

  stopRecording() {
    this.recorderManager.stop();
  },

  async uploadVoice(filePath) {
    try {
      this.setData({ isAIThinking: true, statusText: '正在识别...' });

      const res = await api.uploadVoice(filePath, {
        session_id: this.data.sessionId,
        open_id: app.globalData.openId
      });

      if (res.code === 0) {
        const userMessage = {
          id: Date.now(),
          role: 'user',
          content: res.data.text,
          timestamp: new Date().toISOString()
        };
        this.addMessage(userMessage);

        await this.getAIResponse(res.data.text);
      } else {
        wx.showToast({
          title: res.message || '识别失败',
          icon: 'none'
        });
      }
    } catch (error) {
      console.error('上传语音失败:', error);
      wx.showToast({
        title: '上传失败，请重试',
        icon: 'none'
      });
    } finally {
      this.setData({ isAIThinking: false });
    }
  },

  async getAIResponse(userText) {
    try {
      this.setData({ statusText: 'AI思考中...' });

      const res = await api.sendMessage({
        session_id: this.data.sessionId,
        open_id: app.globalData.openId,
        message: userText
      });

      if (res.code === 0 && res.data.ai_response) {
        const aiMessage = {
          id: Date.now() + 1,
          role: 'ai',
          content: res.data.ai_response,
          timestamp: new Date().toISOString()
        };
        this.addMessage(aiMessage);
        this.playAIText(aiMessage.content);
      }

      this.setData({ statusText: '请继续讲述，或点击完成' });
    } catch (error) {
      console.error('获取AI回复失败:', error);
      this.setData({ statusText: '请继续讲述' });
    }
  },

  addMessage(message) {
    const messages = [...this.data.messages, message];
    this.setData({
      messages,
      scrollToMessage: `msg-${message.id}`
    });
  },

  playAIText(text) {
    api.textToSpeech(text).then(res => {
      if (res.code === 0 && res.data.audio_url) {
        this.innerAudioContext.src = res.data.audio_url;
        this.innerAudioContext.play();
      }
    }).catch(err => {
      console.error('语音合成失败:', err);
    });
  },

  onGenerateArticle() {
    if (this.data.messages.length < 2) {
      wx.showToast({
        title: '请多讲述一些内容',
        icon: 'none'
      });
      return;
    }

    wx.showModal({
      title: '生成回忆录',
      content: '确定要基于当前对话生成回忆录吗？',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({
            url: `/pages/article/article?sessionId=${this.data.sessionId}`
          });
        }
      }
    });
  },

  toggleMode() {
    const newMode = this.data.mode === 'realtime' ? 'push' : 'realtime';
    
    if (newMode === 'push') {
      this.stopRealtimeSession();
      this.setData({ 
        mode: newMode, 
        statusText: '按住按钮开始讲述',
        isListening: false 
      });
    } else {
      this.setData({ 
        mode: newMode, 
        statusText: '正在连接实时对话服务...' 
      });
      this.initWebSocket();
    }
  },

  onSwitchToRealtime() {
    if (this.data.mode === 'realtime') return;
    this.setData({ 
      mode: 'realtime', 
      statusText: '正在连接实时对话服务...' 
    });
    this.initWebSocket();
  },

  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
});
