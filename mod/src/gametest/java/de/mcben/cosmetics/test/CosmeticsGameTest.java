package de.mcben.cosmetics.test;

import de.mcben.cosmetics.client.CosmeticsConfig;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Erstellt eine Welt und fotografiert die Cosmetics aus mehreren Blickwinkeln. */
public class CosmeticsGameTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext sp = ctx.worldBuilder().create()) {
			sp.getServer().runCommand("time set 6000");
			sp.getServer().runCommand("weather clear");
			sp.getServer().runCommand("tp @a ~ ~ ~ 180 10");
			sp.getConnection().waitForChunksRender();

			shoot(ctx, "galaxie", "lila", false, "1_galaxie_lila");
			shoot(ctx, "engel", "lila", true, "2_engel_heiligenschein");
			shoot(ctx, "galaxie", "gruen", true, "3_galaxie_gruen");
			shoot(ctx, "galaxie", "dark", false, "4_galaxie_dark");

			// Plushie-Totem: in der Hand, im Inventar, beim Ausloesen
			sp.getServer().runCommand("give @a totem_of_undying");
			ctx.runOnClient(mc -> { CosmeticsConfig.get().wings = "aus"; CosmeticsConfig.get().halo = false; });
			ctx.waitTicks(10);
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
			ctx.waitTicks(30);
			ctx.setScreen(() -> new de.mcben.cosmetics.client.CosmeticsScreen(null));
			ctx.waitTicks(5);
			ctx.takeScreenshot("9_menue");
			ctx.setScreen(() -> null);
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
