const app = getApp();

Page({
  data: {
    selectedTier: "premium",
    styles: [
      { key: "chinese_style", name: "中国风" },
      { key: "pop_ballad", name: "流行情歌" },
      { key: "mountain_song", name: "山歌" },
      { key: "folk", name: "民谣" },
      { key: "rock", name: "摇滚" },
      { key: "rap", name: "说唱" },
      { key: "rnb", name: "R&B" },
      { key: "light_music", name: "轻音乐" },
    ],
  },

  selectTier(e) {
    this.setData({ selectedTier: e.currentTarget.dataset.tier });
  },

  goCreate() {
    wx.navigateTo({
      url: `/pages/create/create?tier=${this.data.selectedTier}`,
    });
  },
});
