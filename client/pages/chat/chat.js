const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    sessionId: null,
    messages: [],
    isRecording: false,
    isAIThinking: false,
    statusText: '点击按钮开始讲述您的故事',
    recordingTime: 0,
    scrollToMessage: ''
  },

  recorderManager: null,
  innerAudioContext: null,
  recordingTimer: null,

  async onLoad() {
    this.initRecorder();
    this.initAudioPlayer();
    await this.createSession();
  },

  onUnload() {
    if (this.data.sessionId) {
      api.endSession(this.data.sessionId);
    }
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
    }
  },

  initRecorder() {
    this.recorderManager = wx.getRecorderManager();

    this.recorderManager.onStart(() => {
      this.setData({ isRecording: true });
      this.startRecordingTimer();
    });

    this.recorderManager.onStop((res) => {
      this.setData({ isRecording: false });
      this.stopRecordingTimer();
      this.uploadVoice(res.tempFilePath);
    });

    this.recorderManager.onError((err) => {
      console.error('录音错误:', err);
      wx.showToast({
        title: '录音失败，请重试',
        icon: 'none'
      });
      this.setData({ isRecording: false });
    });
  },

  initAudioPlayer() {
    this.innerAudioContext = wx.createInnerAudioContext();
    this.innerAudioContext.onError((err) => {
      console.error('播放错误:', err);
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
          statusText: 'AI已准备好，请开始讲述您的故事'
        });

        // 添加AI欢迎消息
        const welcomeMessage = {
          id: Date.now(),
          role: 'ai',
          content: '您好！我是您的AI回忆录助手。请跟我分享您的人生故事，我会帮您记录下来。您可以讲述任何您想回忆的往事。',
          timestamp: new Date().toISOString()
        };
        this.addMessage(welcomeMessage);

        // 播放欢迎语音
        this.playAIText(welcomeMessage.content);
      }
    } catch (error) {
      console.error('创建会话失败:', error);
      wx.showToast({
        title: '连接失败，请重试',
        icon: 'none'
      });
    }
  },

  onTouchStart() {
    this.startRecording();
  },

  onTouchEnd() {
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
        // 添加用户消息
        const userMessage = {
          id: Date.now(),
          role: 'user',
          content: res.data.text,
          timestamp: new Date().toISOString()
        };
        this.addMessage(userMessage);

        // 获取AI回复
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

  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
});
