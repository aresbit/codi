const app = getApp();

Page({
  data: {
    orderId: "",
    price: 0,
    tier: "premium",
    paymentParams: {},
  },

  onLoad(options) {
    this.setData({
      orderId: options.orderId,
      price: parseFloat(options.price),
      tier: options.tier || "premium",
      paymentParams: JSON.parse(decodeURIComponent(options.params || "{}")),
    });
  },

  doPay() {
    const { orderId, price, tier, paymentParams } = this.data;

    wx.showLoading({ title: "拉起支付..." });

    // MVP 测试模式：直接跳结果页
    if (paymentParams.mode === "test") {
      wx.hideLoading();
      this._afterPay();
      return;
    }

    // 正式模式：调起微信支付
    wx.requestPayment({
      timeStamp: paymentParams.timestamp,
      nonceStr: paymentParams.nonce_str,
      package: paymentParams.package,
      signType: paymentParams.sign_type || "RSA",
      paySign: paymentParams.pay_sign,
      success: () => {
        wx.hideLoading();
        this._afterPay();
      },
      fail: (err) => {
        wx.hideLoading();
        if (err.errMsg.includes("cancel")) {
          wx.showToast({ title: "已取消支付", icon: "none" });
        } else {
          wx.showToast({ title: "支付失败，请重试", icon: "none" });
        }
      },
    });
  },

  async _afterPay() {
    // 通知后端开始生成
    wx.navigateTo({
      url: `/pages/result/result?orderId=${this.data.orderId}&tier=${this.data.tier}`,
    });
  },
});
