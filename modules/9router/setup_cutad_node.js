/* Setup node provider cutad di 9Router lokal (port 20128).
 * Idempoten: bila node prefix `cd` sudah ada, pakai yang ada.
 * Pakai: node setup_9router_cutad.js  (dengan CUTAD_API_KEY di environment)
 */
const api = require("/opt/homebrew/lib/node_modules/9router/src/cli/api/client.js");

(async () => {
  const API_KEY = process.env.CUTAD_API_KEY;
  if (!API_KEY) {
    console.error("CUTAD_API_KEY tidak ada di environment");
    process.exit(1);
  }

  // 1. Cari node cutad yang sudah ada (prefix cd)
  const existing = await api.getProviderNodes();
  const nodes = existing?.data?.nodes || [];
  let node = nodes.find((n) => n.prefix === "cd" && n.name === "cutad");

  if (node) {
    console.log("node sudah ada:", node.id, "apiType:", node.apiType);
    if (node.apiType !== "chat") {
      const upd = await api.updateProviderNode(node.id, {
        name: "cutad",
        prefix: "cd",
        apiType: "chat",
        baseUrl: "https://ai.cutad.web.id/v1",
      });
      console.log("update apiType->chat:", JSON.stringify(upd).slice(0, 200));
    }
  } else {
    const buat = await api.createProviderNode({
      name: "cutad",
      prefix: "cd",
      apiType: "chat",
      baseUrl: "https://ai.cutad.web.id/v1",
      type: "openai-compatible",
    });
    node = buat && buat.data && buat.data.node;
    if (!node) {
      console.error("GAGAL buat node:", JSON.stringify(buat).slice(0, 300));
      process.exit(1);
    }
    console.log("node dibuat:", node.id);
  }

  // 2. Koneksi API key ke node
  const conns = await api.getProviders();
  const list =
    (conns && conns.data && (conns.data.connections || conns.data.providers)) ||
    [];
  const sudah = list.some(
    (c) => c.provider === node.id || c.providerId === node.id
  );
  if (sudah) {
    console.log("koneksi API key cutad sudah ada, lewati");
  } else {
    const kon = await api.createApiKeyProvider({
      provider: node.id,
      name: "cutad key",
      apiKey: API_KEY,
    });
    console.log("koneksi dibuat:", JSON.stringify(kon).slice(0, 250));
  }

  // 3. Kunci gateway sk_9router untuk client (Codex dst)
  const keys = await api.getApiKeys();
  const daftarKey = (keys && keys.data && keys.data.keys) || [];
  const ada = daftarKey.find((k) => k.name === "sk_9router");
  if (ada) {
    console.log("gateway key sk_9router sudah ada (id", ada.id + ")");
    console.log("key:", ada.key || ada.apiKey || "(lihat dashboard)");
  } else {
    const buat = await api.createApiKey("sk_9router");
    console.log("gateway key dibuat:", JSON.stringify(buat.data).slice(0, 300));
  }

  // 4. Verifikasi model tersedia
  const models = await api.getAvailableModels();
  const ids =
    ((models && models.data && models.data.data) || []).map((m) => m.id) || [];
  const cocok = ids.filter((i) => i.startsWith("cd/"));
  console.log("model dengan prefix cd:", cocok.slice(0, 10));
  process.exit(0);
})().catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});
