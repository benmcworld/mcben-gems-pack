package de.mcben.cosmetics.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import de.mcben.cosmetics.client.CosmeticsConfig;
import net.minecraft.client.renderer.FirstPersonHandsAndItemsRenderer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.state.level.FirstPersonHandsAndItemsRenderState;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Low Shield: Schild in der Ich-Perspektive tiefer halten. */
@Mixin(FirstPersonHandsAndItemsRenderer.class)
public class FirstPersonHandsMixin {
	private static boolean mcbencosmetics$active(ItemStack stack) {
		CosmeticsConfig c = CosmeticsConfig.get();
		return c.lowShield && stack != null && stack.is(Items.SHIELD);
	}

	@Inject(method = "submitArmWithItem", at = @At("HEAD"))
	private void mcbencosmetics$shieldDown(PlayerRenderState player, FirstPersonHandsAndItemsRenderState hands, float a, float b,
										   InteractionHand hand, float c, ItemStack stack, float d, PoseStack poseStack,
										   SubmitNodeCollector collector, int light, CallbackInfo ci) {
		if (mcbencosmetics$active(stack)) poseStack.translate(0f, -CosmeticsConfig.get().shieldOffset, 0f);
	}

	@Inject(method = "submitArmWithItem", at = @At("RETURN"))
	private void mcbencosmetics$shieldBack(PlayerRenderState player, FirstPersonHandsAndItemsRenderState hands, float a, float b,
										   InteractionHand hand, float c, ItemStack stack, float d, PoseStack poseStack,
										   SubmitNodeCollector collector, int light, CallbackInfo ci) {
		if (mcbencosmetics$active(stack)) poseStack.translate(0f, CosmeticsConfig.get().shieldOffset, 0f);
	}
}
