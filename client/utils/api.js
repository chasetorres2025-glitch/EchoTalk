const app = getApp();
const BASE_URL = app.globalData.baseUrl;
const WS_URL = app.globalData.wsUrl || BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://');

const request = (url, method = 'GET', data = {}) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json'
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          reject(res);
        }
      },
      fail: reject
    });
  });
};

const createWebSocket = (options) => {
  const {
    onConnect,
    onMessage,
    onError,
    onClose,
    onUserSpeech,
    onAIResponse,
    onAIAudio,
    onAIAudioComplete,
    onSessionStarted,
    onSessionStopped,
    onInterruptAck
  } = options;
  
  let socketTask = null;
  let isConnected = false;
  
  const connect = (sessionId, openId) => {
    return new Promise((resolve, reject) => {
      const wsUrl = `${WS_URL}/ws/realtime/${sessionId}/${openId}`;
      console.log('[WS] 连接地址:', wsUrl);
      
      socketTask = wx.connectSocket({
        url: wsUrl,
        success: () => {
          console.log('[WS] 连接中...');
        },
        fail: (err) => {
          console.error('[WS] 连接失败:', err);
          socketTask = null;
          isConnected = false;
          reject(err);
        }
      });
      
      if (!socketTask) {
        reject(new Error('创建WebSocket失败'));
        return;
      }
      
      socketTask.onOpen(() => {
        console.log('[WS] 连接已打开');
        isConnected = true;
        if (onConnect) onConnect();
        resolve();
      });
      
      socketTask.onMessage((res) => {
        console.log('[WS] 收到消息:', res.data);
        const data = res.data;
        if (onMessage) onMessage(data);
        
        try {
          const msg = JSON.parse(data);
          const msgType = msg.type;
          
          switch (msgType) {
            case 'session_started':
              console.log('[WS] 会话已开始');
              if (onSessionStarted) onSessionStarted(msg);
              break;
            case 'user_speech':
              console.log('[WS] 用户说话:', msg.text);
              if (onUserSpeech) onUserSpeech(msg);
              break;
            case 'ai_response':
              console.log('[WS] AI回复:', msg.text);
              if (onAIResponse) onAIResponse(msg);
              break;
            case 'ai_audio':
              if (onAIAudio) onAIAudio(msg);
              break;
            case 'ai_audio_complete':
              console.log('[WS] AI音频完成');
              if (onAIAudioComplete) onAIAudioComplete(msg);
              break;
            case 'session_stopped':
              console.log('[WS] 会话已停止');
              if (onSessionStopped) onSessionStopped(msg);
              break;
            case 'interrupt_ack':
              console.log('[WS] 打断确认');
              if (onInterruptAck) onInterruptAck(msg);
              break;
            case 'error':
              console.error('[WS] 服务器错误:', msg.message);
              if (onError) onError(msg);
              break;
          }
        } catch (e) {
          console.log('[WS] 解析消息失败:', e);
        }
      });
      
      socketTask.onError((err) => {
        console.error('[WS] 错误:', err);
        isConnected = false;
        socketTask = null;
        if (onError) onError(err);
        reject(err);
      });
      
      socketTask.onClose(() => {
        console.log('[WS] 连接已关闭');
        isConnected = false;
        socketTask = null;
        if (onClose) onClose();
      });
    });
  };
  
  const send = (data) => {
    if (!isConnected || !socketTask) {
      return false;
    }
    socketTask.send({
      data: JSON.stringify(data),
      success: () => {
        console.log(`[WS] 发送消息: ${data.type}`);
      },
      fail: (err) => {
        console.error(`[WS] 发送失败:`, err);
      }
    });
    return true;
  };
  
  const sendAudioFrame = (audioBase64) => {
    send({ type: 'audio_frame', audio: audioBase64 });
  };
  
  const stopSession = () => {
    send({ type: 'stop_session' });
  };
  
  const sendInterrupt = () => {
    send({ type: 'user_interrupt' });
  };
  
  const close = () => {
    if (socketTask) {
      const task = socketTask;
      socketTask = null;
      isConnected = false;
      try {
        task.close();
      } catch (e) {
        console.log('[WS] 关闭连接时出错:', e);
      }
    }
  };
  
  return {
    connect,
    sendAudioFrame,
    stopSession,
    sendInterrupt,
    close,
    isConnected: () => isConnected
  };
};

module.exports = {
  // 认证相关
  login: (code) => request('/api/auth/login', 'POST', { code }),

  // 会话相关
  createSession: (openId) => request('/api/session/create', 'POST', { open_id: openId }),
  getSession: (sessionId) => request(`/api/session/${sessionId}`),
  endSession: (sessionId) => request(`/api/session/${sessionId}/end`, 'POST'),

  // 聊天相关
  sendMessage: (data) => request('/api/chat/message', 'POST', data),
  getChatHistory: (sessionId) => request(`/api/chat/history/${sessionId}`),

  // 语音相关
  uploadVoice: (filePath, data) => {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${BASE_URL}/api/voice/upload`,
        filePath,
        name: 'voice',
        formData: data,
        success: (res) => {
          resolve(JSON.parse(res.data));
        },
        fail: reject
      });
    });
  },

  // 文章相关
  generateArticle: (sessionId) => request('/api/article/generate', 'POST', { session_id: sessionId }),
  getArticle: (articleId) => request(`/api/article/${articleId}`),
  updateArticle: (articleId, content) => request(`/api/article/${articleId}`, 'PUT', { content }),
  saveArticle: (articleId) => request(`/api/article/${articleId}/save`, 'POST'),
  getUserArticles: (openId) => request(`/api/article/user/${openId}`),

  // 语音合成
  textToSpeech: (text) => request('/api/voice/tts', 'POST', { text }),
  
  // WebSocket 实时对话
  createWebSocket
};