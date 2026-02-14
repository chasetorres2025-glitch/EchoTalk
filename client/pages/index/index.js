const app = getApp();

Page({
  data: {
    isLoggedIn: false,
    userInfo: null,
    features: [
      {
        icon: '🎙️',
        title: '语音讲述',
        desc: '语音讲述，自动转写',
        bgColor: 'linear-gradient(135deg, #FFE4B5 0%, #FFB380 100%)'
      },
      {
        icon: '🤖',
        title: 'AI引导',
        desc: '智能对话，挖掘细节',
        bgColor: 'linear-gradient(135deg, #E8F5E9 0%, #88D8B0 100%)'
      },
      {
        icon: '📖',
        title: '生成回忆录',
        desc: '智能整理，生成专属文章',
        bgColor: 'linear-gradient(135deg, #E3F2FD 0%, #90CAF9 100%)'
      }
    ]
  },

  onLoad() {
    this.checkLogin();
  },

  onShow() {
    this.checkLogin();
  },

  checkLogin() {
    const openId = wx.getStorageSync('openId');
    if (openId) {
      this.setData({
        isLoggedIn: true
      });
    }
  },

  async onStartStory() {
    try {
      if (!this.data.isLoggedIn) {
        wx.showLoading({ title: '登录中...' });
        await app.login();
        this.setData({ isLoggedIn: true });
        wx.hideLoading();
      }

      wx.navigateTo({
        url: '/pages/chat/chat'
      });
    } catch (error) {
      wx.hideLoading();
      wx.showToast({
        title: '登录失败，请重试',
        icon: 'none'
      });
      console.error('登录失败:', error);
    }
  },

  onViewArticles() {
    wx.switchTab({
      url: '/pages/my-articles/my-articles'
    });
  }
});
