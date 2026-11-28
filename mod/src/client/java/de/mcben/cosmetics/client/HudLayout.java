package de.mcben.cosmetics.client;

import de.mcben.cosmetics.client.CosmeticsConfig.HudPos;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.PlayerInfo;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FontDescription;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.Identifier;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.phys.Vec3;

import java.time.LocalTime;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Alle HUD-Anzeigen. Jede Anzeige ist einzeln an/aus, frei verschiebbar, skalierbar,
 * mit eigener Hintergrund-Durchsicht, Schatten, Beschriftung und Farbe.
 */
public final class HudLayout {
	private HudLayout() {}

	public static final int BG_RGB = 0x0C0814, TEXT = 0xFFFFFFFF, DIM = 0xFFB9B0C8;
	public static final int GOOD = 0xFF7DFF8A, MID = 0xFFFFD34D, BAD = 0xFFFF5A5A;

	/** Zuletzt gezeichnete Rechtecke (x, y, w, h in GUI-Pixeln) fuer den Editor. */
	public static final Map<String, float[]> RECTS = new HashMap<>();

	// ================================================================== Kontext
	public static final class Ctx {
		public GuiGraphicsExtractor g;
		public Minecraft mc;
		public LocalPlayer p;
		public Font font;
		public HudPos pos;
		public int accent;
		public boolean preview, right;
		FontDescription fd;

		public Component c(String s) {
			MutableComponent m = Component.literal(s);
			return fd == null ? m : m.withStyle(st -> st.withFont(fd));
		}
		public int w(String s) { return font.width(c(s)); }
		public void text(String s, int x, int y, int col) { g.text(font, c(s), x, y, col, pos.shadow); }
		public int bgAlpha() { return Math.round(Math.max(0f, Math.min(1f, pos.bg)) * 255); }
	}

	public static FontDescription fontDescription(String id) {
		return switch (id) {
			case "clean", "clean_bold", "mono" -> new FontDescription.Resource(Identifier.fromNamespaceAndPath(McBenCosmeticsClient.MOD_ID, id));
			case "uniform" -> new FontDescription.Resource(Identifier.withDefaultNamespace("uniform"));
			default -> null;
		};
	}

	/** Text in der gewaehlten Schrift (auch fuer Menues). */
	public static Component styled(String s) {
		FontDescription fd = fontDescription(CosmeticsConfig.get().font);
		MutableComponent m = Component.literal(s);
		return fd == null ? m : m.withStyle(st -> st.withFont(fd));
	}

	// ================================================================== Elemente
	public abstract static class Element {
		public final String id, name;
		private final boolean defOn;
		private final int dax, day;
		private final float dx, dy;

		Element(String id, String name, boolean on, int ax, int ay, float x, float y) {
			this.id = id; this.name = name; this.defOn = on; this.dax = ax; this.day = ay; this.dx = x; this.dy = y;
		}

		public HudPos defaults() {
			return new HudPos(defOn, dax, day, dx, dy);
		}

		/** false = gerade nichts anzuzeigen (z. B. keine Effekte). */
		boolean visible(Ctx c) { return true; }
		abstract int[] size(Ctx c);
		abstract void draw(Ctx c, int w, int h);
		public boolean hasLabel() { return false; }
	}

	/** Einzeilige Anzeige: Beschriftung + Wert. */
	abstract static class TextEl extends Element {
		TextEl(String id, String name, boolean on, int ax, int ay, float x, float y) { super(id, name, on, ax, ay, x, y); }
		abstract String label();
		/** {Wert, Kurzform ohne Beschriftung}; null = nichts anzeigen. */
		abstract String[] value(Ctx c);
		int valueColor(Ctx c) { return TEXT; }
		@Override public boolean hasLabel() { return true; }

		@Override boolean visible(Ctx c) { return value(c) != null; }

		@Override int[] size(Ctx c) {
			String[] v = value(c);
			if (v == null) v = new String[]{"–", "–"};
			int w = c.pos.label ? c.w(label()) + 5 + c.w(v[0]) : c.w(v[1]);
			return new int[]{w + 10, 13};
		}

