import type { OrderRequest, OrderResponse, OrderStatusResponse } from "@/types";

const BASE_URL = import.meta.env.VITE_API_URL || "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  createOrder: (data: OrderRequest) =>
    request<OrderResponse>("/api/orders", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getOrderStatus: (orderId: string) =>
    request<OrderStatusResponse>(`/api/orders/${orderId}`),

  getFileUrl: (orderId: string, filename: string) =>
    `${BASE_URL}/api/files/${orderId}/${filename}`,
};
