package de.mcben.cosmetics.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.serialization.MapCodec;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.PlayerSkinRenderCache;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.special.NoDataSpecialModelRenderer;
import net.minecraft.client.renderer.special.SpecialModelRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.component.ResolvableProfile;
import org.joml.Vector3f;
import org.joml.Vector3fc;

import java.util.function.Consumer;

/** Totem als Plushie: eigener Skin oder der Skin eines eingetragenen Spielernamens. */
public class PlushieRenderer implements NoDataSpecialModelRenderer {
	private static float[] mesh;
	private final PlayerSkinRenderCache skins;

	public PlushieRenderer(PlayerSkinRenderCache skins) {
		this.skins = skins;
	}

	private Identifier skinTexture() {
		Minecraft mc = Minecraft.getInstance();
		String name = CosmeticsConfig.get().plushieName;
		try {
			if (name != null && !name.isBlank()) {
				return skins.getOrDefault(ResolvableProfile.createUnresolved(name.trim())).playerSkin().body().texturePath();
			}
			if (mc.player != null) return mc.player.getSkin().body().texturePath();
		} catch (Exception e) {
			McBenCosmeticsClient.LOG.debug("Skin nicht verfuegbar", e);
		}
		return null;
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, int overlay, boolean foil, int outline) {
		Identifier tex = skinTexture();
		if (tex == null) return;
		if (mesh == null) mesh = PlushMesh.build(true);
		float[] m = mesh;
		collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucent(tex), (pose, vc) -> {
			int s = ObjMesh.STRIDE;
			for (int t = 0; t + 3 * s <= m.length; t += 3 * s) {
				for (int k = 0; k < 4; k++) {
					int i = t + Math.min(k, 2) * s;
					vc.addVertex(pose, m[i], m[i + 1], m[i + 2]).setColor(0xFFFFFFFF).setUv(m[i + 3], m[i + 4])
						.setOverlay(OverlayTexture.NO_OVERLAY).setLight(light).setNormal(pose, m[i + 5], m[i + 6], m[i + 7]);
				}
			}
		});
	}

	@Override
	public void getExtents(Consumer<Vector3fc> out) {
		out.accept(new Vector3f(0.2f, 0f, 0.2f));
		out.accept(new Vector3f(0.8f, 0.75f, 0.8f));
	}

	public record Unbaked() implements NoDataSpecialModelRenderer.Unbaked {
		public static final MapCodec<Unbaked> MAP_CODEC = MapCodec.unit(new Unbaked());

		@Override
		public SpecialModelRenderer<Void> bake(SpecialModelRenderer.BakingContext ctx) {
			return new PlushieRenderer(ctx.playerSkinRenderCache());
		}

		@Override
		public MapCodec<Unbaked> type() {
			return MAP_CODEC;
		}
	}
}
