package de.mcben.cosmetics.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.LivingEntityRenderLayerRegistrationCallback;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class McBenCosmeticsClient implements ClientModInitializer {
	public static final String MOD_ID = "mcbencosmetics";
	public static final Logger LOG = LoggerFactory.getLogger(MOD_ID);

	private static KeyMapping openMenu;

	@Override
	public void onInitializeClient() {
		CosmeticsConfig.get();
		KeyMapping.Category category = KeyMapping.Category.register(Identifier.fromNamespaceAndPath(MOD_ID, "main"));
		openMenu = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.mcbencosmetics.menu", InputConstants.Type.KEYBOARD, InputConstants.KEY_K, category));
		ClientTickEvents.END_CLIENT_TICK.register(mc -> {
			while (openMenu.consumeClick()) mc.gui.setScreen(new CosmeticsScreen(mc.gui.screen()));
		});
		LivingEntityRenderLayerRegistrationCallback.EVENT.register((type, renderer, helper, ctx) -> {
			if (renderer instanceof AvatarRenderer<?> avatar) helper.register(new CosmeticsLayer(avatar));
		});
		LOG.info("McBen Cosmetics geladen – Menü mit Taste K");
	}
}
