package de.mcben.cosmetics.client.mixin;

import de.mcben.cosmetics.client.TotemGhosts;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.network.protocol.game.ClientboundEntityEventPacket;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Erkennt Totem-Pops (Entity-Event 35) von dir und anderen Spielern. */
@Mixin(ClientPacketListener.class)
public class ClientPacketListenerMixin {
	@Inject(method = "handleEntityEvent", at = @At("TAIL"))
	private void mcbencosmetics$totemPop(ClientboundEntityEventPacket packet, CallbackInfo ci) {
		Minecraft mc = Minecraft.getInstance();
		if (packet.getEventId() != 35 || mc.level == null) return;
		Entity e = packet.getEntity(mc.level);
		if (e != null) TotemGhosts.onPop(e);
	}
}
