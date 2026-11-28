package de.mcben.cosmetics.client;

import de.mcben.cosmetics.client.CosmeticsConfig.HudPos;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;

/**
 * HUD-Editor: Anzeigen mit der Maus ziehen, Mausrad = Groesse, Rechtsklick = an/aus.
 * Rechts/links erscheint ein Feld mit allen Einstellungen der gewaehlten Anzeige.
 */
public class HudEditorScreen extends Screen {
	private final Screen parent;
	private String selected;
	private boolean dragging;
	private float grabX, grabY;
	private boolean guideX, guideY;
	private int panelX, panelY;
	private static final int PANEL_W = 150;
	private int barY;

	public HudEditorScreen(Screen parent) {
		super(Component.literal("HUD-Editor"));
		this.parent = parent;
	}

	/** Fuer Tests: Anzeige vorab auswaehlen. */
	public HudEditorScreen select(String id) {
		selected = id;
		return this;
	}

	@Override
	protected void init() {
		CosmeticsConfig c = CosmeticsConfig.get();
		// untere Leiste: Knoepfe so breit wie ihr Text
		String[][] bar = {{"font"}, {"accent"}, {"style"}, {"reset"}, {"done"}};
		java.util.function.Supplier<String>[] texts = new java.util.function.Supplier[]{
			() -> "Aa " + CosmeticsConfig.label(c.font),
			() -> "● " + CosmeticsConfig.label(c.accent),
			() -> "▭ " + CosmeticsConfig.label(c.boxStyle),
			() -> "↺ Alles zurück",
			() -> "Fertig"};
		Runnable[] actions = {
			() -> c.font = CosmeticsConfig.next(CosmeticsConfig.FONTS, c.font),
			() -> c.accent = CosmeticsConfig.next(CosmeticsConfig.ACCENTS, c.accent),
			() -> c.boxStyle = CosmeticsConfig.next(CosmeticsConfig.BOX_STYLES, c.boxStyle),
			() -> { c.hud.clear(); selected = null; rebuildWidgets(); },
			this::onClose};
		int[] ws = new int[bar.length];
		int total = 0;
		for (int i = 0; i < bar.length; i++) { ws[i] = Math.max(Ui.width(i == 0 ? "Aa Clean Bold" : i == 2 ? "▭ Unterstrich" : texts[i].get()) + 14, 44); total += ws[i] + 4; }
		int bx = width / 2 - (total - 4) / 2, by = height - 64;
		barY = by;
		for (int i = 0; i < bar.length; i++) {
			addRenderableWidget(new Ui.Btn(bx, by, ws[i], 16, texts[i], i == bar.length - 1, actions[i]));
			bx += ws[i] + 4;
		}

		HudLayout.Element e = selected == null ? null : HudLayout.byId(selected);
		if (e == null) return;
		HudPos p = c.pos(e);
		float[] r = HudLayout.RECTS.get(e.id);
		boolean leftSide = r == null || r[0] + r[2] / 2 > width / 2f;
		int ph = 172;
		panelX = leftSide ? width / 2 - PANEL_W - 70 : width / 2 + 70;
		panelX = Math.max(2, Math.min(width - PANEL_W - 2, panelX));
		panelY = Math.max(2, Math.min((height - ph) / 2, by - ph - 4));
		int x = panelX + 6, y = panelY + 18, w = PANEL_W - 12;
		addRenderableWidget(new Ui.Toggle(x, y, w, "Anzeigen", () -> p.on, v -> p.on = v));
		addRenderableWidget(new Ui.Slider(x, y + 21, w, "Größe", 0.5f, 3f, () -> p.scale, v -> p.scale = Math.round(v * 20) / 20f, v -> Math.round(v * 100) + " %"));
		addRenderableWidget(new Ui.Slider(x, y + 43, w, "Hintergrund", 0f, 1f, () -> p.bg, v -> p.bg = v, v -> v < 0.01f ? "Unsichtbar" : Math.round(v * 100) + " %"));
		addRenderableWidget(new Ui.Toggle(x, y + 66, w, "Textschatten", () -> p.shadow, v -> p.shadow = v));
		if (e.hasLabel()) addRenderableWidget(new Ui.Toggle(x, y + 87, w, "Beschriftung", () -> p.label, v -> p.label = v));
		String[] colors = new String[CosmeticsConfig.ACCENTS.length + 1];
		colors[0] = "auto";
		System.arraycopy(CosmeticsConfig.ACCENTS, 0, colors, 1, CosmeticsConfig.ACCENTS.length);
		addRenderableWidget(new Ui.Cycle(x, y + 108, w, "Farbe", colors, () -> p.color, v -> p.color = v));
		addRenderableWidget(new Ui.Btn(x, y + 132, w, 18, "Zurücksetzen", false, () -> { c.hud.put(e.id, e.defaults()); rebuildWidgets(); }));
	}

