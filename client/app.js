App({
  globalData: {
    userInfo: null,
    openId: null,
    // 开发环境使用本地地址
    // baseUrl: 'http://localhost:5050'
    // 生产环境（部署后修改为服务器地址）
    // 示例: 'https://your-domain.com' 或 'http://你的服务器IP'
    baseUrl: 'http://127.0.0.1:5050'
  },

  onLaunch() {
    this.checkLoginStatus();
  },

  checkLoginStatus() {
    const openId = wx.getStorageSync('openId');
    if (openId) {
      this.globalData.openId = openId;
    }
  },

  login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
            wx.request({
              url: `${this.globalData.baseUrl}/api/auth/login`,
              method: 'POST',
              data: {
                code: res.code
              },
              success: (response) => {
                if (response.data.code === 0) {
                  const { openId, userInfo } = response.data.data;
                  this.globalData.openId = openId;
                  this.globalData.userInfo = userInfo;
                  wx.setStorageSync('openId', openId);
                  resolve(response.data);
                } else {
                  reject(response.data);
                }
              },
              fail: reject
            });
          } else {
            reject(res);
          }
        },
        fail: reject
      });
    });
  }
});
