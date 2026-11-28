package de.mcben.cosmetics.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.LightCoordsUtil;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.PlayerModelType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

/** Totem-Pop: an der Stelle bleibt kurz ein flackernder, leuchtender Umriss des Spielers stehen. */
public final class TotemGhosts {
	private TotemGhosts() {}

	private static final Identifier WHITE = Identifier.fromNamespaceAndPath(McBenCosmeticsClient.MOD_ID, "textures/cosmetics/white.png");

	static final class Ghost {
		int entityId;
		double x, y, z;
		float bodyRot;
		Identifier skin;
		boolean slim;
		List<PartPose> poses;
		long start = System.currentTimeMillis();
		boolean posed;
	}

	private static final List<Ghost> GHOSTS = new ArrayList<>();
	private static final Map<String, Integer> POPS = new HashMap<>();
	private static PlayerModel wide, slim, poser, poserSlim;

	public static int ownPops() {
		Minecraft mc = Minecraft.getInstance();
		return mc.player == null ? 0 : POPS.getOrDefault(mc.player.getName().getString(), 0);
	}

	/** Paket "Entity-Event 35" (Totem ausgeloest) kam an. */
	public static void onPop(Entity e) {
		if (!(e instanceof AbstractClientPlayer pl)) return;
		Minecraft mc = Minecraft.getInstance();
		CosmeticsConfig c = CosmeticsConfig.get();
		boolean self = mc.player != null && pl.getId() == mc.player.getId();
		String name = pl.getName().getString();
		int n = POPS.merge(name, 1, Integer::sum);
		if (c.popMessage && !self && mc.player != null) {
			mc.player.sendOverlayMessage(Component.literal("✦ " + name + " hat ein Totem verloren  (" + n + ". Pop)")
				.withColor(c.accent() & 0xFFFFFF));
		}
		if (!c.totemGhost || (!self && !c.ghostOthers)) return;
		Ghost g = new Ghost();
		g.entityId = pl.getId();
		g.x = pl.getX(); g.y = pl.getY(); g.z = pl.getZ();
		g.bodyRot = pl.yBodyRot;
		g.skin = pl.getSkin().body().texturePath();
		g.slim = pl.getSkin().model() == PlayerModelType.SLIM;
		synchronized (GHOSTS) { GHOSTS.add(g); }
		McBenCosmeticsClient.LOG.debug("Totem-Pop von {} bei {} {} {}", name, g.x, g.y, g.z);
	}