		@Override void draw(Ctx c, int w, int h) {
			String[] v = value(c);
			if (v == null) v = new String[]{"–", "–"};
			box(c, 0, 0, w, h);
			int x = 5;
			if (c.pos.label) {
				c.text(label(), x, 3, c.accent);
				c.text(v[0], x + c.w(label()) + 5, 3, valueColor(c));
			} else {
				c.text(v[1], x, 3, valueColor(c));
			}
		}
	}

	public static final List<Element> ELEMENTS = new ArrayList<>();
	private static final Map<String, Element> BY_ID = new LinkedHashMap<>();

	public static Element byId(String id) { return BY_ID.get(id); }

	private static void add(Element e) { ELEMENTS.add(e); BY_ID.put(e.id, e); }

	private static float row(int i) { return 4 + i * 14; }

	static {
		add(new TextEl("fps", "FPS", true, 0, 0, 4, row(0)) {
			String label() { return "FPS"; }
			String[] value(Ctx c) { int f = c.mc.getFps(); return new String[]{"" + f, f + " fps"}; }
			int valueColor(Ctx c) { int f = c.mc.getFps(); return f >= 60 ? TEXT : f >= 30 ? MID : BAD; }
		});
		add(new TextEl("ping", "Ping", true, 0, 0, 4, row(1)) {
			String label() { return "Ping"; }
			String[] value(Ctx c) { int p = ping(c); String s = p < 0 ? "–" : p + " ms"; return new String[]{s, s}; }
			int valueColor(Ctx c) { int p = ping(c); return p < 0 || p < 80 ? TEXT : p < 160 ? MID : BAD; }
		});
		add(new TextEl("coords", "Koordinaten", true, 0, 0, 4, row(2)) {
			String label() { return "XYZ"; }
			String[] value(Ctx c) {
				String s = (int) Math.floor(c.p.getX()) + " / " + (int) Math.floor(c.p.getY()) + " / " + (int) Math.floor(c.p.getZ());
				return new String[]{s, s};
			}
		});
		add(new TextEl("direction", "Richtung", true, 0, 0, 4, row(3)) {
			String label() { return "Richtung"; }
			String[] value(Ctx c) {
				int i = Math.floorMod(Math.round(c.p.getYRot() / 45f), 8);
				String[] l = {"Süden (+Z)", "Südwesten", "Westen (-X)", "Nordwesten", "Norden (-Z)", "Nordosten", "Osten (+X)", "Südosten"};
				String[] s = {"S", "SW", "W", "NW", "N", "NO", "O", "SO"};
				return new String[]{l[i], s[i]};
			}
		});
		add(new TextEl("clock", "Uhrzeit", true, 0, 0, 4, row(4)) {
			String label() { return "Uhr"; }
			String[] value(Ctx c) { LocalTime n = LocalTime.now(); String s = String.format("%02d:%02d", n.getHour(), n.getMinute()); return new String[]{s, s}; }
		});
		add(new TextEl("mctime", "MC-Zeit + Tag", true, 0, 0, 4, row(5)) {
			String label() { return "Tag"; }
			String[] value(Ctx c) {
				if (c.mc.level == null) return null;
				long total = c.mc.level.getOverworldClockTime();
				long t = Math.floorMod(total, 24000L);
				int h = (int) ((t / 1000 + 6) % 24), m = (int) (t % 1000 * 60 / 1000);
				String time = String.format("%02d:%02d", h, m) + (t >= 13000 && t < 23000 ? " ☾" : " ☀");
				return new String[]{(total / 24000 + 1) + "  " + time, time};
			}
		});
		add(new TextEl("death", "Letzter Tod", true, 0, 0, 4, row(6)) {
			String label() { return "Tod"; }
			String[] value(Ctx c) {
				String d = CosmeticsConfig.get().lastDeath;
				if (d == null || d.isEmpty()) return c.preview ? new String[]{"12 64 -30 (overworld)", "12 64 -30"} : null;
				return new String[]{d, d};
			}
			int valueColor(Ctx c) { return 0xFFFF9C9C; }
		});
		add(new Element("keys", "Keystrokes", true, 0, 0, 4, 106) {
			int[] size(Ctx c) { return new int[]{64, 78}; }
			void draw(Ctx c, int w, int h) { keystrokes(c); }
		});
		add(new Element("effects", "Effekte", true, 2, 0, 4, 4) {
			boolean visible(Ctx c) { return !c.p.getActiveEffects().isEmpty(); }
			int[] size(Ctx c) {
				List<String[]> rows = effectRows(c);
				int w = 0;
				for (String[] r : rows) w = Math.max(w, c.w(r[0] + "  " + r[1]) + 12);
				return new int[]{Math.max(w, 40), Math.max(1, rows.size()) * 15 - 2};
			}
			void draw(Ctx c, int w, int h) {
				List<String[]> rows = effectRows(c);
				int y = 0;
				for (String[] r : rows) {
					int rw = c.w(r[0] + "  " + r[1]) + 12;
					int x = c.right ? w - rw : 0;
					box(c, x, y, rw, 13);
					int col = Integer.parseUnsignedInt(r[2]);
					if (c.pos.bg > 0.01f) c.g.fill(c.right ? x + rw - 2 : x, y + 1, c.right ? x + rw : x + 2, y + 12, col);
					else c.g.fill(c.right ? x + rw - 3 : x + 1, y + 5, c.right ? x + rw - 1 : x + 3, y + 7, col);
					c.text(r[0], x + 6, y + 3, TEXT);
					c.text(r[1], x + 6 + c.w(r[0] + "  "), y + 3, "1".equals(r[3]) ? BAD : c.accent);
					y += 15;
				}
			}
		});
		add(new Element("armor", "Rüstung", true, 2, 2, 4, 4) {
			int[] size(Ctx c) {
				int tw = 0;
				for (ItemStack st : armorStacks(c)) tw = Math.max(tw, c.w(durText(st, c)));
				return new int[]{18 + (tw > 0 ? tw + 4 : 0), 5 * 18 - 2};
			}
			void draw(Ctx c, int w, int h) {
				if (c.pos.bg > 0.01f) box(c, 0, 0, w, h);
				int y = 0;
				for (ItemStack st : armorStacks(c)) {
					int ix = c.right ? w - 17 : 1;
					if (!st.isEmpty()) {
						c.g.item(st, ix, y);
						c.g.itemDecorations(c.font, st, ix, y);
						String t = durText(st, c);
						if (!t.isEmpty()) {
							int tx = c.right ? ix - 3 - c.w(t) : ix + 19;
							c.text(t, tx, y + 5, durColor(st, c));
						}
					}
					y += 18;
				}
			}
		});
		add(new Element("totems", "Totems", true, 1, 2, 120, 3) {
			int[] size(Ctx c) { return new int[]{22 + c.w(totemText(c)), 18}; }
			void draw(Ctx c, int w, int h) {
				box(c, 0, 0, w, h);
				c.g.item(new ItemStack(Items.TOTEM_OF_UNDYING), 2, 1);
				int n = countItem(c, Items.TOTEM_OF_UNDYING);
				c.text(totemText(c), 20, 5, n == 0 ? BAD : n == 1 ? MID : TEXT);
			}
		});
		add(new TextEl("target", "Gegner-HP", false, 1, 1, 0, 26) {
			String label() { return "♥"; }
			String[] value(Ctx c) {
				LivingEntity t = target(c);
				if (t == null) return c.preview ? new String[]{"BastiGHG 14.5", "14.5"} : null;
				float hp = t.getHealth() + t.getAbsorptionAmount();
				String s = String.format("%.1f", hp);
				return new String[]{t.getName().getString() + " " + s, s};
			}
			int valueColor(Ctx c) {
				LivingEntity t = target(c);
				if (t == null) return TEXT;
				float f = t.getHealth() / t.getMaxHealth();
				return f > .5f ? GOOD : f > .25f ? MID : BAD;
			}
		});
		add(new TextEl("cps", "CPS", false, 2, 1, 4, -60) {
			String label() { return "CPS"; }
			String[] value(Ctx c) { String s = leftClicks.size() + " | " + rightClicks.size(); return new String[]{s, s + " cps"}; }
		});
		add(new TextEl("reach", "Reach", false, 2, 1, 4, -46) {
			String label() { return "Reach"; }
			String[] value(Ctx c) { String s = lastReach < 0 ? "–" : String.format("%.2f", lastReach); return new String[]{s, s + " m"}; }
		});
		add(new TextEl("combo", "Combo", false, 2, 1, 4, -32) {
			String label() { return "Combo"; }
			String[] value(Ctx c) { String s = combo + "x"; return new String[]{s, s}; }
			int valueColor(Ctx c) { return combo >= 3 ? c.accent : TEXT; }
		});
		add(new TextEl("speed", "Tempo", false, 2, 1, 4, -18) {
			String label() { return "Tempo"; }
			String[] value(Ctx c) { String s = String.format("%.1f m/s", speed); return new String[]{s, s}; }
		});
		add(new TextEl("biome", "Biom", false, 2, 1, 4, -4) {
			String label() { return "Biom"; }
			String[] value(Ctx c) {
				if (c.mc.level == null) return null;
				String s = c.mc.level.getBiome(c.p.blockPosition()).unwrapKey()
					.map(k -> Component.translatable(k.identifier().toLanguageKey("biome")).getString()).orElse("?");
				return new String[]{s, s};
			}
		});
		add(new TextEl("light", "Lichtlevel", false, 2, 1, 4, 10) {
			String label() { return "Licht"; }
			String[] value(Ctx c) {
				if (c.mc.level == null) return null;
				String s = "" + c.mc.level.getBrightness(LightLayer.BLOCK, c.p.blockPosition());
				return new String[]{s, "☀ " + s};
			}
			int valueColor(Ctx c) { return c.mc.level != null && c.mc.level.getBrightness(LightLayer.BLOCK, c.p.blockPosition()) == 0 ? BAD : TEXT; }
		});
		add(new TextEl("nether", "Nether-XZ", false, 2, 1, 4, 24) {
			String label() { return inNether(c0()) ? "Oberwelt" : "Nether"; }
			String[] value(Ctx c) {
				double f = inNether(c) ? 8 : 1 / 8d;
				String s = (int) Math.floor(c.p.getX() * f) + " / " + (int) Math.floor(c.p.getZ() * f);
				return new String[]{s, s};
			}
		});
		add(new TextEl("memory", "RAM", false, 2, 1, 4, 38) {
			String label() { return "RAM"; }
			String[] value(Ctx c) {
				Runtime r = Runtime.getRuntime();
				long used = (r.totalMemory() - r.freeMemory()) >> 20, max = r.maxMemory() >> 20;
				String s = used * 100 / Math.max(1, max) + " %  " + used + "/" + max + " MB";
				return new String[]{s, used * 100 / Math.max(1, max) + " %"};
			}
		});
	}

