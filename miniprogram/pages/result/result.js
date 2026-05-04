const app = getApp();

Page({
  data: {
    orderId: "",
    tier: "premium",
    status: "generating",    // generating / completed / failed
    lyrics: "",
    videoUrl: "",
    sheetMusicUrl: "",
    errorMsg: "",
    elapsed: 0,
  },

  timer: null,

  onLoad(options) {
    this.setData({
      orderId: options.orderId,
      tier: options.tier || "premium",
    });

    // 触发后端生成
    this._startGeneration();
  },

  onUnload() {
    if (this.timer) clearInterval(this.timer);
  },

  async _startGeneration() {
    const baseUrl = app.globalData.baseUrl;

    // 通知后端开始生成
    wx.request({
      url: `${baseUrl}/api/orders/${this.data.orderId}/generate`,
      method: "POST",
    });

    // 轮询状态
    let elapsed = 0;
    this.timer = setInterval(async () => {
      elapsed += 1;
      this.setData({ elapsed });

      try {
        const resp = await new Promise((resolve) => {
          wx.request({
            url: `${baseUrl}/api/orders/${this.data.orderId}`,
            method: "GET",
            success: resolve,
          });
        });

        if (resp.statusCode === 200 && resp.data) {
          const order = resp.data;
          if (order.status === "completed") {
            clearInterval(this.timer);
            this.setData({
              status: "completed",
              lyrics: order.lyrics || "",
              videoUrl: order.video_url || "",
              sheetMusicUrl: order.sheet_music_url || "",
            });
          } else if (order.status === "failed") {
            clearInterval(this.timer);
            this.setData({
              status: "failed",
              errorMsg: order.error_message || "未知错误",
            });
          }
        }
      } catch (e) {
        // 继续轮询
      }
    }, 2000);
  },

  previewVideo() {
    const baseUrl = app.globalData.baseUrl;
    wx.previewMedia({
      sources: [{ url: `${baseUrl}${this.data.videoUrl}`, type: "video" }],
    });
  },

  downloadVideo() {
    const baseUrl = app.globalData.baseUrl;
    wx.downloadFile({
      url: `${baseUrl}${this.data.videoUrl}`,
      success: (res) => {
        wx.saveVideoToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => wx.showToast({ title: "已保存到相册" }),
          fail: () => wx.showToast({ title: "保存失败", icon: "none" }),
        });
      },
    });
  },

  downloadSheet() {
    const baseUrl = app.globalData.baseUrl;
    wx.downloadFile({
      url: `${baseUrl}${this.data.sheetMusicUrl}`,
      success: (res) => {
        wx.saveImageToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => wx.showToast({ title: "曲谱已保存" }),
          fail: () => wx.showToast({ title: "保存失败", icon: "none" }),
        });
      },
    });
  },

  shareSong() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ["shareAppMessage", "shareTimeline"],
    });
  },

  retry() {
    this.setData({ status: "generating", elapsed: 0, errorMsg: "" });
    this._startGeneration();
  },
});
