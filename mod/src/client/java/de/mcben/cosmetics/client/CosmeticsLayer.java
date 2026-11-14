package de.mcben.cosmetics.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.LightCoordsUtil;

/** Zeichnet Fluegel und Heiligenschein am eigenen Spieler. */
public class CosmeticsLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	private static final String NS = McBenCosmeticsClient.MOD_ID;
	private static final Identifier WING_MODEL = Identifier.fromNamespaceAndPath(NS, "models/wing_feather.obj");
	private static final Identifier GLOW_TEX = Identifier.fromNamespaceAndPath(NS, "textures/cosmetics/feather_glow.png");
	private static final Identifier WHITE_TEX = Identifier.fromNamespaceAndPath(NS, "textures/cosmetics/white.png");
	/** Fluegelwurzel im Koerper-Modellraum (Bloecke): leicht hinter dem Ruecken, Schulterhoehe. */
	private static final float ROOT_X = -0.15f, ROOT_Y = 0.05f, ROOT_Z = 0.2f;

	private static ObjMesh wingMesh;
	private static float[] haloMesh;

	public CosmeticsLayer(RenderLayerParent<AvatarRenderState, PlayerModel> parent) {
		super(parent);
	}

	private static boolean isLocalPlayer(AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		return mc.player != null && state.id == mc.player.getId();
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		if (state.isInvisible || !isLocalPlayer(state)) return;
		CosmeticsConfig cfg = CosmeticsConfig.get();
		if (!"aus".equals(cfg.wings)) submitWings(poseStack, collector, light, state, cfg);
		if (cfg.halo) submitHalo(poseStack, collector, state, cfg);
	}

	// ------------------------------------------------------------------ Fluegel
	private void submitWings(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, CosmeticsConfig cfg) {
		if (wingMesh == null) wingMesh = ObjMesh.load(WING_MODEL);
		float[] feathers = wingMesh.parts.get("feather");
		float[] edge = wingMesh.parts.get("glow");
		if (feathers == null) return;

		String texName = "engel".equals(cfg.wings) ? "engel" : cfg.theme;
		Identifier tex = Identifier.fromNamespaceAndPath(NS, "textures/cosmetics/feather_" + texName + ".png");
		int tip = CosmeticsConfig.tipColor(cfg.theme);
		int glow = scale(tip, Math.min(1f, cfg.brightness * 0.75f));
		float flap = cfg.flap ? (float) Math.sin(state.ageInTicks * 0.12f) * 9f : 0f;
		if (state.isCrouching) flap -= 10f;

		poseStack.pushPose();
		getParentModel().body.translateAndRotate(poseStack);
		for (int side = -1; side <= 1; side += 2) {
			poseStack.pushPose();
			if (side > 0) poseStack.scale(-1f, 1f, 1f);           // linker Fluegel = gespiegelter rechter
			poseStack.translate(ROOT_X, ROOT_Y, ROOT_Z);
			poseStack.rotateDegrees(Axis.YP, -flap);       // Fluegelschlag um die Wurzel
			poseStack.translate(-ROOT_X, -ROOT_Y, -ROOT_Z);
			poseStack.translate(0f, 0f, 0.02f);
			boolean mirrored = side > 0;   // gespiegelt -> Dreiecke andersherum ausgeben, damit Rueckseiten-Culling stimmt
			collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucentCull(tex), (pose, vc) -> emit(pose, vc, feathers, 0xFFFFFFFF, light, mirrored));
			if (cfg.brightness > 0.05f) {
				collector.submitCustomGeometry(poseStack, RenderTypes.eyes(GLOW_TEX), (pose, vc) -> emit(pose, vc, feathers, 0xFF000000 | glow, LightCoordsUtil.FULL_BRIGHT, mirrored));
				if (edge != null)
					collector.submitCustomGeometry(poseStack, RenderTypes.eyes(WHITE_TEX), (pose, vc) -> emit(pose, vc, edge, 0xFF000000 | glow, LightCoordsUtil.FULL_BRIGHT, mirrored));
			}
			poseStack.popPose();
		}
		poseStack.popPose();
	}

	// ------------------------------------------------------------------ Heiligenschein
	private void submitHalo(PoseStack poseStack, SubmitNodeCollector collector, AvatarRenderState state, CosmeticsConfig cfg) {
		if (haloMesh == null) haloMesh = torus(0.27f, 0.028f, 40, 10);
		int color = 0xFF000000 | scale(CosmeticsConfig.tipColor(cfg.theme), Math.min(1f, cfg.brightness * 0.6f));
		poseStack.pushPose();
		getParentModel().head.translateAndRotate(poseStack);
		poseStack.translate(0f, -0.72f + (float) Math.sin(state.ageInTicks * 0.08f) * 0.025f, 0f);
		poseStack.rotateDegrees(Axis.XP, 8f);
		poseStack.rotateDegrees(Axis.YP, state.ageInTicks * 1.5f);
		collector.submitCustomGeometry(poseStack, RenderTypes.eyes(WHITE_TEX), (pose, vc) -> emit(pose, vc, haloMesh, color, LightCoordsUtil.FULL_BRIGHT, false));
		poseStack.popPose();
	}

	// ------------------------------------------------------------------ Helfer
	/** Dreiecke als (entartete) Vierecke ausgeben – Entity-Rendertypen zeichnen Quads. */
	static void emit(PoseStack.Pose pose, VertexConsumer vc, float[] tris, int argb, int light, boolean reverse) {
		int s = ObjMesh.STRIDE;
		for (int t = 0; t + 3 * s <= tris.length; t += 3 * s) {
			for (int k = 0; k < 4; k++) {
				int c = Math.min(k, 2);
				int i = t + (reverse ? 2 - c : c) * s;
				vc.addVertex(pose, tris[i], tris[i + 1], tris[i + 2])
					.setColor(argb)
					.setUv(tris[i + 3], tris[i + 4])
					.setOverlay(OverlayTexture.NO_OVERLAY)
					.setLight(light)
					.setNormal(pose, tris[i + 5], tris[i + 6], tris[i + 7]);
			}
		}
	}

	private static int scale(int rgb, float f) {
		int r = Math.min(255, (int) (((rgb >> 16) & 255) * f));
		int g = Math.min(255, (int) (((rgb >> 8) & 255) * f));
		int b = Math.min(255, (int) ((rgb & 255) * f));
		return (r << 16) | (g << 8) | b;
	}

	/** Torus in der XZ-Ebene als Dreiecksliste. */
	private static float[] torus(float R, float r, int seg, int rseg) {
		float[] out = new float[seg * rseg * 6 * ObjMesh.STRIDE];
		int o = 0;
		for (int i = 0; i < seg; i++) {
			for (int j = 0; j < rseg; j++) {
				int[][] q = {{i, j}, {i + 1, j}, {i + 1, j + 1}, {i, j}, {i + 1, j + 1}, {i, j + 1}};
				for (int[] c : q) {
					double a = 2 * Math.PI * c[0] / seg, b = 2 * Math.PI * c[1] / rseg;
					float nx = (float) (Math.cos(b) * Math.cos(a)), ny = (float) Math.sin(b), nz = (float) (Math.cos(b) * Math.sin(a));
					out[o++] = (float) ((R + r * Math.cos(b)) * Math.cos(a));
					out[o++] = (float) (r * Math.sin(b));
					out[o++] = (float) ((R + r * Math.cos(b)) * Math.sin(a));
					out[o++] = 0.5f; out[o++] = 0.5f;
					out[o++] = nx; out[o++] = ny; out[o++] = nz;
				}
			}
		}
		return out;
	}
}
