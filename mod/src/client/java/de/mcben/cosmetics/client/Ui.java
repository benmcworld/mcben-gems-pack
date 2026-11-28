package de.mcben.cosmetics.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.AbstractWidget;
import net.minecraft.client.gui.narration.NarrationElementOutput;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.input.MouseButtonInfo;
import net.minecraft.network.chat.Component;

import java.util.function.Consumer;
import java.util.function.Function;
import java.util.function.Supplier;

/** Flache, cleane Bedienelemente im McBen-Stil (Schalter, Regler, Auswahl, Knopf, Tab). */
public final class Ui {
	private Ui() {}

	public static final int PANEL = 0xF2100B18, PANEL_2 = 0xF0181222, ROW = 0x22FFFFFF, ROW_HOVER = 0x3CFFFFFF;
	public static final int TEXT = 0xFFF2EEF8, MUTED = 0xFF9C93AE, OFF = 0xFF3A3346;

	public static int accent() { return CosmeticsConfig.get().accent(); }
	static Font font() { return Minecraft.getInstance().font; }
	public static Component t(String s) { return HudLayout.styled(s); }

	/** Rechteck mit leicht abgerundeten Ecken. */
	public static void rr(GuiGraphicsExtractor g, int x, int y, int w, int h, int col) {
		g.fill(x + 1, y, x + w - 1, y + h, col);
		g.fill(x, y + 1, x + 1, y + h - 1, col);
		g.fill(x + w - 1, y + 1, x + w, y + h - 1, col);
	}

	public static void label(GuiGraphicsExtractor g, String s, int x, int y, int col) {
		g.text(font(), t(s), x, y, col, false);
	}

	public static int width(String s) { return font().width(t(s)); }

	abstract static class Base extends AbstractWidget {
		Base(int x, int y, int w, int h, String msg) { super(x, y, w, h, Component.literal(msg)); }
		@Override protected void updateWidgetNarration(NarrationElementOutput out) { defaultButtonNarrationText(out); }
		void row(GuiGraphicsExtractor g) { rr(g, getX(), getY(), width, height, isHovered() ? ROW_HOVER : ROW); }
		int ty() { return getY() + (height - 8) / 2; }
	}

	// ------------------------------------------------------------------ Schalter
	public static class Toggle extends Base {
		private final String name;
		private final Supplier<Boolean> get;
		private final Consumer<Boolean> set;

		public Toggle(int x, int y, int w, String name, Supplier<Boolean> get, Consumer<Boolean> set) {
			super(x, y, w, 18, name);
			this.name = name; this.get = get; this.set = set;
		}

		@Override protected void extractWidgetRenderState(GuiGraphicsExtractor g, int mx, int my, float d) {
			row(g);
			label(g, name, getX() + 6, ty(), TEXT);
			boolean on = get.get();
			int tx = getX() + width - 24, tyy = getY() + height / 2 - 4;
			rr(g, tx, tyy, 18, 8, on ? accent() : OFF);
			int kx = on ? tx + 11 : tx + 1;
			rr(g, kx, tyy + 1, 6, 6, on ? 0xFFFFFFFF : 0xFF8A8298);
		}

		@Override public void onClick(MouseButtonEvent e, boolean dbl) { set.accept(!get.get()); }
	}

	// ------------------------------------------------------------------ Regler
	public static class Slider extends Base {
		private final String name;
		private final float min, max;
		private final Supplier<Float> get;
		private final Consumer<Float> set;
		private final Function<Float, String> fmt;

		public Slider(int x, int y, int w, String name, float min, float max, Supplier<Float> get, Consumer<Float> set, Function<Float, String> fmt) {
			super(x, y, w, 20, name);
			this.name = name; this.min = min; this.max = max; this.get = get; this.set = set; this.fmt = fmt;
		}

