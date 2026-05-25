import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
let accessToken = null;

export const apiClient = axios.create({ baseURL });

export function setAccessToken(token) {
  accessToken = token;
}

apiClient.interceptors.request.use((config) => {
  const nextConfig = { ...config };
  if (accessToken) {
    nextConfig.headers = {
      ...(nextConfig.headers || {}),
      Authorization: `Bearer ${accessToken}`,
    };
  }
  return nextConfig;
});
