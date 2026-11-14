package de.mcben.cosmetics.client.mixin;

import com.mojang.serialization.MapCodec;
import de.mcben.cosmetics.client.PlushieRenderer;
import net.minecraft.client.renderer.special.SpecialModelRenderer;
import net.minecraft.client.renderer.special.SpecialModelRenderers;
import net.minecraft.resources.Identifier;
import net.minecraft.util.ExtraCodecs;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Meldet den Modell-Typ "mcbencosmetics:plushie" an (wird im Item-Modell des Totems benutzt). */
@Mixin(SpecialModelRenderers.class)
public class SpecialModelRenderersMixin {
	@Shadow @Final private static ExtraCodecs.LateBoundIdMapper<Identifier, MapCodec<? extends SpecialModelRenderer.Unbaked<?>>> ID_MAPPER;

	@Inject(method = "bootstrap", at = @At("TAIL"))
	private static void mcbencosmetics$register(CallbackInfo ci) {
		ID_MAPPER.put(Identifier.fromNamespaceAndPath("mcbencosmetics", "plushie"), PlushieRenderer.Unbaked.MAP_CODEC);
	}
}
