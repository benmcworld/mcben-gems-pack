package de.mcben.cosmetics.client;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

import java.util.LinkedHashMap;

/** Das McBen-Menue (Taste K): Seitenleiste mit Tabs, rechts die Einstellungen. */
public class McBenScreen extends Screen {
	public static final String[] TABS = {"Cosmetics", "Mods", "HUD", "Totem", "Design"};
	private static int tab = 0;

	private final Screen parent;
	private int px, py, pw, ph, cx, cw;

	public McBenScreen(Screen parent) {
		this(parent, tab);
	}

	public McBenScreen(Screen parent, int startTab) {
		super(Component.literal("McBen"));
		this.parent = parent;
		tab = startTab;
	}

	@Override
	protected void init() {
		CosmeticsConfig c = CosmeticsConfig.get();
		pw = Math.min(width - 16, 420);
		ph = Math.min(height - 16, 250);
		px = (width - pw) / 2;
		py = (height - ph) / 2;
		int side = 88;
		for (int i = 0; i < TABS.length; i++) {
			int idx = i;
			addRenderableWidget(new Ui.Tab(px + 6, py + 30 + i * 22, side - 12, TABS[i], () -> tab == idx, () -> { tab = idx; rebuildWidgets(); }));
		}
		addRenderableWidget(new Ui.Btn(px + 6, py + ph - 26, side - 12, 20, "Fertig", true, this::onClose));

		cx = px + side + 4;
		cw = pw - side - 12;
		int top = py + 30;
		int col = (cw - 6) / 2;
		int xl = cx, xr = cx + col + 6;
		switch (tab) {
			case 0 -> {
				add(new Ui.Cycle(xl, top, col, "Flügel", CosmeticsConfig.WINGS, () -> c.wings, v -> c.wings = v));
				add(new Ui.Cycle(xr, top, col, "Farbe", CosmeticsConfig.THEMES, () -> c.theme, v -> c.theme = v));
				add(new Ui.Toggle(xl, top + 22, col, "Flügelschlag", () -> c.flap, v -> c.flap = v));
				add(new Ui.Toggle(xr, top + 22, col, "Heiligenschein", () -> c.halo, v -> c.halo = v));
				add(new Ui.Slider(xl, top + 44, cw, "Leuchtstärke", 0.2f, 2f, () -> c.brightness, v -> c.brightness = v, v -> Math.round(v * 100) + " %"));
				EditBox plush = new EditBox(font, xl + 6, top + 96, cw - 12, 12, Component.literal("Plushie-Skin"));
				plush.setBordered(false);
				plush.setTextColor(0xFFFFFFFF);
				plush.setHint(Component.literal("leer = dein Skin, z. B. BastiGHG").withColor(0x9C93AE));
				plush.setMaxLength(16);
				plush.setValue(c.plushieName == null ? "" : c.plushieName);
				plush.setResponder(v -> c.plushieName = v.trim());
				addRenderableWidget(plush);
			}
			case 1 -> {
				add(new Ui.Toggle(xl, top, col, "Fullbright (G)", () -> c.fullbright, v -> c.fullbright = v));
				add(new Ui.Toggle(xr, top, col, "Auto-Sprint", () -> c.autoSprint, v -> c.autoSprint = v));
				add(new Ui.Toggle(xl, top + 22, col, "Zoom (C halten)", () -> c.zoom, v -> c.zoom = v));
				add(new Ui.Slider(xr, top + 21, col, "Zoom", 2f, 10f, () -> c.zoomFactor, v -> c.zoomFactor = v, v -> Math.round(v * 10) / 10f + "x"));
				add(new Ui.Toggle(xl, top + 44, col, "Low Fire", () -> c.lowFire, v -> c.lowFire = v));
				add(new Ui.Slider(xr, top + 43, col, "Feuer tiefer", 0f, 0.4f, () -> c.fireOffset, v -> c.fireOffset = v, v -> Math.round(v * 250) + " %"));
				add(new Ui.Toggle(xl, top + 66, col, "Low Shield", () -> c.lowShield, v -> c.lowShield = v));
				add(new Ui.Slider(xr, top + 65, col, "Schild tiefer", 0f, 0.4f, () -> c.shieldOffset, v -> c.shieldOffset = v, v -> Math.round(v * 250) + " %"));
				add(new Ui.Toggle(xl, top + 88, col, "Item-Zähler", () -> c.itemCounter, v -> c.itemCounter = v));
				add(new Ui.Toggle(xr, top + 88, col, "Todespunkt merken", () -> c.deathCoords, v -> c.deathCoords = v));
			}
			case 2 -> {
				add(new Ui.Btn(cx, top, cw, 20, "✥  HUD-Editor öffnen  (verschieben & Größe)", true,
					() -> minecraft.gui.setScreen(new HudEditorScreen(this))));
				int i = 0, c3 = (cw - 8) / 3;
				for (HudLayout.Element e : HudLayout.ELEMENTS) {
					CosmeticsConfig.HudPos p = c.pos(e);
					int x = cx + (i % 3) * (c3 + 4), y = top + 25 + (i / 3) * 20;
					add(new Ui.Toggle(x, y, c3, e.name, () -> p.on, v -> p.on = v));
					i++;
				}
			}
			case 3 -> {
				add(new Ui.Toggle(xl, top, col, "Totem vorne halten", () -> c.totemForward, v -> c.totemForward = v));
				add(new Ui.Slider(xr, top - 1, col, "Wie weit", 0f, 1f, () -> c.totemForwardAmount, v -> c.totemForwardAmount = v, v -> Math.round(v * 100) + " %"));
				add(new Ui.Slider(xr, top + 21, col, "Totem-Größe", 0.5f, 1.5f, () -> c.totemSize, v -> c.totemSize = v, v -> Math.round(v * 100) + " %"));
				add(new Ui.Toggle(xl, top + 48, col, "Pop-Umriss", () -> c.totemGhost, v -> c.totemGhost = v));
				add(new Ui.Cycle(xr, top + 48, col, "Farbe", CosmeticsConfig.GHOST_COLORS, () -> c.ghostColor, v -> c.ghostColor = v));
				add(new Ui.Slider(xl, top + 69, col, "Dauer", 0.4f, 3f, () -> c.ghostTime, v -> c.ghostTime = v, v -> Math.round(v * 10) / 10f + " s"));
				add(new Ui.Toggle(xr, top + 70, col, "Auch bei Gegnern", () -> c.ghostOthers, v -> c.ghostOthers = v));
				add(new Ui.Toggle(xl, top + 92, col, "Pop-Nachricht", () -> c.popMessage, v -> c.popMessage = v));
				add(new Ui.Btn(xr, top + 92, col, 18, "Umriss testen", false, TotemGhosts::spawnTestGhost));
			}
			default -> {
				add(new Ui.Cycle(xl, top, cw, "Schriftart", CosmeticsConfig.FONTS, () -> c.font, v -> c.font = v));
				add(new Ui.Cycle(xl, top + 22, cw, "Akzentfarbe", CosmeticsConfig.ACCENTS, () -> c.accent, v -> c.accent = v));
				add(new Ui.Cycle(xl, top + 44, cw, "Kästchen-Stil", CosmeticsConfig.BOX_STYLES, () -> c.boxStyle, v -> c.boxStyle = v));
				add(new Ui.Slider(xl, top + 66, cw, "Hintergrund (alle)", 0f, 1f, McBenScreen::avgBg, McBenScreen::setAllBg, v -> Math.round(v * 100) + " %"));
				add(new Ui.Toggle(xl, top + 90, col, "Textschatten (alle)", McBenScreen::allShadow, McBenScreen::setAllShadow));
				add(new Ui.Toggle(xr, top + 90, col, "Beschriftung (alle)", McBenScreen::allLabel, McBenScreen::setAllLabel));
				add(new Ui.Btn(xl, top + 116, cw, 18, "HUD komplett zurücksetzen", false, () -> c.hud = new LinkedHashMap<>()));
			}
		}
	}