	/** Knopf "Umriss testen": Umriss zwei Bloecke vor dem eigenen Spieler. */
	public static void spawnTestGhost() {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null) return;
		Vec3 look = Vec3.directionFromRotation(0, mc.player.getYRot());
		Ghost g = new Ghost();
		g.entityId = -1;
		g.x = mc.player.getX() + look.x * 2.5; g.y = mc.player.getY(); g.z = mc.player.getZ() + look.z * 2.5;
		g.bodyRot = mc.player.getYRot() + 180;
		g.skin = mc.player.getSkin().body().texturePath();
		g.slim = mc.player.getSkin().model() == PlayerModelType.SLIM;
		synchronized (GHOSTS) { GHOSTS.add(g); }
	}

	private static PlayerModel model(boolean isSlim) {
		if (wide == null) {
			var models = Minecraft.getInstance().getEntityModels();
			wide = new PlayerModel(models.bakeLayer(ModelLayers.PLAYER), false);
			slim = new PlayerModel(models.bakeLayer(ModelLayers.PLAYER_SLIM), true);
			poser = new PlayerModel(models.bakeLayer(ModelLayers.PLAYER), false);
			poserSlim = new PlayerModel(models.bakeLayer(ModelLayers.PLAYER_SLIM), true);
		}
		return isSlim ? slim : wide;
	}

	/** Wird beim Zeichnen jedes Spielers aufgerufen: Haltung im Moment des Pops uebernehmen. */
	public static void capturePose(AvatarRenderState state) {
		if (GHOSTS.isEmpty()) return;
		synchronized (GHOSTS) {
			for (Ghost g : GHOSTS) {
				if (g.posed || g.entityId != state.id || System.currentTimeMillis() - g.start > 250) continue;
				model(g.slim);
				PlayerModel m = g.slim ? poserSlim : poser;
				m.resetPose();
				m.setupAnim(state);
				List<PartPose> poses = new ArrayList<>();
				for (ModelPart p : m.allParts()) poses.add(p.storePose());
				g.poses = poses;
				g.x = state.x; g.y = state.y; g.z = state.z;
				g.bodyRot = state.bodyRot;
				g.posed = true;
			}
		}
	}

	private static int colorRgb(Ghost g, CosmeticsConfig c) {
		return switch (c.ghostColor) {
			case "akzent" -> c.accent() & 0xFFFFFF;
			case "weiss" -> 0xFFFFFF;
			case "rot" -> 0xFF4A4A;
			case "skin" -> 0xFFFFFF;
			default -> 0xFFD34D;
		};
	}

	/** Zeichnen in der Welt. */
	public static void submit(LevelRenderContext ctx) {
		if (GHOSTS.isEmpty()) return;
		CosmeticsConfig c = CosmeticsConfig.get();
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		PoseStack ps = ctx.poseStack();
		long now = System.currentTimeMillis();
		float dur = Math.max(0.2f, c.ghostTime) * 1000f;
		synchronized (GHOSTS) {
			Iterator<Ghost> it = GHOSTS.iterator();
			while (it.hasNext()) {
				Ghost g = it.next();
				float t = (now - g.start) / dur;
				if (t >= 1f) { it.remove(); continue; }
				double dx = g.x - cam.x, dy = g.y - cam.y, dz = g.z - cam.z;
				if (dx * dx + dz * dz < 1.0 && dy > -2.2 && dy < 0.5) continue;   // Kamera steckt drin

				// Flackern: am Anfang hart an/aus, dann sanft pulsierend ausblenden
				float age = now - g.start;
				float flicker = age < 260 ? ((int) (age / 65) % 2 == 0 ? 1f : 0.25f)
					: 0.7f + 0.3f * (float) Math.sin(age / 38.0);
				float alpha = (float) Math.pow(1f - t, 0.8) * flicker;
				int rgb = colorRgb(g, c);
				boolean skinOnly = "skin".equals(c.ghostColor);
				int inner = Math.round(alpha * (skinOnly ? 210 : 175)) << 24 | (skinOnly ? 0xFFFFFF : mix(rgb, 0xFFFFFF, 0.35f));
				int shell = Math.round(alpha * 150) << 24 | rgb;
				int halo = Math.round(alpha * 55) << 24 | rgb;
				float grow = 1f + t * 0.12f;

				PlayerModel model = model(g.slim);
				List<PartPose> poses = g.poses;
				ps.pushPose();
				ps.translate(dx, dy, dz);
				ps.rotateDegrees(Axis.YP, 180f - g.bodyRot);
				ps.translate(0f, 0.9f, 0f);
				ps.scale(grow, grow, grow);
				ps.translate(0f, -0.9f, 0f);
				ps.scale(-1f, -1f, 1f);
				ps.scale(0.9375f, 0.9375f, 0.9375f);
				ps.translate(0f, -1.501f, 0f);
				ctx.submitNodeCollector().submitCustomGeometry(ps, RenderTypes.entityTranslucent(g.skin),
					(pose, vc) -> drawModel(model, poses, pose, vc, inner, 1f));
				if (!skinOnly) {
					ctx.submitNodeCollector().submitCustomGeometry(ps, RenderTypes.entityTranslucentEmissive(WHITE),
						(pose, vc) -> drawModel(model, poses, pose, vc, shell, 1.06f));
					ctx.submitNodeCollector().submitCustomGeometry(ps, RenderTypes.entityTranslucentEmissive(WHITE),
						(pose, vc) -> drawModel(model, poses, pose, vc, halo, 1.13f));
				}
				ps.popPose();
			}
		}
	}

	private static void drawModel(PlayerModel model, List<PartPose> poses, PoseStack.Pose pose, com.mojang.blaze3d.vertex.VertexConsumer vc, int argb, float inflate) {
		List<ModelPart> parts = model.allParts();
		if (poses != null && poses.size() == parts.size()) {
			for (int i = 0; i < parts.size(); i++) parts.get(i).loadPose(poses.get(i));
		} else {
			model.resetPose();
		}
		for (ModelPart p : parts) p.visible = true;
		PoseStack tmp = new PoseStack();
		tmp.last().set(pose);
		if (inflate != 1f) {
			tmp.translate(0f, 0.75f, 0f);
			tmp.scale(inflate, inflate * 0.985f, inflate);
			tmp.translate(0f, -0.75f, 0f);
		}
		model.root().render(tmp, vc, LightCoordsUtil.FULL_BRIGHT, OverlayTexture.NO_OVERLAY, argb);
	}

	private static int mix(int a, int b, float f) {
		int r = (int) (((a >> 16) & 255) * (1 - f) + ((b >> 16) & 255) * f);
		int gg = (int) (((a >> 8) & 255) * (1 - f) + ((b >> 8) & 255) * f);
		int bl = (int) ((a & 255) * (1 - f) + (b & 255) * f);
		return r << 16 | gg << 8 | bl;
	}
}
