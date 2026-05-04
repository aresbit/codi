const app = getApp();

Page({
  data: {
    step: 1,
    audience: "",
    occasion: "",
    personalNote: "",
    style: "",
    tier: "premium",

    styles: [
      { key: "pop_ballad", name: "流行情歌" },
      { key: "chinese_style", name: "中国风" },
      { key: "folk", name: "民谣" },
      { key: "mountain_song", name: "山歌" },
      { key: "rock", name: "摇滚" },
      { key: "rap", name: "说唱" },
      { key: "rnb", name: "R&B" },
      { key: "light_music", name: "轻音乐" },
    ],
  },

  onLoad(options) {
    if (options.tier) {
      this.setData({ tier: options.tier });
    }
  },

  selectAudience(e) {
    this.setData({ audience: e.currentTarget.dataset.key });
  },

  selectOccasion(e) {
    this.setData({ occasion: e.currentTarget.dataset.key });
  },

  selectStyle(e) {
    this.setData({ style: e.currentTarget.dataset.key });
  },

  onNoteInput(e) {
    this.setData({ personalNote: e.detail.value });
  },

  nextStep() {
    if (this.data.step < 3) {
      this.setData({ step: this.data.step + 1 });
    }
  },

  prevStep() {
    if (this.data.step > 1) {
      this.setData({ step: this.data.step - 1 });
    }
  },

  async previewAndPay() {
    const { audience, occasion, personalNote, style, tier } = this.data;

    wx.showLoading({ title: "创建订单中..." });

    try {
      // 1. 创建订单
      const resp = await new Promise((resolve, reject) => {
        wx.request({
          url: `${app.globalData.baseUrl}/api/orders`,
          method: "POST",
          header: {
            "Content-Type": "application/json",
            "X-WX-OpenID": app.globalData.userOpenId,
          },
          data: { audience, occasion, personal_note: personalNote, style, tier },
          success: resolve,
          fail: reject,
        });
      });

      if (resp.statusCode !== 200 || !resp.data?.order_id) {
        throw new Error(resp.data?.detail || "创建订单失败");
      }

      const { order_id, price, payment_params } = resp.data;

      wx.hideLoading();

      // 2. 跳转支付页
      wx.navigateTo({
        url: `/pages/pay/pay?orderId=${order_id}&price=${price}&params=${encodeURIComponent(JSON.stringify(payment_params))}`,
      });

    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || "网络错误", icon: "none" });
    }
  },
});
