const app = getApp();

Page({
  data: {
    isLoggedIn: false,
    userInfo: null
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
