package de.mcben.cosmetics.client.mixin;

import de.mcben.cosmetics.client.McBenCosmeticsClient;
import net.minecraft.client.Camera;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Zoom: Sichtfeld verkleinern, solange die Zoom-Taste gehalten wird. */
@Mixin(Camera.class)
public class CameraMixin {
	@Inject(method = "calculateFov", at = @At("RETURN"), cancellable = true)
	private void mcbencosmetics$zoom(float partialTick, CallbackInfoReturnable<Float> cir) {
		float f = McBenCosmeticsClient.zoomAmount();
		if (f > 1.001f) cir.setReturnValue(cir.getReturnValue() / f);
	}
}
