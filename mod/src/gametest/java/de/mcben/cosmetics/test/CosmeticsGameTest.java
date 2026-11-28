package de.mcben.cosmetics.test;

import de.mcben.cosmetics.client.CosmeticsConfig;
import de.mcben.cosmetics.client.HudEditorScreen;
import de.mcben.cosmetics.client.HudLayout;
import de.mcben.cosmetics.client.McBenScreen;
import de.mcben.cosmetics.client.TotemGhosts;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

import java.util.LinkedHashMap;

/** Erstellt eine Welt und fotografiert Menue, HUD-Editor, HUD-Varianten und Totem-Minimods. */
public class CosmeticsGameTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext sp = ctx.worldBuilder().create()) {
			sp.getServer().runCommand("time set 6000");
			sp.getServer().runCommand("weather clear");
			sp.getServer().runCommand("tp @a ~ ~ ~ 180 10");
			sp.getConnection().waitForChunksRender();
			ctx.runOnClient(mc -> {
				CosmeticsConfig c = CosmeticsConfig.get();
				c.hud = new LinkedHashMap<>();
				c.wings = "galaxie"; c.theme = "lila"; c.flap = false; c.halo = false;
				c.lastDeath = "120 64 -340 (overworld)";
			});

			// Ausruestung + Effekte, damit alle Anzeigen etwas zeigen
			sp.getServer().runCommand("item replace entity @a armor.head with diamond_helmet");
			sp.getServer().runCommand("item replace entity @a armor.chest with diamond_chestplate");
			sp.getServer().runCommand("item replace entity @a armor.legs with iron_leggings");
			sp.getServer().runCommand("item replace entity @a armor.feet with iron_boots");
			sp.getServer().runCommand("item replace entity @a weapon.mainhand with diamond_sword");
			sp.getServer().runCommand("give @a totem_of_undying 3");
			sp.getServer().runCommand("effect give @a speed 95 1");
			sp.getServer().runCommand("effect give @a strength 8 0");

			ctx.waitTicks(20);
			ctx.runOnClient(mc -> { mc.gui.toastManager().clear(); mc.gui.hud.getChat().clearMessages(false); });

			// 1) Menue-Tabs
			for (int i = 0; i < McBenScreen.TABS.length; i++) {
				int tab = i;
				ctx.setScreen(() -> new McBenScreen(null, tab));
				ctx.waitTicks(4);
				ctx.takeScreenshot("1_menue_" + i + "_" + McBenScreen.TABS[i].toLowerCase());
			}
			ctx.setScreen(() -> null);

			// 2) Standard-HUD
			ctx.waitTicks(5);
			ctx.takeScreenshot("2_hud_standard");

			// 3) HUD-Editor mit ausgewaehlter Anzeige
			ctx.setScreen(() -> new HudEditorScreen(null));
			ctx.waitTicks(4);
			ctx.takeScreenshot("3_hud_editor_leer");
			ctx.setScreen(() -> new HudEditorScreen(null).select("fps"));
			ctx.waitTicks(4);
			ctx.takeScreenshot("3_hud_editor");
			ctx.setScreen(() -> null);

			// 4) Nur Zahlen: Hintergrund unsichtbar, keine Beschriftung, Clean-Schrift
			ctx.runOnClient(mc -> {
				CosmeticsConfig c = CosmeticsConfig.get();
				c.font = "clean";
				for (HudLayout.Element e : HudLayout.ELEMENTS) { c.pos(e).bg = 0f; c.pos(e).label = false; }
			});
			ctx.waitTicks(4);
			ctx.takeScreenshot("4_hud_nur_zahlen_clean");

			// 5) Alle Extras an, Rahmen-Stil, Mono-Schrift, Cyan, groesser verschoben
			ctx.runOnClient(mc -> {
				CosmeticsConfig c = CosmeticsConfig.get();
				c.hud = new LinkedHashMap<>();
				c.font = "clean_bold"; c.accent = "cyan"; c.boxStyle = "rahmen";
				for (HudLayout.Element e : HudLayout.ELEMENTS) c.pos(e).on = true;
				c.pos(HudLayout.byId("coords")).scale = 1.5f;
				c.pos(HudLayout.byId("keys")).bg = 0.25f;
			});
			ctx.waitTicks(4);
			ctx.takeScreenshot("5_hud_alle_extras");
			ctx.runOnClient(mc -> {
				CosmeticsConfig c = CosmeticsConfig.get();
				c.hud = new LinkedHashMap<>();
				c.font = "minecraft"; c.accent = "lila"; c.boxStyle = "streifen";
			});

			// 6) Totem vorne halten
			sp.getServer().runCommand("item replace entity @a weapon.mainhand with totem_of_undying");
			ctx.runOnClient(mc -> { CosmeticsConfig.get().totemForward = false; mc.options.setCameraType(CameraType.FIRST_PERSON); });
			ctx.waitTicks(10);
			ctx.takeScreenshot("6_totem_normal");
			ctx.runOnClient(mc -> CosmeticsConfig.get().totemForward = true);
			ctx.waitTicks(5);
			ctx.takeScreenshot("7_totem_vorne");

			// 7) Pop-Umriss (Test-Umriss vor dem Spieler)
			ctx.runOnClient(mc -> { CosmeticsConfig c = CosmeticsConfig.get(); c.ghostTime = 3f; c.ghostColor = "gold"; TotemGhosts.spawnTestGhost(); });
			ctx.waitTicks(8);
			ctx.takeScreenshot("8_pop_umriss_gold");
			ctx.runOnClient(mc -> { CosmeticsConfig.get().ghostColor = "akzent"; TotemGhosts.spawnTestGhost(); });
			ctx.waitTicks(8);
			ctx.takeScreenshot("9_pop_umriss_lila");

			// 8) Echter Pop: Survival, Schaden -> Totem loest aus, von hinten fotografiert
			ctx.runOnClient(mc -> CosmeticsConfig.get().ghostColor = "gold");
			sp.getServer().runCommand("gamemode survival @a");
			sp.getServer().runCommand("item replace entity @a weapon.offhand with totem_of_undying");
			ctx.waitTicks(5);
			sp.getServer().runCommand("damage @p 100 minecraft:generic");
			sp.getServer().runCommand("tp @p ~ ~ ~3.5 180 10");
			ctx.waitTicks(6);
			ctx.takeScreenshot("10_echter_pop");
		}
	}
}
