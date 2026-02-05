const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    articles: [],
    isLoading: true,
    hasMore: false
  },

  onLoad() {
    this.loadArticles();
  },

  onShow() {
    this.loadArticles();
  },

  async loadArticles() {
    try {
      this.setData({ isLoading: true });

      const openId = app.globalData.openId || wx.getStorageSync('openId');

      if (!openId) {
        this.setData({
          articles: [],
          isLoading: false
        });
        return;
      }

      const res = await api.getUserArticles(openId);

      if (res.code === 0) {
        this.setData({
          articles: res.data.articles || [],
          isLoading: false
        });
      } else {
        throw new Error(res.message);
      }
    } catch (error) {
      console.error('加载文章列表失败:', error);
      this.setData({ isLoading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    }
  },

  onArticleTap(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/article/article?articleId=${id}`
    });
  },

  onStartNewStory() {
    wx.navigateTo({
      url: '/pages/chat/chat'
    });
  },

  formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
  }
});
