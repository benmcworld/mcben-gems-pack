package de.mcben.cosmetics.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import de.mcben.cosmetics.client.CosmeticsConfig;
import net.minecraft.client.renderer.ScreenEffectRenderer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Low Fire: Feuer-Anzeige im Bildschirm nach unten schieben. */
@Mixin(ScreenEffectRenderer.class)
public class ScreenEffectRendererMixin {
	@Inject(method = "submitFire", at = @At("HEAD"))
	private static void mcbencosmetics$lowFireDown(PoseStack poseStack, SubmitNodeCollector collector, TextureAtlasSprite sprite, CallbackInfo ci) {
		CosmeticsConfig c = CosmeticsConfig.get();
		if (c.lowFire) poseStack.translate(0f, -c.fireOffset, 0f);
	}

	@Inject(method = "submitFire", at = @At("RETURN"))
	private static void mcbencosmetics$lowFireBack(PoseStack poseStack, SubmitNodeCollector collector, TextureAtlasSprite sprite, CallbackInfo ci) {
		CosmeticsConfig c = CosmeticsConfig.get();
		if (c.lowFire) poseStack.translate(0f, c.fireOffset, 0f);
	}
}
