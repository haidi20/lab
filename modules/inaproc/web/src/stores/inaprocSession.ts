import { defineStore } from "pinia";
import { api, userMessage } from "../api";

export const useInaprocSessionStore = defineStore("inaprocSession", {
  state: () => ({
    configured: false,
    loading: false,
    connecting: false,
    disconnecting: false,
    error: "" as string,
  }),
  actions: {
    async load() {
      this.loading = true;
      this.error = "";
      try {
        const status = await api.session();
        this.configured = status.configured;
      } catch (error) {
        this.error = userMessage(error);
      } finally {
        this.loading = false;
      }
    },
    async connect(email: string, password: string) {
      this.connecting = true;
      this.error = "";
      try {
        const result = await api.login(email, password);
        this.configured = result.configured;
        return result;
      } catch (error) {
        this.error = userMessage(error);
        throw error;
      } finally {
        this.connecting = false;
      }
    },
    async disconnect() {
      this.disconnecting = true;
      this.error = "";
      try {
        await api.logout();
        this.configured = false;
      } catch (error) {
        this.error = userMessage(error);
      } finally {
        this.disconnecting = false;
      }
    },
  },
});
