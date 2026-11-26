package de.mcben.cosmetics.client;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.AbstractSliderButton;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

import java.util.function.Consumer;
import java.util.function.Supplier;

/** Mods-Menue: Verbesserungen an/aus + Regler. */
public class ModsScreen extends Screen {
	private final Screen parent;

	public ModsScreen(Screen parent) {
		super(Component.literal("McBen Mods"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		CosmeticsConfig c = CosmeticsConfig.get();
		int w = 180, gap = 24, top = height / 2 - 90;
		int xl = width / 2 - w - 6, xr = width / 2 + 6;
		toggle(xl, top, w, "Fullbright (G)", () -> c.fullbright, v -> c.fullbright = v);
		toggle(xl, top + gap, w, "Zoom (C halten)", () -> c.zoom, v -> c.zoom = v);
		slider(xl, top + 2 * gap, w, "Zoom-Stärke", c.zoomFactor, 2f, 10f, v -> c.zoomFactor = v, v -> Math.round(v * 10) / 10f + "x");
		toggle(xl, top + 3 * gap, w, "Auto-Sprint", () -> c.autoSprint, v -> c.autoSprint = v);
		toggle(xl, top + 4 * gap, w, "Info (FPS, Ping, XYZ)", () -> c.infoHud, v -> c.infoHud = v);
		toggle(xr, top, w, "Keystrokes + CPS", () -> c.keystrokes, v -> c.keystrokes = v);
		toggle(xr, top + gap, w, "Rüstungs-Anzeige", () -> c.armorHud, v -> c.armorHud = v);
		toggle(xr, top + 2 * gap, w, "Low Fire", () -> c.lowFire, v -> c.lowFire = v);
		slider(xr, top + 3 * gap, w, "Feuer tiefer", c.fireOffset, 0f, 0.5f, v -> c.fireOffset = v, v -> Math.round(v * 200) + " %");
		toggle(xr, top + 4 * gap, w, "Low Shield", () -> c.lowShield, v -> c.lowShield = v);
		slider(xr, top + 5 * gap, w, "Schild tiefer", c.shieldOffset, 0f, 0.4f, v -> c.shieldOffset = v, v -> Math.round(v * 250) + " %");
		addRenderableWidget(Button.builder(Component.literal("Fertig"), b -> onClose()).bounds(width / 2 - 100, top + 6 * gap + 14, 200, 20).build());
	}

	private void toggle(int x, int y, int w, String name, Supplier<Boolean> get, Consumer<Boolean> set) {
		addRenderableWidget(Button.builder(label(name, get.get()), b -> {
			set.accept(!get.get());
			b.setMessage(label(name, get.get()));
		}).bounds(x, y, w, 20).build());
	}

	private static Component label(String name, boolean on) {
		return Component.literal(name + ": " + (on ? "§aAn" : "§cAus"));
	}

	private void slider(int x, int y, int w, String name, float value, float min, float max,
						Consumer<Float> set, java.util.function.Function<Float, String> fmt) {
		addRenderableWidget(new AbstractSliderButton(x, y, w, 20, Component.empty(), (value - min) / (max - min)) {
			{ updateMessage(); }
			@Override protected void updateMessage() { setMessage(Component.literal(name + ": " + fmt.apply((float) (min + this.value * (max - min))))); }
			@Override protected void applyValue() { set.accept((float) (min + this.value * (max - min))); }
		});
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
		super.extractRenderState(g, mouseX, mouseY, delta);
		g.centeredText(font, title, width / 2, height / 2 - 108, 0xFFFF6CF5);
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
