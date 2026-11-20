<script setup lang="ts">
import { reactive } from "vue";
import { useInaprocSessionStore } from "../stores/inaprocSession";

const session = useInaprocSessionStore();
const form = reactive({ email: "", password: "" });

async function submit() {
  try {
    await session.connect(form.email, form.password);
    form.password = "";
  } catch {
    // The store exposes the API message in its error state.
  }
}
</script>

<template>
  <form class="row g-2 align-items-end" @submit.prevent="submit">
    <div class="col-12 col-md-4">
      <label class="form-label small fw-semibold" for="inaproc-email">Email INAPROC</label>
      <input
        id="inaproc-email"
        v-model="form.email"
        type="email"
        class="form-control"
        autocomplete="username"
        required
      />
    </div>
    <div class="col-12 col-md-4">
      <label class="form-label small fw-semibold" for="inaproc-password">Password INAPROC</label>
      <input
        id="inaproc-password"
        v-model="form.password"
        type="password"
        class="form-control"
        autocomplete="current-password"
        required
      />
    </div>
    <div class="col-12 col-md-4 d-flex gap-2">
      <button class="btn btn-success flex-grow-1" type="submit" :disabled="session.connecting">
        <span v-if="session.connecting" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
        <i v-else class="bi bi-box-arrow-in-right me-2"></i>
        {{ session.connecting ? "Menghubungkan..." : "Hubungkan Sesi" }}
      </button>
    </div>
    <p v-if="session.error" class="col-12 text-danger small mb-0">{{ session.error }}</p>
  </form>
</template>
