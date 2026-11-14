package de.mcben.cosmetics.client;

/**
 * Baut ein rundes Stofftier aus der normalen Skin-Aufteilung (64x64), Proportionen wie ein echtes Minecraft-Plushie:
 * grosser weicher Kopf, kleiner Koerper, kurze Arme, sitzende Beine.
 * Raum: Einheit = 1 Block, Mitte bei x=z=0.5, Boden y=0, Gesicht zeigt nach -Z.
 */
public final class PlushMesh {
	private PlushMesh() {}

	private static float[] buf;
	private static int n;

	public static float[] build(boolean overlays) {
		buf = new float[200_000];
		n = 0;
		float s = 0.5f; // Gesamtgroesse
		// Kopf + Hut
		box(0.5f, 0.70f * s + 0.12f, 0.5f, 0.50f * s, 0.46f * s, 0.47f * s, 0.13f * s, 0, 0, 8, 8, 8, 0, 0, 0.02f);
		if (overlays) box(0.5f, 0.70f * s + 0.12f, 0.5f, 0.53f * s, 0.49f * s, 0.50f * s, 0.14f * s, 32, 0, 8, 8, 8, 0, 0, 0.02f);
		// Koerper + Jacke
		box(0.5f, 0.28f * s + 0.12f - 0.02f, 0.5f + 0.01f, 0.31f * s, 0.28f * s, 0.20f * s, 0.07f * s, 16, 16, 8, 12, 4, 0, 0, 0.01f);
		if (overlays) box(0.5f, 0.28f * s + 0.12f - 0.02f, 0.5f + 0.01f, 0.325f * s, 0.295f * s, 0.215f * s, 0.075f * s, 16, 32, 8, 12, 4, 0, 0, 0.01f);
		// Arme (leicht nach vorne)
		box(0.5f - 0.235f * s, 0.32f * s + 0.10f, 0.5f - 0.04f * s, 0.15f * s, 0.25f * s, 0.15f * s, 0.065f * s, 40, 16, 4, 12, 4, -38, 14, 0.01f);
		box(0.5f + 0.235f * s, 0.32f * s + 0.10f, 0.5f - 0.04f * s, 0.15f * s, 0.25f * s, 0.15f * s, 0.065f * s, 32, 48, 4, 12, 4, -38, -14, 0.01f);
		// Beine (sitzend, Fuesse nach vorne)
		box(0.5f - 0.08f * s, 0.085f * s + 0.02f, 0.5f - 0.08f * s, 0.15f * s, 0.23f * s, 0.16f * s, 0.065f * s, 0, 16, 4, 12, 4, -82, 0, 0.01f);
		box(0.5f + 0.08f * s, 0.085f * s + 0.02f, 0.5f - 0.08f * s, 0.15f * s, 0.23f * s, 0.16f * s, 0.065f * s, 16, 48, 4, 12, 4, -82, 0, 0.01f);
		float[] out = new float[n];
		System.arraycopy(buf, 0, out, 0, n);
		buf = null;
		return out;
	}

