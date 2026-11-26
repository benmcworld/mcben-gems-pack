package de.mcben.cosmetics.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.PlayerInfo;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayDeque;
import java.util.Deque;

/** Info-Anzeige (FPS, Ping, Koordinaten), Keystrokes mit CPS, Ruestungs-Anzeige. */
public final class HudOverlays {
	private HudOverlays() {}

	private static final int ACCENT = 0xFFE07BFF, TEXT = 0xFFFFFFFF, BOX = 0x90100A18, BOX_ON = 0xD0B44CFF;
	private static final Deque<Long> leftClicks = new ArrayDeque<>(), rightClicks = new ArrayDeque<>();
	private static boolean lastLeft, lastRight;

	public static void render(GuiGraphicsExtractor g) {
		Minecraft mc = Minecraft.getInstance();
		LocalPlayer p = mc.player;
		if (p == null) return;
		CosmeticsConfig c = CosmeticsConfig.get();
		trackClicks(mc);
		if (c.infoHud) info(g, mc, p);
		if (c.keystrokes) keystrokes(g, mc);
		if (c.armorHud) armor(g, mc, p);
		if (McBenCosmeticsClient.zoomAmount() > 1.001f) {
			String z = "Zoom " + Math.round(McBenCosmeticsClient.zoomAmount() * 10) / 10f + "x";
			g.centeredText(mc.font, z, g.guiWidth() / 2, 12, ACCENT);
		}
	}

	// ------------------------------------------------------------------ Info
	private static void info(GuiGraphicsExtractor g, Minecraft mc, LocalPlayer p) {
		Font f = mc.font;
		int ping = -1;
		if (mc.getConnection() != null) {
			PlayerInfo pi = mc.getConnection().getPlayerInfo(p.getUUID());
			if (pi != null) ping = pi.getLatency();
		}
		String[][] rows = {
			{"FPS", String.valueOf(mc.getFps())},
			{"Ping", ping < 0 ? "–" : ping + " ms"},
			{"XYZ", (int) Math.floor(p.getX()) + " / " + (int) Math.floor(p.getY()) + " / " + (int) Math.floor(p.getZ())},
			{"Richtung", direction(p.getYRot())},
		};
		int w = 0;
		for (String[] r : rows) w = Math.max(w, f.width(r[0] + "  " + r[1]));
		int x = 4, y = 4, h = rows.length * 11 + 5;
		g.fill(x, y, x + w + 10, y + h, BOX);
		g.fill(x, y, x + 2, y + h, BOX_ON);
		for (int i = 0; i < rows.length; i++) {
			g.text(f, rows[i][0], x + 6, y + 4 + i * 11, ACCENT);
			g.text(f, rows[i][1], x + 6 + f.width(rows[i][0] + "  "), y + 4 + i * 11, TEXT);
		}
	}

	private static String direction(float yaw) {
		String[] d = {"Süden", "Südwesten", "Westen", "Nordwesten", "Norden", "Nordosten", "Osten", "Südosten"};
		int i = Math.floorMod(Math.round(yaw / 45f), 8);
		return d[i];
	}

	// ------------------------------------------------------------------ Keystrokes
	private static void trackClicks(Minecraft mc) {
		long now = System.currentTimeMillis();
		boolean l = mc.options.keyAttack.isDown(), r = mc.options.keyUse.isDown();
		if (l && !lastLeft) leftClicks.add(now);
		if (r && !lastRight) rightClicks.add(now);
		lastLeft = l; lastRight = r;
		while (!leftClicks.isEmpty() && now - leftClicks.peekFirst() > 1000) leftClicks.pollFirst();
		while (!rightClicks.isEmpty() && now - rightClicks.peekFirst() > 1000) rightClicks.pollFirst();
	}

	private static void keystrokes(GuiGraphicsExtractor g, Minecraft mc) {
		int s = 20, gap = 2;
		int x0 = g.guiWidth() - (3 * s + 2 * gap) - 4, y0 = 4;
		key(g, mc, "W", mc.options.keyUp.isDown(), x0 + s + gap, y0, s, s);
		key(g, mc, "A", mc.options.keyLeft.isDown(), x0, y0 + s + gap, s, s);
		key(g, mc, "S", mc.options.keyDown.isDown(), x0 + s + gap, y0 + s + gap, s, s);
		key(g, mc, "D", mc.options.keyRight.isDown(), x0 + 2 * (s + gap), y0 + s + gap, s, s);
		int w2 = (3 * s + 2 * gap - gap) / 2;
		key(g, mc, "LMB " + leftClicks.size(), mc.options.keyAttack.isDown(), x0, y0 + 2 * (s + gap), w2, s);
		key(g, mc, "RMB " + rightClicks.size(), mc.options.keyUse.isDown(), x0 + w2 + gap, y0 + 2 * (s + gap), w2, s);
		key(g, mc, "———", mc.options.keyJump.isDown(), x0, y0 + 3 * (s + gap), 3 * s + 2 * gap, 12);
	}

	private static void key(GuiGraphicsExtractor g, Minecraft mc, String label, boolean down, int x, int y, int w, int h) {
		g.fill(x, y, x + w, y + h, down ? BOX_ON : BOX);
		g.centeredText(mc.font, label, x + w / 2, y + (h - 8) / 2, down ? 0xFF1A0B22 : TEXT);
	}

	// ------------------------------------------------------------------ Ruestung
	private static void armor(GuiGraphicsExtractor g, Minecraft mc, LocalPlayer p) {
		EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET, EquipmentSlot.MAINHAND};
		int x = g.guiWidth() - 22, y = g.guiHeight() - 4 - slots.length * 18;
		for (EquipmentSlot slot : slots) {
			ItemStack st = p.getItemBySlot(slot);
			if (!st.isEmpty()) {
				g.item(st, x, y);
				g.itemDecorations(mc.font, st, x, y);
				if (st.isDamageableItem()) {
					int left = st.getMaxDamage() - st.getDamageValue();
					String t = String.valueOf(left);
					float frac = left / (float) st.getMaxDamage();
					int col = frac > .5f ? 0xFF7DFF8A : frac > .2f ? 0xFFFFD34D : 0xFFFF5A5A;
					g.text(mc.font, t, x - mc.font.width(t) - 3, y + 5, col);
				}
			}
			y += 18;
		}
	}
}
