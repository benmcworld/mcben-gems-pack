package de.mcben.cosmetics.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.PlayerInfo;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;

import java.time.LocalTime;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
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
		int y = 4;
		if (c.infoHud) y = info(g, mc, p, c) + 4;
		if (c.keystrokes) { keystrokes(g, mc, y); y += 3 * 22 + 12 + 6; }
		if (c.effectsHud) effects(g, mc, p, 4);
		if (c.armorHud) armor(g, mc, p);
		if (McBenCosmeticsClient.zoomAmount() > 1.001f) {
			String z = "Zoom " + Math.round(McBenCosmeticsClient.zoomAmount() * 10) / 10f + "x";
			g.centeredText(mc.font, z, g.guiWidth() / 2, 12, ACCENT);
		}
	}

	// ------------------------------------------------------------------ Info
	private static int info(GuiGraphicsExtractor g, Minecraft mc, LocalPlayer p, CosmeticsConfig c) {
		Font f = mc.font;
		int ping = -1;
		if (mc.getConnection() != null) {
			PlayerInfo pi = mc.getConnection().getPlayerInfo(p.getUUID());
			if (pi != null) ping = pi.getLatency();
		}
		List<String[]> rows = new ArrayList<>();
		rows.add(new String[]{"FPS", String.valueOf(mc.getFps())});
		rows.add(new String[]{"Ping", ping < 0 ? "–" : ping + " ms"});
		rows.add(new String[]{"XYZ", (int) Math.floor(p.getX()) + " / " + (int) Math.floor(p.getY()) + " / " + (int) Math.floor(p.getZ())});
		rows.add(new String[]{"Richtung", direction(p.getYRot())});
		if (c.clockHud) {
			LocalTime now = LocalTime.now();
			rows.add(new String[]{"Uhr", String.format("%02d:%02d", now.getHour(), now.getMinute())});
			if (mc.level != null) {
				long t = Math.floorMod(mc.level.getOverworldClockTime(), 24000L);
				int h = (int) ((t / 1000 + 6) % 24), m = (int) (t % 1000 * 60 / 1000);
				rows.add(new String[]{"MC-Zeit", String.format("%02d:%02d", h, m) + (t >= 13000 && t < 23000 ? "  Nacht" : "")});
			}
		}
		if (c.deathCoords && c.lastDeath != null && !c.lastDeath.isEmpty()) rows.add(new String[]{"Tod", c.lastDeath});
		int w = 0;
		for (String[] r : rows) w = Math.max(w, f.width(r[0] + "  " + r[1]));
		int x = 4, y = 4, h = rows.size() * 11 + 5;
		g.fill(x, y, x + w + 10, y + h, BOX);
		g.fill(x, y, x + 2, y + h, BOX_ON);
		for (int i = 0; i < rows.size(); i++) {
			String[] r = rows.get(i);
			g.text(f, r[0], x + 6, y + 4 + i * 11, ACCENT);
			g.text(f, r[1], x + 6 + f.width(r[0] + "  "), y + 4 + i * 11, TEXT);
		}
		return y + h;
	}

	// ------------------------------------------------------------------ Trank-Effekte
	private static void effects(GuiGraphicsExtractor g, Minecraft mc, LocalPlayer p, int y) {
		Font f = mc.font;
		for (MobEffectInstance e : p.getActiveEffects()) {
			String name = e.getEffect().value().getDisplayName().getString();
			if (e.getAmplifier() > 0) name += " " + roman(e.getAmplifier() + 1);
			String time;
			if (e.isInfiniteDuration()) time = "∞";
			else { int sec = e.getDuration() / 20; time = sec / 60 + ":" + String.format("%02d", sec % 60); }
			int col = 0xFF000000 | e.getEffect().value().getColor();
			int w = f.width(name + "  " + time) + 10, x = g.guiWidth() - w - 4;
			g.fill(x, y, x + w, y + 13, BOX);
			g.fill(x + w - 2, y, x + w, y + 13, col);
			g.text(f, name, x + 4, y + 3, TEXT);
			g.text(f, time, x + 4 + f.width(name + "  "), y + 3, e.endsWithin(200) ? 0xFFFF5A5A : ACCENT);
			y += 15;
		}
	}

	private static String roman(int n) {
		String[] r = {"", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"};
		return n < r.length ? r[n] : String.valueOf(n);
	}

	/** Merkt sich beim Sterben die Koordinaten (wird jeden Tick aufgerufen). */
	private static boolean wasDead;
	public static void trackDeath(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null) { wasDead = false; return; }
		boolean dead = p.isDeadOrDying();
		if (dead && !wasDead) {
			CosmeticsConfig c = CosmeticsConfig.get();
			String dim = p.level().dimension().identifier().getPath().replace("the_", "");
			c.lastDeath = (int) Math.floor(p.getX()) + " " + (int) Math.floor(p.getY()) + " " + (int) Math.floor(p.getZ()) + " (" + dim + ")";
			c.save();
		}
		wasDead = dead;
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

	private static void keystrokes(GuiGraphicsExtractor g, Minecraft mc, int y0) {
		int s = 20, gap = 2;
		int x0 = 4;
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
				if (slot == EquipmentSlot.MAINHAND && CosmeticsConfig.get().itemCounter && st.isStackable()) {
					int total = 0;
					for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
						ItemStack o = p.getInventory().getItem(i);
						if (ItemStack.isSameItemSameComponents(o, st)) total += o.getCount();
					}
					String t = "×" + total;
					g.text(mc.font, t, x - mc.font.width(t) - 3, y + 5, ACCENT);
				}
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
