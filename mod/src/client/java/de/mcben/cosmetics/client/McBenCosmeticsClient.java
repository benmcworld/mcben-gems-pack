package de.mcben.cosmetics.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.LivingEntityRenderLayerRegistrationCallback;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class McBenCosmeticsClient implements ClientModInitializer {
	public static final String MOD_ID = "mcbencosmetics";
	public static final Logger LOG = LoggerFactory.getLogger(MOD_ID);

	private static KeyMapping openMenu, fullbrightKey, zoomKey;
	/** Fuer Tests: Zoom ohne Tastendruck erzwingen. */
	public static boolean forceZoom = false;

	public static float zoomAmount() {
		CosmeticsConfig c = CosmeticsConfig.get();
		boolean held = forceZoom || (zoomKey != null && zoomKey.isDown());
		return c.zoom && held ? Math.max(1f, c.zoomFactor) : 1f;
	}

	@Override
	public void onInitializeClient() {
		CosmeticsConfig.get();
		KeyMapping.Category category = KeyMapping.Category.register(Identifier.fromNamespaceAndPath(MOD_ID, "main"));
		openMenu = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.mcbencosmetics.menu", InputConstants.Type.KEYBOARD, InputConstants.KEY_K, category));
		fullbrightKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.mcbencosmetics.fullbright", InputConstants.Type.KEYBOARD, InputConstants.KEY_G, category));
		zoomKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.mcbencosmetics.zoom", InputConstants.Type.KEYBOARD, InputConstants.KEY_C, category));

		ClientTickEvents.END_CLIENT_TICK.register(mc -> {
			while (openMenu.consumeClick()) mc.gui.setScreen(new McBenScreen(mc.gui.screen()));
			while (fullbrightKey.consumeClick()) {
				CosmeticsConfig c = CosmeticsConfig.get();
				c.fullbright = !c.fullbright;
				c.save();
			}
			autoSprint(mc);
			HudLayout.trackDeath(mc);
			HudLayout.tick(mc);
		});
		HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(MOD_ID, "overlays"), (g, delta) -> {
			Minecraft mc = Minecraft.getInstance();
			HudLayout.trackClicks(mc);
			if (!(mc.gui.screen() instanceof HudEditorScreen)) HudLayout.render(g, false);
		});
		LevelRenderEvents.COLLECT_SUBMITS.register(TotemGhosts::submit);
		AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) -> {
			if (level.isClientSide() && player instanceof LocalPlayer lp) HudLayout.onAttack(lp, entity);
			return InteractionResult.PASS;
		});
		LivingEntityRenderLayerRegistrationCallback.EVENT.register((type, renderer, helper, ctx) -> {
			if (renderer instanceof AvatarRenderer<?> avatar) helper.register(new CosmeticsLayer(avatar));
		});
		LOG.info("McBen Cosmetics geladen – Menü mit Taste K");
	}

	private static void autoSprint(Minecraft mc) {
		if (!CosmeticsConfig.get().autoSprint || mc.player == null) return;
		if (mc.options.keyUp.isDown() && !mc.player.isShiftKeyDown() && !mc.player.isUsingItem()) mc.options.keySprint.setDown(true);
	}
}
