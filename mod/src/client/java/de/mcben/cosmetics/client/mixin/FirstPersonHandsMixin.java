package de.mcben.cosmetics.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import de.mcben.cosmetics.client.CosmeticsConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.FirstPersonHandsAndItemsRenderer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.state.level.FirstPersonHandsAndItemsRenderState;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Low Shield (Schild tiefer) und "Totem vorne halten" in der Ich-Perspektive. */
@Mixin(FirstPersonHandsAndItemsRenderer.class)
public class FirstPersonHandsMixin {
	private static int mcbencosmetics$mode(ItemStack stack) {
		if (stack == null) return 0;
		CosmeticsConfig c = CosmeticsConfig.get();
		if (c.lowShield && stack.is(Items.SHIELD)) return 1;
		if (c.totemForward && stack.is(Items.TOTEM_OF_UNDYING)) return 2;
		return 0;
	}

	@Inject(method = "submitArmWithItem", at = @At("HEAD"))
	private void mcbencosmetics$before(PlayerRenderState player, FirstPersonHandsAndItemsRenderState hands, float a, float b,
									   InteractionHand hand, float c, ItemStack stack, float d, PoseStack poseStack,
									   SubmitNodeCollector collector, int light, CallbackInfo ci) {
		int mode = mcbencosmetics$mode(stack);
		if (mode == 0) return;
		CosmeticsConfig cfg = CosmeticsConfig.get();
		poseStack.pushPose();
		if (mode == 1) {
			poseStack.translate(0f, -cfg.shieldOffset, 0f);
		} else {
			Minecraft mc = Minecraft.getInstance();
			boolean mainRight = mc.player == null || mc.player.getMainArm() == HumanoidArm.RIGHT;
			boolean right = (hand == InteractionHand.MAIN_HAND) == mainRight;
			float side = right ? 1f : -1f, k = cfg.totemForwardAmount;
			// zur Bildmitte, etwas hoeher und naeher an die Kamera
			poseStack.translate(-side * 0.30f * k, 0.10f * k, -0.12f * k);
			float s = cfg.totemSize;
			poseStack.scale(s, s, s);
		}
	}

	@Inject(method = "submitArmWithItem", at = @At("RETURN"))
	private void mcbencosmetics$after(PlayerRenderState player, FirstPersonHandsAndItemsRenderState hands, float a, float b,
									  InteractionHand hand, float c, ItemStack stack, float d, PoseStack poseStack,
									  SubmitNodeCollector collector, int light, CallbackInfo ci) {
		if (mcbencosmetics$mode(stack) != 0) poseStack.popPose();
	}
}