	// ================================================================== Zeichnen
	public static void render(GuiGraphicsExtractor g, boolean preview) {
		Minecraft mc = Minecraft.getInstance();
		LocalPlayer p = mc.player;
		if (p == null) return;
		CosmeticsConfig cfg = CosmeticsConfig.get();
		Ctx c = CTX;
		c.g = g; c.mc = mc; c.p = p; c.font = mc.font; c.preview = preview;
		c.fd = fontDescription(cfg.font);
		int sw = g.guiWidth(), sh = g.guiHeight();
		RECTS.clear();
		for (Element e : ELEMENTS) {
			HudPos pos = cfg.pos(e);
			if (!pos.on && !preview) continue;
			c.pos = pos;
			c.accent = "auto".equals(pos.color) ? cfg.accent() : CosmeticsConfig.accentColor(pos.color);
			c.right = pos.ax == 2;
			if (!preview && !e.visible(c)) continue;
			int[] s = e.size(c);
			float sc = Math.max(0.3f, pos.scale);
			float w = s[0] * sc, h = s[1] * sc;
			float[] xy = place(pos, w, h, sw, sh);
			RECTS.put(e.id, new float[]{xy[0], xy[1], w, h});
			g.pose().pushMatrix();
			g.pose().translate(xy[0], xy[1]);
			g.pose().scale(sc, sc);
			e.draw(c, s[0], s[1]);
			g.pose().popMatrix();
		}
		if (!preview && McBenCosmeticsClient.zoomAmount() > 1.001f) {
			String z = "Zoom " + Math.round(McBenCosmeticsClient.zoomAmount() * 10) / 10f + "x";
			g.centeredText(mc.font, styled(z), sw / 2, 12, cfg.accent());
		}
	}

