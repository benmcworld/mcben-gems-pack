package de.mcben.cosmetics.client;

import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;

import java.io.BufferedReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Minimaler OBJ-Leser fuer die aus Blender exportierten Modelle.
 * Pro Material eine flache Liste von Dreiecken: je Ecke x,y,z,u,v,nx,ny,nz.
 */
public class ObjMesh {
	public static final int STRIDE = 8;
	public final Map<String, float[]> parts = new HashMap<>();

	public static ObjMesh load(Identifier id) {
		ObjMesh mesh = new ObjMesh();
		List<float[]> v = new ArrayList<>(), vt = new ArrayList<>(), vn = new ArrayList<>();
		Map<String, List<Float>> out = new HashMap<>();
		List<Float> cur = null;
		try (BufferedReader r = Minecraft.getInstance().getResourceManager().openAsReader(id)) {
			String line;
			while ((line = r.readLine()) != null) {
				if (line.isEmpty() || line.charAt(0) == '#') continue;
				String[] p = line.trim().split("\\s+");
				switch (p[0]) {
					case "v" -> v.add(new float[]{Float.parseFloat(p[1]), Float.parseFloat(p[2]), Float.parseFloat(p[3])});
					case "vt" -> vt.add(new float[]{Float.parseFloat(p[1]), Float.parseFloat(p[2])});
					case "vn" -> vn.add(new float[]{Float.parseFloat(p[1]), Float.parseFloat(p[2]), Float.parseFloat(p[3])});
					case "usemtl" -> cur = out.computeIfAbsent(p[1], k -> new ArrayList<>());
					case "f" -> {
						if (cur == null) cur = out.computeIfAbsent("default", k -> new ArrayList<>());
						for (int k = 1; k <= 3; k++) {
							String[] idx = p[k].split("/");
							float[] pos = v.get(Integer.parseInt(idx[0]) - 1);
							float[] uv = idx.length > 1 && !idx[1].isEmpty() ? vt.get(Integer.parseInt(idx[1]) - 1) : new float[]{0, 0};
							float[] n = idx.length > 2 ? vn.get(Integer.parseInt(idx[2]) - 1) : new float[]{0, -1, 0};
							cur.add(pos[0]); cur.add(pos[1]); cur.add(pos[2]);
							cur.add(uv[0]); cur.add(uv[1]);
							cur.add(n[0]); cur.add(n[1]); cur.add(n[2]);
						}
					}
					default -> { }
				}
			}
		} catch (Exception e) {
			McBenCosmeticsClient.LOG.error("Modell {} konnte nicht geladen werden", id, e);
		}
		out.forEach((name, list) -> {
			float[] a = new float[list.size()];
			for (int i = 0; i < a.length; i++) a[i] = list.get(i);
			mesh.parts.put(name, a);
		});
		return mesh;
	}
}