	// ------------------------------------------------------------------ Zeichnen
	@Override
	public void extractBackground(GuiGraphicsExtractor g, int mx, int my, float d) {
		int a = Ui.accent();
		g.fill(0, 0, width, height, 0x40000000);
		// Raster-Mittellinien
		g.fill(width / 2, 0, width / 2 + 1, height, 0x18FFFFFF);
		g.fill(0, height / 2, width, height / 2 + 1, 0x18FFFFFF);
		HudLayout.render(g, true);
		CosmeticsConfig c = CosmeticsConfig.get();
		String hover = hit(mx, my);
		for (HudLayout.Element e : HudLayout.ELEMENTS) {
			float[] r = HudLayout.RECTS.get(e.id);
			if (r == null) continue;
			int x = (int) Math.floor(r[0]) - 1, y = (int) Math.floor(r[1]) - 1, w = (int) Math.ceil(r[2]) + 2, h = (int) Math.ceil(r[3]) + 2;
			boolean on = c.pos(e).on;
			if (!on) g.fill(x, y, x + w, y + h, 0xA0000000);
			int col = e.id.equals(selected) ? a : e.id.equals(hover) ? 0xC0FFFFFF : 0x40FFFFFF;
			g.outline(x, y, w, h, col);
		}
		if (dragging && guideX) g.fill(width / 2, 0, width / 2 + 1, height, a);
		if (dragging && guideY) g.fill(0, height / 2, width, height / 2 + 1, a);
		g.nextStratum();
		// Panel
		HudLayout.Element sel = selected == null ? null : HudLayout.byId(selected);
		if (sel != null) {
			Ui.rr(g, panelX, panelY, PANEL_W, 172, Ui.PANEL);
			g.fill(panelX + 1, panelY, panelX + PANEL_W - 1, panelY + 1, a);
			Ui.label(g, sel.name, panelX + 8, panelY + 6, a);
		}
		if (sel != null) return;
		String help = "Ziehen · Mausrad = Größe · Rechtsklick = an/aus";
		Ui.rr(g, width / 2 - Ui.width(help) / 2 - 6, barY - 15, Ui.width(help) + 12, 13, 0xA0000000);
		Ui.label(g, help, width / 2 - Ui.width(help) / 2, barY - 12, Ui.MUTED);
	}

	// ------------------------------------------------------------------ Maus
	private String hit(double mx, double my) {
		for (int i = HudLayout.ELEMENTS.size() - 1; i >= 0; i--) {
			HudLayout.Element e = HudLayout.ELEMENTS.get(i);
			float[] r = HudLayout.RECTS.get(e.id);
			if (r != null && mx >= r[0] && mx < r[0] + r[2] && my >= r[1] && my < r[1] + r[3]) return e.id;
		}
		return null;
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent ev, boolean dbl) {
		if (super.mouseClicked(ev, dbl)) return true;
		String id = hit(ev.x(), ev.y());
		CosmeticsConfig c = CosmeticsConfig.get();
		if (id == null) {
			if (selected != null) { selected = null; rebuildWidgets(); }
			return false;
		}
		HudLayout.Element e = HudLayout.byId(id);
		if (ev.button() == 1) {
			HudPos p = c.pos(e);
			p.on = !p.on;
			return true;
		}
		float[] r = HudLayout.RECTS.get(id);
		grabX = (float) ev.x() - r[0];
		grabY = (float) ev.y() - r[1];
		dragging = true;
		if (!id.equals(selected)) { selected = id; rebuildWidgets(); }
		return true;
	}

	@Override
	public boolean mouseDragged(MouseButtonEvent ev, double dx, double dy) {
		if (!dragging || selected == null) return super.mouseDragged(ev, dx, dy);
		HudLayout.Element e = HudLayout.byId(selected);
		float[] r = HudLayout.RECTS.get(selected);
		if (e == null || r == null) return true;
		float w = r[2], h = r[3];
		float x = (float) ev.x() - grabX, y = (float) ev.y() - grabY;
		guideX = guideY = false;
		if (!hasShiftDownSafe()) {
			float[] xs = {2, width - w - 2, width / 2f - w / 2f};
			for (int i = 0; i < xs.length; i++) if (Math.abs(x - xs[i]) < 5) { x = xs[i]; guideX = i == 2; break; }
			float[] ys = {2, height - h - 2, height / 2f - h / 2f};
			for (int i = 0; i < ys.length; i++) if (Math.abs(y - ys[i]) < 5) { y = ys[i]; guideY = i == 2; break; }
		}
		x = Math.max(0, Math.min(width - w, x));
		y = Math.max(0, Math.min(height - h, y));
		HudLayout.anchor(CosmeticsConfig.get().pos(e), x, y, w, h, width, height);
		r[0] = x; r[1] = y;
		return true;
	}

	private boolean hasShiftDownSafe() {
		return minecraft != null && minecraft.hasShiftDown();
	}

	@Override
	public boolean mouseReleased(MouseButtonEvent ev) {
		if (dragging) {
			dragging = false;
			rebuildWidgets();   // Panel auf die andere Seite, falls noetig
			return true;
		}
		return super.mouseReleased(ev);
	}

	@Override
	public boolean mouseScrolled(double mx, double my, double sx, double sy) {
		String id = hit(mx, my);
		if (id == null) id = selected;
		if (id == null) return super.mouseScrolled(mx, my, sx, sy);
		HudPos p = CosmeticsConfig.get().pos(HudLayout.byId(id));
		p.scale = Math.max(0.5f, Math.min(3f, Math.round((p.scale + (sy > 0 ? 0.1f : -0.1f)) * 20) / 20f));
		return true;
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