	private static final Ctx CTX = new Ctx();
	private static Ctx c0() { return CTX; }

	/** Bildschirmposition (oben links) aus Anker + Abstand. */
	public static float[] place(HudPos pos, float w, float h, int sw, int sh) {
		float x = switch (pos.ax) { case 1 -> sw / 2f - w / 2f + pos.x; case 2 -> sw - w - pos.x; default -> pos.x; };
		float y = switch (pos.ay) { case 1 -> sh / 2f - h / 2f + pos.y; case 2 -> sh - h - pos.y; default -> pos.y; };
		x = Math.max(0, Math.min(sw - w, x));
		y = Math.max(0, Math.min(sh - h, y));
		return new float[]{x, y};
	}

	/** Umgekehrt: aus einer Bildschirmposition Anker + Abstand berechnen (nach dem Ziehen). */
	public static void anchor(HudPos pos, float px, float py, float w, float h, int sw, int sh) {
		float cx = px + w / 2f, cy = py + h / 2f;
		pos.ax = cx < sw / 3f ? 0 : cx > sw * 2f / 3f ? 2 : 1;
		pos.ay = cy < sh / 3f ? 0 : cy > sh * 2f / 3f ? 2 : 1;
		pos.x = switch (pos.ax) { case 1 -> px + w / 2f - sw / 2f; case 2 -> sw - w - px; default -> px; };
		pos.y = switch (pos.ay) { case 1 -> py + h / 2f - sh / 2f; case 2 -> sh - h - py; default -> py; };
	}

