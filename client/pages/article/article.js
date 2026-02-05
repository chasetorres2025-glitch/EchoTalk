const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    sessionId: null,
    articleId: null,
    article: null,
    isLoading: true,
    isPlaying: false,
    isEditing: false,
    editContent: ''
  },

  innerAudioContext: null,

  async onLoad(options) {
    this.initAudioPlayer();

    if (options.sessionId) {
      this.setData({ sessionId: options.sessionId });
      await this.generateArticle(options.sessionId);
    } else if (options.articleId) {
      this.setData({ articleId: options.articleId });
      await this.loadArticle(options.articleId);
    }
  },

  onUnload() {
    if (this.innerAudioContext) {
      this.innerAudioContext.stop();
      this.innerAudioContext.destroy();
    }
  },

  initAudioPlayer() {
    this.innerAudioContext = wx.createInnerAudioContext();

    this.innerAudioContext.onPlay(() => {
      this.setData({ isPlaying: true });
    });

    this.innerAudioContext.onStop(() => {
      this.setData({ isPlaying: false });
    });

    this.innerAudioContext.onEnded(() => {
      this.setData({ isPlaying: false });
    });

    this.innerAudioContext.onError((err) => {
      console.error('播放错误:', err);
      this.setData({ isPlaying: false });
      wx.showToast({
        title: '播放失败',
        icon: 'none'
      });
    });
  },

  async generateArticle(sessionId) {
    try {
      wx.showLoading({ title: '生成中...' });

      const res = await api.generateArticle(sessionId);

      wx.hideLoading();

      if (res.code === 0) {
        this.setData({
          articleId: res.data.article_id,
          article: res.data.article,
          editContent: res.data.article.content,
          isLoading: false
        });

        // 自动朗读
        this.playArticle();
      } else {
        throw new Error(res.message);
      }
    } catch (error) {
      wx.hideLoading();
      console.error('生成文章失败:', error);
      wx.showToast({
        title: '生成失败，请重试',
        icon: 'none'
      });
      this.setData({ isLoading: false });
    }
  },

  async loadArticle(articleId) {
    try {
      const res = await api.getArticle(articleId);

      if (res.code === 0) {
        this.setData({
          article: res.data,
          editContent: res.data.content,
          isLoading: false
        });
      } else {
        throw new Error(res.message);
      }
    } catch (error) {
      console.error('加载文章失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
      this.setData({ isLoading: false });
    }
  },

  playArticle() {
    if (!this.data.article) return;

    if (this.data.isPlaying) {
      this.innerAudioContext.stop();
      this.setData({ isPlaying: false });
    } else {
      api.textToSpeech(this.data.article.content).then(res => {
        if (res.code === 0 && res.data.audio_url) {
          this.innerAudioContext.src = res.data.audio_url;
          this.innerAudioContext.play();
        } else {
          wx.showToast({
            title: '语音合成失败',
            icon: 'none'
          });
        }
      }).catch(err => {
        console.error('语音合成失败:', err);
        wx.showToast({
          title: '语音合成失败',
          icon: 'none'
        });
      });
    }
  },

  onEdit() {
    this.setData({ isEditing: true });
  },

  onCancelEdit() {
    this.setData({
      isEditing: false,
      editContent: this.data.article.content
    });
  },

  onContentInput(e) {
    this.setData({ editContent: e.detail.value });
  },

  async onSaveEdit() {
    if (!this.data.editContent.trim()) {
      wx.showToast({
        title: '内容不能为空',
        icon: 'none'
      });
      return;
    }

    try {
      wx.showLoading({ title: '保存中...' });

      const res = await api.updateArticle(
        this.data.articleId,
        this.data.editContent
      );

      wx.hideLoading();

      if (res.code === 0) {
        this.setData({
          isEditing: false,
          article: { ...this.data.article, content: this.data.editContent }
        });
        wx.showToast({
          title: '保存成功',
          icon: 'success'
        });
      } else {
        throw new Error(res.message);
      }
    } catch (error) {
      wx.hideLoading();
      console.error('保存失败:', error);
      wx.showToast({
        title: '保存失败',
        icon: 'none'
      });
    }
  },

  async onSaveArticle() {
    try {
      wx.showLoading({ title: '保存中...' });

      const res = await api.saveArticle(this.data.articleId);

      wx.hideLoading();

      if (res.code === 0) {
        wx.showToast({
          title: '保存成功',
          icon: 'success'
        });

        setTimeout(() => {
          wx.switchTab({
            url: '/pages/my-articles/my-articles'
          });
        }, 1500);
      } else {
        throw new Error(res.message);
      }
    } catch (error) {
      wx.hideLoading();
      console.error('保存失败:', error);
      wx.showToast({
        title: '保存失败',
        icon: 'none'
      });
    }
  },

  onBackToChat() {
    wx.navigateBack();
  }
});
