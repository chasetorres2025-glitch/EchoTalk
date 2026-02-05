const app = getApp();
const BASE_URL = app.globalData.baseUrl;

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
  textToSpeech: (text) => request('/api/tts', 'POST', { text })
};