	/** Hintergrund-Kaestchen im gewaehlten Stil; bei 0 % Durchsicht wird gar nichts gezeichnet. */
	static void box(Ctx c, int x, int y, int w, int h) {
		int a = c.bgAlpha();
		if (a <= 2) return;
		GuiGraphicsExtractor g = c.g;
		int col = a << 24 | BG_RGB;
		g.fill(x + 1, y, x + w - 1, y + h, col);
		g.fill(x, y + 1, x + 1, y + h - 1, col);
		g.fill(x + w - 1, y + 1, x + w, y + h - 1, col);
		int acc = Math.min(255, a + 70) << 24 | (c.accent & 0xFFFFFF);
		switch (CosmeticsConfig.get().boxStyle) {
			case "rahmen" -> g.outline(x, y, w, h, acc);
			case "unterstrich" -> g.fill(x + 1, y + h - 1, x + w - 1, y + h, acc);
			case "schlicht" -> {}
			default -> {
				if (c.right) g.fill(x + w - 2, y + 1, x + w, y + h - 1, acc);
				else g.fill(x, y + 1, x + 2, y + h - 1, acc);
			}
		}
	}

	// ================================================================== Daten
	private static final Deque<Long> leftClicks = new ArrayDeque<>(), rightClicks = new ArrayDeque<>();
	private static boolean lastLeft, lastRight;
	static float speed;
	private static Vec3 lastPos;
	static double lastReach = -1;
	static int combo;
	private static long lastHitTime;
	private static int lastHurtTime;
	private static LivingEntity lastTarget;
	private static long lastTargetTime;

