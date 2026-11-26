package de.mcben.cosmetics.test;

import de.mcben.cosmetics.client.CosmeticsConfig;
import de.mcben.cosmetics.client.MainMenuScreen;
import de.mcben.cosmetics.client.McBenCosmeticsClient;
import de.mcben.cosmetics.client.ModsScreen;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Erstellt eine Welt und fotografiert Cosmetics und Mods aus mehreren Blickwinkeln. */
public class CosmeticsGameTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext sp = ctx.worldBuilder().create()) {
			sp.getServer().runCommand("time set 6000");
			sp.getServer().runCommand("weather clear");
			sp.getServer().runCommand("tp @a ~ ~ ~ 180 10");
			sp.getConnection().waitForChunksRender();
			ctx.runOnClient(mc -> { CosmeticsConfig c = CosmeticsConfig.get(); c.infoHud = false; c.keystrokes = false; c.armorHud = false; });

			shoot(ctx, "galaxie", "lila", false, "1_galaxie_lila");
			shoot(ctx, "engel", "lila", true, "2_engel_heiligenschein");
			shoot(ctx, "galaxie", "gruen", true, "3_galaxie_gruen");
			shoot(ctx, "galaxie", "dark", false, "4_galaxie_dark");

			// Plushie-Totem
			sp.getServer().runCommand("give @a totem_of_undying");
			ctx.runOnClient(mc -> { CosmeticsConfig.get().wings = "aus"; CosmeticsConfig.get().halo = false; });
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(10);
			ctx.takeScreenshot("5_plushie_hand");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(5);
			ctx.takeScreenshot("6_plushie_ich");
			ctx.setScreen(() -> new InventoryScreen(net.minecraft.client.Minecraft.getInstance().player));
			ctx.waitTicks(5);
			ctx.takeScreenshot("7_plushie_inventar");
			ctx.setScreen(() -> null);
			ctx.runOnClient(mc -> mc.player.displayItemActivation(new ItemStack(Items.TOTEM_OF_UNDYING)));
			ctx.waitTicks(12);
			ctx.takeScreenshot("8_plushie_ausloesen");
			ctx.waitTicks(40);

			// Menues
			ctx.setScreen(() -> new MainMenuScreen(null));
			ctx.waitTicks(5);
			ctx.takeScreenshot("9_menue_haupt");
			ctx.setScreen(() -> new ModsScreen(null));
			ctx.waitTicks(5);
			ctx.takeScreenshot("10_menue_mods");
			ctx.setScreen(() -> null);

			// Anzeigen: Info, Keystrokes, Ruestung
			sp.getServer().runCommand("item replace entity @a armor.head with diamond_helmet");
			sp.getServer().runCommand("item replace entity @a armor.chest with diamond_chestplate");
			sp.getServer().runCommand("item replace entity @a armor.legs with iron_leggings");
			sp.getServer().runCommand("item replace entity @a armor.feet with iron_boots");
			sp.getServer().runCommand("item replace entity @a weapon.mainhand with diamond_sword");
			ctx.runOnClient(mc -> { CosmeticsConfig c = CosmeticsConfig.get(); c.infoHud = true; c.keystrokes = true; c.armorHud = true; });
			ctx.waitTicks(10);
			ctx.takeScreenshot("11_anzeigen");

			// Zoom
			ctx.runOnClient(mc -> McBenCosmeticsClient.forceZoom = true);
			ctx.waitTicks(5);
			ctx.takeScreenshot("12_zoom");
			ctx.runOnClient(mc -> McBenCosmeticsClient.forceZoom = false);

			// Fullbright bei Nacht
			sp.getServer().runCommand("time set 18000");
			sp.getServer().runCommand("tp @a ~ ~ ~ 180 60");
			ctx.runOnClient(mc -> CosmeticsConfig.get().fullbright = false);
			ctx.waitTicks(10);
			ctx.takeScreenshot("13_nacht_ohne_fullbright");
			ctx.runOnClient(mc -> CosmeticsConfig.get().fullbright = true);
			ctx.waitTicks(10);
			ctx.takeScreenshot("14_nacht_mit_fullbright");
			ctx.runOnClient(mc -> CosmeticsConfig.get().fullbright = false);
			sp.getServer().runCommand("time set 6000");
			sp.getServer().runCommand("tp @a ~ ~ ~ 180 10");

			// Low Shield
			sp.getServer().runCommand("item replace entity @a weapon.offhand with shield");
			ctx.runOnClient(mc -> CosmeticsConfig.get().lowShield = false);
			ctx.waitTicks(10);
			ctx.takeScreenshot("15_schild_normal");
			ctx.runOnClient(mc -> { CosmeticsConfig.get().lowShield = true; CosmeticsConfig.get().shieldOffset = 0.1f; });
			ctx.waitTicks(5);
			ctx.takeScreenshot("16_schild_low");

			// Low Fire
			sp.getServer().runCommand("effect give @a fire_resistance 60 0 true");
			sp.getServer().runOnServer(s -> s.getPlayerList().getPlayers().forEach(pl -> pl.igniteForSeconds(30)));
			ctx.runOnClient(mc -> CosmeticsConfig.get().lowFire = false);
			ctx.waitTicks(10);
			ctx.takeScreenshot("17_feuer_normal");
			ctx.runOnClient(mc -> { CosmeticsConfig.get().lowFire = true; CosmeticsConfig.get().fireOffset = 0.15f; });
			ctx.waitTicks(5);
			ctx.takeScreenshot("18_feuer_low");
		}
	}

	private static void shoot(ClientGameTestContext ctx, String wings, String theme, boolean halo, String name) {
		ctx.runOnClient(mc -> {
			CosmeticsConfig c = CosmeticsConfig.get();
			c.wings = wings; c.theme = theme; c.halo = halo; c.flap = false; c.brightness = 1.0f;
			mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
		});
		ctx.waitTicks(10);
		ctx.takeScreenshot(name + "_hinten");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.waitTicks(10);
		ctx.takeScreenshot(name + "_vorne");
	}
}
