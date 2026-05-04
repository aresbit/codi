App({
  globalData: {
    baseUrl: "https://your-domain.com", // 替换为你的后端地址
    userOpenId: "",
  },

  onLaunch() {
    // 获取微信登录 code → 后端换取 openid
    wx.login({
      success: (res) => {
        if (res.code) {
          wx.request({
            url: `${this.globalData.baseUrl}/api/auth/openid`,
            method: "POST",
            data: { code: res.code },
            success: (resp) => {
              if (resp.data?.openid) {
                this.globalData.userOpenId = resp.data.openid;
              }
            },
          });
        }
      },
    });
  },
});
