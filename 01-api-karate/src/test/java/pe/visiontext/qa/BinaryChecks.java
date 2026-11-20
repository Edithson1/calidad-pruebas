package pe.visiontext.qa;

import javax.imageio.ImageIO;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipInputStream;

public final class BinaryChecks {
    private BinaryChecks() {
    }

    public static Map<String, Integer> jpegDimensions(byte[] bytes) throws IOException {
        if (bytes.length < 4 || (bytes[0] & 0xff) != 0xff || (bytes[1] & 0xff) != 0xd8) {
            throw new IOException("La respuesta no empieza con la firma JPEG");
        }
        var image = ImageIO.read(new ByteArrayInputStream(bytes));
        if (image == null) {
            throw new IOException("No se pudo decodificar el JPEG");
        }
        return Map.of("width", image.getWidth(), "height", image.getHeight());
    }

    public static boolean containsApkEntries(byte[] bytes) throws IOException {
        var requiredEntries = Set.of("AndroidManifest.xml", "classes.dex");
        var found = new HashSet<String>();
        try (var zip = new ZipInputStream(new ByteArrayInputStream(bytes))) {
            var entry = zip.getNextEntry();
            while (entry != null) {
                if (requiredEntries.contains(entry.getName())) {
                    found.add(entry.getName());
                    if (found.equals(requiredEntries)) {
                        return true;
                    }
                }
                entry = zip.getNextEntry();
            }
        }
        return false;
    }
}
