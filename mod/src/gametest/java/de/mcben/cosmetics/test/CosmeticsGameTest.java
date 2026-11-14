package de.mcben.cosmetics.test;

import de.mcben.cosmetics.client.CosmeticsConfig;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

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
		}
	}

	private static void shoot(ClientGameTestContext ctx, String wings, String theme, boolean halo, String name) {
		ctx.runOnClient(mc -> {
			CosmeticsConfig c = CosmeticsConfig.get();
			c.wings = wings; c.theme = theme; c.halo = halo; c.flap = false; c.brightness = 1.0f;
			mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
			mc.options.hideGui = true;
		});
		ctx.waitTicks(10);
		ctx.takeScreenshot(name + "_hinten");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.waitTicks(10);
		ctx.takeScreenshot(name + "_vorne");
	}
}
