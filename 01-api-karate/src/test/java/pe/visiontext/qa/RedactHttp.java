package pe.visiontext.qa;

import com.intuit.karate.http.HttpLogModifier;

import java.net.URI;
import java.util.Set;
import java.util.Locale;
import java.util.regex.Pattern;

/** Conserva los códigos y tiempos en los reportes sin incluir secretos de sesión. */
public final class RedactHttp implements HttpLogModifier {
    private static final Set<String> PRIVATE_HEADERS =
            Set.of("authorization", "proxy-authorization", "cookie", "set-cookie");
    private static final Pattern TOKEN =
            Pattern.compile("(\"access_token\"\\s*:\\s*\")[^\"]*(\")");

    private static boolean isLogin(String uri) {
        return "/api/admin/login".equals(URI.create(uri).getPath());
    }

    @Override
    public boolean enableForUri(String uri) {
        return true;
    }

    @Override
    public String uri(String uri) {
        return uri;
    }

    @Override
    public String header(String name, String value) {
        return PRIVATE_HEADERS.contains(name.toLowerCase(Locale.ROOT)) ? "***" : value;
    }

    @Override
    public String request(String uri, String request) {
        return isLogin(uri) ? "[formulario oculto]" : request;
    }

    @Override
    public String response(String uri, String response) {
        return isLogin(uri) ? TOKEN.matcher(response).replaceAll("$1***$2") : response;
    }
}