	/** Jeden Client-Tick. */
	public static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null) { lastPos = null; return; }
		Vec3 now = p.position();
		if (lastPos != null) {
			double d = Math.hypot(now.x - lastPos.x, now.z - lastPos.z) * 20;
			speed = (float) (speed * 0.7 + d * 0.3);
		}
		lastPos = now;
		if (p.hurtTime > lastHurtTime) combo = 0;           // selbst getroffen -> Combo vorbei
		lastHurtTime = p.hurtTime;
		if (System.currentTimeMillis() - lastHitTime > 2500) combo = 0;
	}

	/** Jeder eigene Schlag auf ein Wesen. */
	public static void onAttack(LocalPlayer p, Entity target) {
		Vec3 eye = p.getEyePosition();
		lastReach = Math.sqrt(target.getBoundingBox().distanceToSqr(eye));
		combo++;
		lastHitTime = System.currentTimeMillis();
		if (target instanceof LivingEntity le) { lastTarget = le; lastTargetTime = lastHitTime; }
	}

	private static LivingEntity target(Ctx c) {
		if (c.mc.crosshairPickEntity instanceof LivingEntity le) return le;
		if (lastTarget != null && lastTarget.isAlive() && System.currentTimeMillis() - lastTargetTime < 4000) return lastTarget;
		return null;
	}

	public static void trackClicks(Minecraft mc) {
		long now = System.currentTimeMillis();
		boolean l = mc.options.keyAttack.isDown(), r = mc.options.keyUse.isDown();
		if (l && !lastLeft) leftClicks.add(now);
		if (r && !lastRight) rightClicks.add(now);
		lastLeft = l; lastRight = r;
		while (!leftClicks.isEmpty() && now - leftClicks.peekFirst() > 1000) leftClicks.pollFirst();
		while (!rightClicks.isEmpty() && now - rightClicks.peekFirst() > 1000) rightClicks.pollFirst();
	}

	private static int ping(Ctx c) {
		if (c.mc.getConnection() == null) return -1;
		PlayerInfo pi = c.mc.getConnection().getPlayerInfo(c.p.getUUID());
		return pi == null ? -1 : pi.getLatency();
	}

	private static boolean inNether(Ctx c) {
		return c.p != null && c.p.level().dimension().identifier().getPath().equals("the_nether");
	}

	private static String totemText(Ctx c) {
		int n = countItem(c, Items.TOTEM_OF_UNDYING);
		int pops = TotemGhosts.ownPops();
		return "×" + n + (pops > 0 ? "  Pops " + pops : "");
	}

	private static int countItem(Ctx c, net.minecraft.world.item.Item item) {
		int total = 0;
		for (int i = 0; i < c.p.getInventory().getContainerSize(); i++) {
			ItemStack o = c.p.getInventory().getItem(i);
			if (o.is(item)) total += o.getCount();
		}
		if (c.preview && total == 0) return 3;
		return total;
	}

	private static List<String[]> effectRows(Ctx c) {
		List<String[]> rows = new ArrayList<>();
		for (MobEffectInstance e : c.p.getActiveEffects()) {
			String name = e.getEffect().value().getDisplayName().getString();
			if (e.getAmplifier() > 0) name += " " + roman(e.getAmplifier() + 1);
			String time;
			if (e.isInfiniteDuration()) time = "∞";
			else { int sec = e.getDuration() / 20; time = sec / 60 + ":" + String.format("%02d", sec % 60); }
			rows.add(new String[]{name, time, Integer.toUnsignedString(0xFF000000 | e.getEffect().value().getColor()), e.endsWithin(200) ? "1" : "0"});
		}
		if (rows.isEmpty() && c.preview) {
			rows.add(new String[]{"Stärke II", "1:30", Integer.toUnsignedString(0xFFFFC700), "0"});
			rows.add(new String[]{"Schnelligkeit", "2:45", Integer.toUnsignedString(0xFF33EBFF), "0"});
			rows.add(new String[]{"Feuerresistenz", "0:08", Integer.toUnsignedString(0xFFFF9900), "1"});
		}
		return rows;
	}

	private static String roman(int n) {
		String[] r = {"", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"};
		return n < r.length ? r[n] : String.valueOf(n);
	}

	private static List<ItemStack> armorStacks(Ctx c) {
		EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET, EquipmentSlot.MAINHAND};
		List<ItemStack> l = new ArrayList<>();
		boolean any = false;
		for (EquipmentSlot s : slots) { ItemStack st = c.p.getItemBySlot(s); l.add(st); any |= !st.isEmpty(); }
		if (!any && c.preview) {
			return List.of(new ItemStack(Items.DIAMOND_HELMET), new ItemStack(Items.DIAMOND_CHESTPLATE), new ItemStack(Items.DIAMOND_LEGGINGS),
				new ItemStack(Items.DIAMOND_BOOTS), new ItemStack(Items.DIAMOND_SWORD));
		}
		return l;
	}

	private static String durText(ItemStack st, Ctx c) {
		if (st.isEmpty()) return "";
		if (st.isDamageableItem()) return String.valueOf(st.getMaxDamage() - st.getDamageValue());
		if (CosmeticsConfig.get().itemCounter && st.isStackable() && st == c.p.getMainHandItem()) {
			int total = 0;
			for (int i = 0; i < c.p.getInventory().getContainerSize(); i++) {
				ItemStack o = c.p.getInventory().getItem(i);
				if (ItemStack.isSameItemSameComponents(o, st)) total += o.getCount();
			}
			return "×" + total;
		}
		return "";
	}

	private static int durColor(ItemStack st, Ctx c) {
		if (!st.isDamageableItem()) return c.accent;
		float f = (st.getMaxDamage() - st.getDamageValue()) / (float) st.getMaxDamage();
		return f > .5f ? GOOD : f > .2f ? MID : BAD;
	}

	private static void keystrokes(Ctx c) {
		Minecraft mc = c.mc;
		int s = 20, gap = 2;
		key(c, "W", mc.options.keyUp.isDown(), s + gap, 0, s, s);
		key(c, "A", mc.options.keyLeft.isDown(), 0, s + gap, s, s);
		key(c, "S", mc.options.keyDown.isDown(), s + gap, s + gap, s, s);
		key(c, "D", mc.options.keyRight.isDown(), 2 * (s + gap), s + gap, s, s);
		int w2 = (3 * s + gap) / 2;
		key(c, "LMB " + leftClicks.size(), mc.options.keyAttack.isDown(), 0, 2 * (s + gap), w2, s);
		key(c, "RMB " + rightClicks.size(), mc.options.keyUse.isDown(), w2 + gap, 2 * (s + gap), w2, s);
		key(c, "▬▬▬", mc.options.keyJump.isDown(), 0, 3 * (s + gap), 3 * s + 2 * gap, 12);
	}

	private static void key(Ctx c, String label, boolean down, int x, int y, int w, int h) {
		int a = c.bgAlpha();
		if (down) {
			int pa = Math.max(a, 0x30);
			if (a > 2) c.g.fill(x, y, x + w, y + h, Math.min(255, pa + 60) << 24 | (c.accent & 0xFFFFFF));
		} else if (a > 2) {
			c.g.fill(x, y, x + w, y + h, a << 24 | BG_RGB);
		}
		int tc = down ? (a > 2 ? 0xFF140A1E : c.accent) : TEXT;
		int tw = c.w(label);
		if (tw > w - 3 && label.startsWith("LMB ")) { label = "L " + label.substring(4); tw = c.w(label); }
		if (tw > w - 3 && label.startsWith("RMB ")) { label = "R " + label.substring(4); tw = c.w(label); }
		c.g.text(c.font, c.c(label), x + (w - tw) / 2, y + (h - 8) / 2, tc, c.pos.shadow && !(down && a > 2));
	}

	/** Merkt sich beim Sterben die Koordinaten (jeden Tick). */
	private static boolean wasDead;
	public static void trackDeath(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null) { wasDead = false; return; }
		boolean dead = p.isDeadOrDying();
		CosmeticsConfig c = CosmeticsConfig.get();
		if (dead && !wasDead && c.deathCoords) {
			String dim = p.level().dimension().identifier().getPath().replace("the_", "");
			BlockPos b = p.blockPosition();
			c.lastDeath = b.getX() + " " + b.getY() + " " + b.getZ() + " (" + dim + ")";
			c.save();
		}
		wasDead = dead;
	}
}
