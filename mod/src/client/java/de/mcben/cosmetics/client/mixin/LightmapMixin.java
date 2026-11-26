package de.mcben.cosmetics.client.mixin;

import de.mcben.cosmetics.client.CosmeticsConfig;
import net.minecraft.client.renderer.LightmapRenderStateExtractor;
import net.minecraft.client.renderer.state.LightmapRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Fullbright: Lichtkarte wie mit Nachtsicht berechnen. */
@Mixin(LightmapRenderStateExtractor.class)
public class LightmapMixin {
	@Shadow private boolean needsUpdate;
	private boolean mcbencosmetics$last;

	@Inject(method = "extract", at = @At("HEAD"))
	private void mcbencosmetics$forceUpdate(LightmapRenderState state, float partialTick, CallbackInfo ci) {
		boolean on = CosmeticsConfig.get().fullbright;
		if (on || on != mcbencosmetics$last) needsUpdate = true;
		mcbencosmetics$last = on;
	}

	@Inject(method = "extract", at = @At("TAIL"))
	private void mcbencosmetics$fullbright(LightmapRenderState state, float partialTick, CallbackInfo ci) {
		if (!CosmeticsConfig.get().fullbright) return;
		state.nightVisionEffectIntensity = 1f;
		state.darknessEffectScale = 0f;
		state.brightness = 1f;
		state.needsUpdate = true;
	}
}
