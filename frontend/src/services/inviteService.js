import { apiClient } from "./api";

export const inviteService = {
  async accept(token) {
    const response = await apiClient.get("/invites/accept", { params: { token } });
    return response.data;
  },
};
