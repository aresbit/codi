/**
 * SongCraft API 封装
 */

const app = getApp();

function request(method, path, data = {}) {
  return new Promise((resolve, reject) => {
    const header = {
      "Content-Type": "application/json",
      "X-WX-OpenID": app.globalData.userOpenId,
    };

    wx.request({
      url: `${app.globalData.baseUrl}${path}`,
      method,
      header,
      data,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(new Error(res.data?.detail || `HTTP ${res.statusCode}`));
        }
      },
      fail: (err) => reject(err),
    });
  });
}

module.exports = {
  getStyles: () => request("GET", "/api/styles"),
  getOccasions: () => request("GET", "/api/occasions"),
  getAudiences: () => request("GET", "/api/audiences"),
  createOrder: (data) => request("POST", "/api/orders", data),
  getOrderStatus: (orderId) => request("GET", `/api/orders/${orderId}`),
  triggerGenerate: (orderId) => request("POST", `/api/orders/${orderId}/generate`),
};
