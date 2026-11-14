package de.mcben.cosmetics.client;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.AbstractSliderButton;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Menue (Taste K): Fluegel, Farbe, Fluegelschlag, Heiligenschein, Helligkeit. */
public class CosmeticsScreen extends Screen {
	private final Screen parent;

	public CosmeticsScreen(Screen parent) {
		super(Component.literal("McBen Cosmetics"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		CosmeticsConfig cfg = CosmeticsConfig.get();
		int w = 220, x = width / 2 - w / 2, y = height / 2 - 70, h = 20, gap = 24;
		addRenderableWidget(Button.builder(Component.literal("Flügel: " + CosmeticsConfig.label(cfg.wings)), b -> {
			cfg.wings = CosmeticsConfig.next(CosmeticsConfig.WINGS, cfg.wings);
			b.setMessage(Component.literal("Flügel: " + CosmeticsConfig.label(cfg.wings)));
		}).bounds(x, y, w, h).build());
		addRenderableWidget(Button.builder(Component.literal("Farbe: " + CosmeticsConfig.label(cfg.theme)), b -> {
			cfg.theme = CosmeticsConfig.next(CosmeticsConfig.THEMES, cfg.theme);
			b.setMessage(Component.literal("Farbe: " + CosmeticsConfig.label(cfg.theme)));
		}).bounds(x, y + gap, w, h).build());
		addRenderableWidget(Button.builder(onOff("Flügelschlag", cfg.flap), b -> {
			cfg.flap = !cfg.flap;
			b.setMessage(onOff("Flügelschlag", cfg.flap));
		}).bounds(x, y + 2 * gap, w, h).build());
		addRenderableWidget(Button.builder(onOff("Heiligenschein", cfg.halo), b -> {
			cfg.halo = !cfg.halo;
			b.setMessage(onOff("Heiligenschein", cfg.halo));
		}).bounds(x, y + 3 * gap, w, h).build());
		addRenderableWidget(new AbstractSliderButton(x, y + 4 * gap, w, h, Component.empty(), (cfg.brightness - 0.2) / 1.8) {
			{ updateMessage(); }
			@Override protected void updateMessage() {
				setMessage(Component.literal("Leuchtstärke: " + Math.round((0.2 + value * 1.8) * 100) + " %"));
			}
			@Override protected void applyValue() {
				cfg.brightness = (float) (0.2 + value * 1.8);
			}
		});
		addRenderableWidget(Button.builder(Component.literal("Fertig"), b -> onClose())
			.bounds(x, y + 5 * gap + 8, w, h).build());
	}

	private static Component onOff(String name, boolean on) {
		return Component.literal(name + ": " + (on ? "An" : "Aus"));
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
		super.extractRenderState(g, mouseX, mouseY, delta);
		g.centeredText(font, title, width / 2, height / 2 - 92, 0xFFFF6CF5);
		g.centeredText(font, Component.literal("Zum Ansehen in die 3rd-Person wechseln (F5)"), width / 2, height / 2 + 108, 0xFFB8A8D0);
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