	private void add(net.minecraft.client.gui.components.AbstractWidget w) {
		addRenderableWidget(w);
	}

	static float avgBg() {
		CosmeticsConfig c = CosmeticsConfig.get();
		float s = 0;
		for (HudLayout.Element e : HudLayout.ELEMENTS) s += c.pos(e).bg;
		return s / HudLayout.ELEMENTS.size();
	}

	static void setAllBg(float v) {
		CosmeticsConfig c = CosmeticsConfig.get();
		for (HudLayout.Element e : HudLayout.ELEMENTS) c.pos(e).bg = v;
	}

	static boolean allShadow() {
		CosmeticsConfig c = CosmeticsConfig.get();
		for (HudLayout.Element e : HudLayout.ELEMENTS) if (!c.pos(e).shadow) return false;
		return true;
	}

	static void setAllShadow(boolean v) {
		CosmeticsConfig c = CosmeticsConfig.get();
		for (HudLayout.Element e : HudLayout.ELEMENTS) c.pos(e).shadow = v;
	}

	static boolean allLabel() {
		CosmeticsConfig c = CosmeticsConfig.get();
		for (HudLayout.Element e : HudLayout.ELEMENTS) if (e.hasLabel() && !c.pos(e).label) return false;
		return true;
	}

	static void setAllLabel(boolean v) {
		CosmeticsConfig c = CosmeticsConfig.get();
		for (HudLayout.Element e : HudLayout.ELEMENTS) c.pos(e).label = v;
	}

	@Override
	public void extractBackground(GuiGraphicsExtractor g, int mx, int my, float d) {
		g.fill(0, 0, width, height, 0x66000000);
		int a = Ui.accent();
		Ui.rr(g, px, py, pw, ph, Ui.PANEL);
		Ui.rr(g, px, py, 88, ph, Ui.PANEL_2);
		g.fill(px + 1, py, px + pw - 1, py + 1, a);
		Ui.label(g, "✦ McBen", px + 10, py + 10, a);
		Ui.label(g, TABS[tab], cx, py + 10, 0xFFFFFFFF);
		String hint = switch (tab) {
			case 0 -> "F5 = dich von außen ansehen";
			case 2 -> "Anzeigen an/aus · Editor zum Verschieben";
			case 3 -> "Minimods rund ums Totem";
			case 4 -> "Gilt für HUD und Menü";
			default -> "Verbesserungen";
		};
		Ui.label(g, hint, px + pw - 8 - Ui.width(hint), py + 10, Ui.MUTED);
		g.fill(cx, py + 23, px + pw - 8, py + 24, 0x30FFFFFF);
		if (tab == 0) {
			Ui.label(g, "Plushie-Totem mit Skin von:", cx + 2, py + 30 + 76, Ui.MUTED);
			Ui.rr(g, cx, py + 30 + 88, cw, 22, Ui.ROW);
			g.fill(cx + 4, py + 30 + 108, cx + cw - 4, py + 30 + 109, Ui.accent());
		}
		g.nextStratum();
	}

	@Override
	public void onClose() {
		CosmeticsConfig.get().save();
		minecraft.gui.setScreen(parent);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
