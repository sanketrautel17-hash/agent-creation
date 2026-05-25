import { apiClient } from "./api";

export const authService = {
  async sendOtp(payload) {
    const response = await apiClient.post("/auth/send-otp", payload);
    return response.data;
  },
  async verifyOtp(payload) {
    const response = await apiClient.post("/auth/verify-otp", payload);
    return response.data;
  },
  async me() {
    const response = await apiClient.get("/auth/me");
    return response.data;
  },
  async adminLogin(payload) {
    const response = await apiClient.post("/auth/admin-login", payload);
    return response.data;
  },
};
