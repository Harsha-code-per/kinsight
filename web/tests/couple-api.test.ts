import { afterEach, expect, test, vi } from "vitest";
import { real } from "../lib/real";

afterEach(() => vi.unstubAllGlobals());

test("keeps access denials distinct from request failures", async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(new Response(null, { status: 403 }))
    .mockResolvedValueOnce(new Response(null, { status: 401 }))
    .mockResolvedValueOnce(new Response(null, { status: 503 }));
  vi.stubGlobal("fetch", fetchMock);
  await expect(real.couple()).resolves.toMatchObject({ tier: null, findings: null });
  await expect(real.couple()).rejects.toThrow("401");
  await expect(real.couple()).rejects.toThrow("503");
});

test("distinguishes restricted findings from a released empty list", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(Response.json({ tier: 1 }))
    .mockResolvedValueOnce(Response.json({ tier: 1, findings: [] })));
  await expect(real.couple()).resolves.toMatchObject({ tier: 1, findings: null });
  await expect(real.couple()).resolves.toMatchObject({ tier: 1, findings: [] });
});
