package pe.visiontext.qa;

import com.intuit.karate.Results;
import com.intuit.karate.Runner;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ApiTest {
    @Test
    void runFeatures() {
        String profile = System.getProperty("karate.env", "publico");
        String tags = switch (profile) {
            case "publico" -> "@comun,@publico";
            case "local" -> "@comun,@local";
            case "limite-login" -> "@limite-login";
            default -> throw new IllegalArgumentException("Perfil Karate no reconocido: " + profile);
        };

        Results results = Runner.path("features")
                .karateEnv(profile)
                .tags(tags)
                .reportDir("reports/" + profile)
                .outputJunitXml(true)
                .outputCucumberJson(true)
                .parallel(1);

        assertTrue(results.getScenariosTotal() > 0, "No se ejecutó ningún escenario de Karate");
        assertEquals(0, results.getFailCount(), results.getErrorMessages());
    }
}
