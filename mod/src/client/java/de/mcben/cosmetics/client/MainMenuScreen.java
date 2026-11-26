package de.mcben.cosmetics.client;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Hauptmenue (Taste K): Cosmetics oder Mods. */
public class MainMenuScreen extends Screen {
	private final Screen parent;

	public MainMenuScreen(Screen parent) {
		super(Component.literal("McBen Menü"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		int w = 220, x = width / 2 - w / 2, y = height / 2 - 30;
		addRenderableWidget(Button.builder(Component.literal("✦ Cosmetics  (Flügel, Heiligenschein, Plushie)"), b -> minecraft.gui.setScreen(new CosmeticsScreen(this)))
			.bounds(x, y, w, 20).build());
		addRenderableWidget(Button.builder(Component.literal("⚙ Mods  (Fullbright, Zoom, Anzeigen …)"), b -> minecraft.gui.setScreen(new ModsScreen(this)))
			.bounds(x, y + 26, w, 20).build());
		addRenderableWidget(Button.builder(Component.literal("Schließen"), b -> onClose()).bounds(x, y + 62, w, 20).build());
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
		super.extractRenderState(g, mouseX, mouseY, delta);
		g.centeredText(font, title, width / 2, height / 2 - 52, 0xFFFF6CF5);
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
