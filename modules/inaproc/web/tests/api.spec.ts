import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "../src/api";

describe("api error envelope", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("membaca error string dari envelope baru", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ error: "belum_login", message: "Connect the INAPROC provider session first" }),
    }));

    await expect(api.session()).rejects.toMatchObject({
      code: "belum_login",
      message: "Connect the INAPROC provider session first",
      status: 401,
    } satisfies Partial<ApiError>);
  });
});
