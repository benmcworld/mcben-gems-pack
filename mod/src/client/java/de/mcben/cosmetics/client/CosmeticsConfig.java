package de.mcben.cosmetics.client;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.loader.api.FabricLoader;

import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;

/** Gespeicherte Auswahl (config/mcbencosmetics.json). */
public class CosmeticsConfig {
	public static final String[] WINGS = {"aus", "galaxie", "engel"};
	public static final String[] THEMES = {"lila", "gruen", "blau", "rot", "dark", "gold"};

	public String wings = "galaxie";
	public String theme = "lila";
	public boolean flap = true;
	public boolean halo = false;
	public float brightness = 1.0f;   // 0.2 .. 2.0, gilt fuer Leuchten von Fluegeln und Heiligenschein
	/** Leer = eigener Skin; sonst Spielername, dessen Skin das Plushie-Totem bekommt. */
	public String plushieName = "";

	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static CosmeticsConfig instance;

	private static Path file() {
		return FabricLoader.getInstance().getConfigDir().resolve("mcbencosmetics.json");
	}

	public static CosmeticsConfig get() {
		if (instance == null) {
			instance = new CosmeticsConfig();
			try {
				if (Files.exists(file())) {
					try (Reader r = Files.newBufferedReader(file())) {
						CosmeticsConfig loaded = GSON.fromJson(r, CosmeticsConfig.class);
						if (loaded != null) instance = loaded;
					}
				}
			} catch (Exception e) {
				McBenCosmeticsClient.LOG.warn("Konnte Einstellungen nicht laden", e);
			}
		}
		return instance;
	}

	public void save() {
		try (Writer w = Files.newBufferedWriter(file())) {
			GSON.toJson(this, w);
		} catch (Exception e) {
			McBenCosmeticsClient.LOG.warn("Konnte Einstellungen nicht speichern", e);
		}
	}

	/** Leuchtfarbe (RGB) pro Farbschema. */
	public static int tipColor(String theme) {
		return switch (theme) {
			case "gruen" -> 0xB0FF8A;
			case "blau" -> 0x8FE8FF;
			case "rot" -> 0xFFA06C;
			case "dark" -> 0xFFFFFF;
			case "gold" -> 0xFFF0A0;
			default -> 0xFF6CF5;
		};
	}

	public static String label(String id) {
		return switch (id) {
			case "aus" -> "Aus";
			case "galaxie" -> "Galaxie-Federn";
			case "engel" -> "Engel";
			case "lila" -> "Lila";
			case "gruen" -> "Grün";
			case "blau" -> "Blau";
			case "rot" -> "Rot";
			case "dark" -> "Dark Edition";
			case "gold" -> "Gold";
			default -> id;
		};
	}

	public static String next(String[] values, String current) {
		for (int i = 0; i < values.length; i++) if (values[i].equals(current)) return values[(i + 1) % values.length];
		return values[0];
	}
}