		@Override protected void extractWidgetRenderState(GuiGraphicsExtractor g, int mx, int my, float d) {
			row(g);
			float v = (get.get() - min) / (max - min);
			v = Math.max(0, Math.min(1, v));
			label(g, name, getX() + 6, getY() + 3, TEXT);
			String val = fmt.apply(get.get());
			label(g, val, getX() + width - 6 - width(val), getY() + 3, accent());
			int bx = getX() + 6, bw = width - 12, by = getY() + height - 5;
			g.fill(bx, by, bx + bw, by + 2, OFF);
			int fx = bx + Math.round(bw * v);
			g.fill(bx, by, fx, by + 2, accent());
			rr(g, fx - 2, by - 2, 4, 6, 0xFFFFFFFF);
		}

		private void apply(double mouseX) {
			float v = (float) ((mouseX - (getX() + 6)) / (width - 12));
			v = Math.max(0, Math.min(1, v));
			set.accept(min + v * (max - min));
		}

		@Override public void onClick(MouseButtonEvent e, boolean dbl) { apply(e.x()); }
		@Override protected void onDrag(MouseButtonEvent e, double dx, double dy) { apply(e.x()); }
	}

	// ------------------------------------------------------------------ Auswahl (Links-/Rechtsklick)
	public static class Cycle extends Base {
		private final String name;
		private final String[] values;
		private final Supplier<String> get;
		private final Consumer<String> set;

		public Cycle(int x, int y, int w, String name, String[] values, Supplier<String> get, Consumer<String> set) {
			super(x, y, w, 18, name);
			this.name = name; this.values = values; this.get = get; this.set = set;
		}

		@Override protected void extractWidgetRenderState(GuiGraphicsExtractor g, int mx, int my, float d) {
			row(g);
			label(g, name, getX() + 6, ty(), TEXT);
			String v = "‹ " + CosmeticsConfig.label(get.get()) + " ›";
			label(g, v, getX() + width - 6 - width(v), ty(), accent());
		}

		@Override protected boolean isValidClickButton(MouseButtonInfo info) { return info.button() == 0 || info.button() == 1; }

		@Override public void onClick(MouseButtonEvent e, boolean dbl) {
			set.accept(e.button() == 1 ? CosmeticsConfig.prev(values, get.get()) : CosmeticsConfig.next(values, get.get()));
		}
	}

	// ------------------------------------------------------------------ Knopf
	public static class Btn extends Base {
		private final Supplier<String> text;
		private final Runnable action;
		private final boolean primary;

		public Btn(int x, int y, int w, int h, String text, boolean primary, Runnable action) {
			this(x, y, w, h, () -> text, primary, action);
		}

		public Btn(int x, int y, int w, int h, Supplier<String> text, boolean primary, Runnable action) {
			super(x, y, w, h, text.get());
			this.text = text; this.action = action; this.primary = primary;
		}

		@Override protected void extractWidgetRenderState(GuiGraphicsExtractor g, int mx, int my, float d) {
			int a = accent();
			if (primary) rr(g, getX(), getY(), width, height, isHovered() ? (a | 0xFF000000) : (0xC0000000 | a & 0xFFFFFF));
			else row(g);
			String s = text.get();
			label(g, s, getX() + (width - width(s)) / 2, ty(), primary ? 0xFF140A1E : TEXT);
		}

		@Override public void onClick(MouseButtonEvent e, boolean dbl) { action.run(); }
	}

	// ------------------------------------------------------------------ Tab (Seitenleiste)
	public static class Tab extends Base {
		private final String text;
		private final Supplier<Boolean> active;
		private final Runnable action;

		public Tab(int x, int y, int w, String text, Supplier<Boolean> active, Runnable action) {
			super(x, y, w, 20, text);
			this.text = text; this.active = active; this.action = action;
		}

		@Override protected void extractWidgetRenderState(GuiGraphicsExtractor g, int mx, int my, float d) {
			boolean on = active.get();
			if (on) {
				rr(g, getX(), getY(), width, height, 0x40000000 | accent() & 0xFFFFFF);
				g.fill(getX(), getY() + 3, getX() + 2, getY() + height - 3, accent());
			} else if (isHovered()) {
				rr(g, getX(), getY(), width, height, ROW);
			}
			label(g, text, getX() + 8, ty(), on ? 0xFFFFFFFF : MUTED);
		}

		@Override public void onClick(MouseButtonEvent e, boolean dbl) { action.run(); }
	}
}