	/**
	 * Abgerundete, leicht aufgeplusterte Box mit Skin-UVs.
	 * cx,cy,cz Mitte; hx,hy,hz halbe Groessen; r Rundung; (u,v,w,h,d) Skin-Box in Pixeln;
	 * rotX/rotY Neigung in Grad (um die Mitte); puff Aufpluster-Staerke.
	 */
	private static void box(float cx, float cy, float cz, float hx, float hy, float hz, float r,
							int u, int v, int w, int h, int d, float rotX, float rotY, float puff) {
		int res = 8;
		// Seiten: Ursprung-Funktion (a,b in [-1,1]), Normale, Skin-Rechteck. Vorne = -Z, rechte Spielerseite = -X.
		float[][] normals = {{0, 0, -1}, {0, 0, 1}, {-1, 0, 0}, {1, 0, 0}, {0, 1, 0}, {0, -1, 0}};
		int[][] rects = {
			{u + d, v + d, w, h}, {u + 2 * d + w, v + d, w, h}, {u, v + d, d, h},
			{u + d + w, v + d, d, h}, {u + d, v, w, d}, {u + d + w, v, w, d}};
		double ax = Math.toRadians(rotX), ay = Math.toRadians(rotY);
		float ix = Math.max(0, hx - r), iy = Math.max(0, hy - r), iz = Math.max(0, hz - r);
		for (int f = 0; f < 6; f++) {
			float[][][] grid = new float[res + 1][res + 1][];
			for (int j = 0; j <= res; j++) {
				for (int i = 0; i <= res; i++) {
					float a = -1 + 2f * i / res, b = -1 + 2f * j / res;
					float[] p = facePoint(f, a, b, hx, hy, hz);
					// auf abgerundete Box projizieren
					float qx = clamp(p[0], -ix, ix), qy = clamp(p[1], -iy, iy), qz = clamp(p[2], -iz, iz);
					float dx = p[0] - qx, dy = p[1] - qy, dz = p[2] - qz;
					float len = (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
					float nx = normals[f][0], ny = normals[f][1], nz = normals[f][2];
					if (len > 1e-6f) { dx /= len; dy /= len; dz /= len; p[0] = qx + dx * r; p[1] = qy + dy * r; p[2] = qz + dz * r; nx = dx; ny = dy; nz = dz; }
					float pf = puff * (1 - a * a) * (1 - b * b);
					p[0] += normals[f][0] * pf; p[1] += normals[f][1] * pf; p[2] += normals[f][2] * pf;
					float[] rp = rotate(p, ax, ay), rn = rotate(new float[]{nx, ny, nz}, ax, ay);
					int[] rc = rects[f];
					float uu = (rc[0] + (i / (float) res) * rc[2]) / 64f;
					float vv = (rc[1] + (1 - j / (float) res) * rc[3]) / 64f;
					grid[j][i] = new float[]{cx + rp[0], cy + rp[1], cz + rp[2], uu, vv, rn[0], rn[1], rn[2]};
				}
			}
			for (int j = 0; j < res; j++) {
				for (int i = 0; i < res; i++) {
					tri(grid[j][i], grid[j][i + 1], grid[j + 1][i + 1]);
					tri(grid[j][i], grid[j + 1][i + 1], grid[j + 1][i]);
				}
			}
		}
	}

	private static float[] facePoint(int f, float a, float b, float hx, float hy, float hz) {
		return switch (f) {
			case 0 -> new float[]{a * hx, b * hy, -hz};      // vorne (-Z), u nach +X
			case 1 -> new float[]{-a * hx, b * hy, hz};      // hinten
			case 2 -> new float[]{-hx, b * hy, -a * hz};     // rechte Spielerseite (-X)... u Richtung vorne
			case 3 -> new float[]{hx, b * hy, a * hz};       // linke Seite
			case 4 -> new float[]{a * hx, hy, b * hz};       // oben, unterer Bildrand = vorne
			default -> new float[]{a * hx, -hy, -b * hz};    // unten
		};
	}

	private static float[] rotate(float[] p, double ax, double ay) {
		float y = (float) (p[1] * Math.cos(ax) - p[2] * Math.sin(ax));
		float z = (float) (p[1] * Math.sin(ax) + p[2] * Math.cos(ax));
		float x = (float) (p[0] * Math.cos(ay) + z * Math.sin(ay));
		z = (float) (-p[0] * Math.sin(ay) + z * Math.cos(ay));
		return new float[]{x, y, z};
	}

	private static float clamp(float v, float lo, float hi) { return Math.max(lo, Math.min(hi, v)); }

	private static void tri(float[] a, float[] b, float[] c) {
		for (float[] p : new float[][]{a, b, c}) { System.arraycopy(p, 0, buf, n, 8); n += 8; }
	}
}
