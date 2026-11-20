"""Generate editable JMeter 5.6.3 plans from the common workload definitions."""

from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

from perfiles import BUDGETS, OPERATIONS, PROFILES, ROOT


def prop(parent, name, value):
    if isinstance(value, bool):
        return _prop(parent, "boolProp", name, str(value).lower())
    return _prop(parent, "stringProp", name, str(value))


def _prop(parent, tag, name, value):
    node = SubElement(parent, tag, name=name)
    node.text = value
    return node


def component(parent, tag, gui, label):
    node = SubElement(parent, tag, guiclass=gui, testclass=tag, testname=label, enabled="true")
    return node, SubElement(parent, "hashTree")


def property_ref(name, default):
    return "${__P(" + name + "," + str(default) + ")}"


def variable(name):
    return "${" + name + "}"


def arguments(parent, values=None, raw=None):
    args = SubElement(parent, "elementProp", name="HTTPsampler.Arguments", elementType="Arguments")
    entries = SubElement(args, "collectionProp", name="Arguments.arguments")
    for name, value in ([("", raw)] if raw is not None else (values or {}).items()):
        item = SubElement(entries, "elementProp", name=name, elementType="HTTPArgument")
        prop(item, "HTTPArgument.always_encode", raw is None)
        prop(item, "Argument.name", name)
        prop(item, "Argument.value", value)
        prop(item, "Argument.metadata", "=")
        prop(item, "HTTPArgument.use_equals", True)


def headers(tree, values):
    node, _ = component(tree, "HeaderManager", "HeaderPanel", "Cabeceras de la peticion")
    collection = SubElement(node, "collectionProp", name="HeaderManager.headers")
    for name, value in values.items():
        item = SubElement(collection, "elementProp", name="", elementType="Header")
        prop(item, "Header.name", name)
        prop(item, "Header.value", value)


def script(tree, tag, label, body):
    node, children = component(tree, tag, "TestBeanGUI", label)
    for key, value in {"scriptLanguage": "groovy", "parameters": "", "filename": "",
                       "cacheKey": "true", "script": body.strip()}.items():
        prop(node, key, value)
    return children


def check(tree, code, body):
    script(tree, "JSR223Assertion", "Validar respuesta y correlacion", f"""
if (prev.getResponseCode() != '{code}') return
def verify = {{ ok, message ->
    if (!ok) {{
        AssertionResult.setFailure(true)
        AssertionResult.setFailureMessage(message)
    }}
    ok
}}
try {{
    {body.strip()}
}} catch (Exception ignored) {{
    AssertionResult.setFailure(true)
    AssertionResult.setFailureMessage('Respuesta inesperada o formato invalido')
}}
""")


class Plan:
    def __init__(self, env, profile):
        self.env = env
        self.profile = profile
        self.root = Element("jmeterTestPlan", version="1.2", properties="5.0", jmeter="5.6.3")
        tree = SubElement(self.root, "hashTree")
        plan, self.tree = component(tree, "TestPlan", "TestPlanGui", f"VisionText | {env} | {profile}")
        prop(plan, "TestPlan.comments", "Plan HTTP generado desde scripts/perfiles.py. Usa el lanzador para configurar datos y reportes.")
        prop(plan, "TestPlan.functional_mode", False)
        prop(plan, "TestPlan.serialize_threadgroups", False)
        variables = SubElement(plan, "elementProp", name="TestPlan.user_defined_variables", elementType="Arguments")
        SubElement(variables, "collectionProp", name="Arguments.arguments")
        defaults, _ = component(self.tree, "ConfigTestElement", "HttpDefaultsGui", "API y timeouts")
        arguments(defaults)
        api_domain = "127.0.0.1" if env == "local" else "visiontext-backend.onrender.com"
        prop(defaults, "HTTPSampler.domain", api_domain)
        prop(defaults, "HTTPSampler.protocol", "http" if env == "local" else "https")
        prop(defaults, "HTTPSampler.port", property_ref("API_PORT", 8012) if env == "local" else "443")
        prop(defaults, "HTTPSampler.connect_timeout", 12000)
        ready_timeout = 170000 if profile == "inicio" else 65000
        prop(defaults, "HTTPSampler.response_timeout", ready_timeout if env == "render" else 25000)
        prop(defaults, "HTTPSampler.implementation", "HttpClient4")
        prop(defaults, "HTTPSampler.contentEncoding", "UTF-8")
        prop(defaults, "HTTPSampler.concurrentPool", 1)

    def http(self, parent, key, path, *, method="GET", expected=200, values=None, raw=None,
             request_headers=None, upload=None, assertion=None, before=None, web=False):
        budget, description = OPERATIONS[key]
        label = f"{key} {description}"
        if self.env == "render" and key.startswith("ADM-"):
            tree = script(parent, "JSR223Sampler", label, verified_admin_request(path, values, method))
        else:
            node, tree = component(parent, "HTTPSamplerProxy", "HttpTestSampleGui", label)
            arguments(node, values, raw)
            prop(node, "HTTPSampler.path", path)
            prop(node, "HTTPSampler.method", method)
            prop(node, "HTTPSampler.follow_redirects", False)
            prop(node, "HTTPSampler.auto_redirects", False)
            prop(node, "HTTPSampler.use_keepalive", True)
            prop(node, "HTTPSampler.postBodyRaw", raw is not None)
            if web:
                prop(node, "HTTPSampler.domain", "127.0.0.1" if self.env == "local" else "visiontext-sigma.vercel.app")
                prop(node, "HTTPSampler.protocol", "http" if self.env == "local" else "https")
                prop(node, "HTTPSampler.port", property_ref("WEB_PORT", 4173) if self.env == "local" else "443")
            if upload:
                filename, mime = upload
                prop(node, "HTTPSampler.DO_MULTIPART_POST", True)
                prop(node, "HTTPSampler.BROWSER_COMPATIBLE_MULTIPART", True)
                file_args = SubElement(node, "elementProp", name="HTTPsampler.Files", elementType="HTTPFileArgs")
                files = SubElement(file_args, "collectionProp", name="HTTPFileArgs.files")
                file_node = SubElement(files, "elementProp", name="", elementType="HTTPFileArg")
                prop(file_node, "File.path", filename)
                prop(file_node, "File.paramname", "image")
                prop(file_node, "File.mimetype", mime)
            if request_headers:
                headers(tree, request_headers)
        if before:
            script(tree, "JSR223PreProcessor", "Preparar variables de la peticion", before)
        http_code, _ = component(tree, "ResponseAssertion", "AssertionGui", f"HTTP {expected}")
        tests = SubElement(http_code, "collectionProp", name="Asserion.test_strings")
        prop(tests, "0", expected)
        prop(http_code, "Assertion.test_field", "Assertion.response_code")
        prop(http_code, "Assertion.assume_success", expected >= 400)
        _prop(http_code, "intProp", "Assertion.test_type", "8")
        ceiling = BUDGETS[self.env][budget][0]
        duration, _ = component(tree, "DurationAssertion", "DurationAssertionGui", f"Respuesta en {ceiling} ms o menos")
        prop(duration, "DurationAssertion.duration", ceiling)
        if assertion:
            check(tree, expected, assertion)
        return tree

    def group(self, group):
        node, tree = component(
            self.tree, "ThreadGroup", "ThreadGroupGui", f"{group.flow} | {group.users} VU"
        )
        prop(node, "ThreadGroup.on_sample_error", "continue")
        main = SubElement(node, "elementProp", name="ThreadGroup.main_controller", elementType="LoopController",
                          guiclass="LoopControlPanel", testclass="LoopController", testname="Iteraciones")
        prop(main, "LoopController.continue_forever", False)
        prop(main, "LoopController.loops", group.loops)
        prop(node, "ThreadGroup.num_threads", group.users)
        prop(node, "ThreadGroup.ramp_time", group.ramp)
        prop(node, "ThreadGroup.scheduler", group.duration > 0)
        prop(node, "ThreadGroup.duration", group.duration or "")
        prop(node, "ThreadGroup.delay", "")
        if group.pause_ms:
            timer, _ = component(tree, "ConstantTimer", "ConstantTimerGui", "Pausa del usuario entre peticiones")
            prop(timer, "ConstantTimer.delay", group.pause_ms)
        if group.flow in ("texto", "imagen", "busquedas"):
            data, _ = component(tree, "CSVDataSet", "TestBeanGUI", "Datos del catalogo desde CSV")
            for name, value in {
                "filename": property_ref("QUERY_CSV", "../../data/consultas.csv"),
                "fileEncoding": "UTF-8", "variableNames": "", "ignoreFirstLine": False,
                "delimiter": ",", "quotedData": True, "recycle": True,
                "stopThread": False, "shareMode": "shareMode.group",
            }.items():
                prop(data, name, value)
        getattr(self, "flow_" + group.flow)(tree)

    @staticmethod
    def if_present(tree, key):
        node, inside = component(tree, "IfController", "IfControllerPanel", f"Si se obtuvo {key}")
        prop(node, "IfController.condition", "${__groovy(vars.get('" + key + "') != null)}")
        prop(node, "IfController.evaluateAll", False)
        prop(node, "IfController.useExpression", True)
        return inside

    def flow_inicio(self, tree):
        self.http(tree, "INI-01", "/", assertion=ROOT_CHECK)

    def flow_rutas(self, tree):
        self.http(tree, "API-01", "/", assertion=ROOT_CHECK)
        provider = "s3" if self.env == "local" else "google_drive"
        self.http(tree, "API-02", "/api/health", assertion=json_check(f"""
verify(body.status == 'healthy' && body.storage_provider == '{provider}' &&
       body.images_in_db > 0 && body.images_in_db == body.vectors_in_index,
       'Salud o conteos del indice incorrectos')
"""))
        self.http(tree, "API-03", "/openapi.json", assertion=json_check("""
verify(body.openapi?.startsWith('3.') && body.paths?.containsKey('/api/search/image'),
       'Falta la ruta esperada en el contrato OpenAPI')
"""))
        origin = "http://127.0.0.1:" + property_ref("WEB_PORT", 4173) if self.env == "local" else "https://visiontext-sigma.vercel.app"
        self.http(tree, "API-04", "/api/search/text", method="OPTIONS", request_headers={
            "Origin": origin, "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }, assertion=f"""
def origin = {'"http://127.0.0.1:" + props.getProperty("WEB_PORT", "4173")' if self.env == 'local' else "'https://visiontext-sigma.vercel.app'"}
verify(prev.getResponseHeaders().readLines().any {{ it.trim().equalsIgnoreCase('Access-Control-Allow-Origin: ' + origin) }},
       'No se encontro el origen autorizado en CORS')
""")
        self.http(tree, "ERR-01", "/api/search/text", method="POST", expected=422, raw='{"query":""}',
                  request_headers=JSON_HEADER, assertion=json_check("""
verify(body.detail instanceof List && body.detail.any { it.loc?.contains('query') },
       'Se esperaba un error para el campo query')
"""))
        self.http(tree, "ERR-02", "/api/search/image", method="POST", expected=400,
                  upload=(property_ref("INVALID_FILE", "../../data/no-imagen.txt"), "text/plain"),
                  assertion=json_check("verify(body.detail?.contains('debe ser una imagen'), 'Tipo MIME no rechazado')"))
        for key, route in (("ERR-03", "images"), ("ERR-04", "thumbnails")):
            self.http(tree, key, f"/api/{route}/00000000-0000-4000-8000-000000000000", expected=404,
                      assertion=NOT_FOUND)
        self.http(tree, "ERR-05", "/api/admin/images", expected=401, assertion=UNAUTHORIZED)
        self.http(tree, "ERR-06", "/api/upload", method="POST", expected=401, assertion=UNAUTHORIZED)
        if self.env == "render":
            self.http(tree, "APK-01", "/api/app/download", assertion="""
def data = prev.getResponseData()
verify(prev.getContentType().startsWith('application/vnd.android.package-archive') &&
       data.length > 4 && data[0] == 80 && data[1] == 75, 'APK MIME o firma ZIP incorrectos')
""")
        else:
            self.http(tree, "APK-01", "/api/app/download", expected=404, assertion=json_check(
                "verify(body.detail?.contains('Drive'), 'Se esperaba la respuesta de descarga sin Drive')"))

    def flow_busquedas(self, tree):
        self.flow_texto(tree)
        self.flow_imagen(tree)

    def flow_texto(self, tree):
        self.http(tree, "BUS-01", "/api/search/text", method="POST",
                  raw=variable("textBody"), request_headers=JSON_HEADER, before="""
vars.remove('textId')
vars.put('textBody', groovy.json.JsonOutput.toJson([
  query: vars.get('consulta'), limit: vars.get('limite').toInteger(),
  threshold: vars.get('umbral').toBigDecimal()
]))
""", assertion=search_check("textId", "item.filename.startsWith(vars.get('clase'))"))
        inside = self.if_present(tree, "textId")
        self.http(inside, "MED-01", "/api/thumbnails/" + variable("textId"), assertion=JPEG)
        self.http(inside, "MED-02", "/api/images/" + variable("textId"), assertion=JPEG)

    def flow_imagen(self, tree):
        self.http(tree, "BUS-02", "/api/search/image", method="POST", values={
            "limit": variable("limite"), "threshold": variable("umbral"),
        }, upload=(property_ref("DATASET", "../../../../VisionText-backend/dataset_final") + "/" + variable("archivo"), "image/jpeg"),
            before="vars.remove('imageId')",
            assertion=search_check("imageId", "item.filename == vars.get('archivo')"))
        inside = self.if_present(tree, "imageId")
        self.http(inside, "MED-03", "/api/thumbnails/" + variable("imageId"), assertion=JPEG)

    def login(self, tree, once=True):
        if once:
            _, tree = component(tree, "OnceOnlyController", "OnceOnlyControllerGui", "Abrir una sesion por usuario")
        self.http(tree, "ADM-01", "/api/admin/login", method="POST", values={
            "username": variable("adminUser"), "password": variable("adminPassword"),
        }, before="""
vars.remove('adminToken')
vars.put('adminUser', System.getenv('VT_JMETER_ADMIN_USER'))
vars.put('adminPassword', System.getenv('VT_JMETER_ADMIN_PASSWORD'))
""", assertion=json_check("""
if (verify(body.token_type == 'bearer' && body.access_token instanceof String &&
           (body.access_token ==~ /[A-Za-z0-9_-]+[.][A-Za-z0-9_-]+[.][A-Za-z0-9_-]+/), 'Respuesta de login sin JWT Bearer')) {
    vars.put('adminToken', body.access_token)
}
vars.remove('adminPassword')
"""))

    def flow_admin(self, tree):
        self.login(tree)
        inside = self.if_present(tree, "adminToken")
        for key, offset in (("ADM-02", 0), ("ADM-03", 5)):
            self.http(inside, key, "/api/admin/images", values={"limit": 5, "offset": offset},
                      request_headers=AUTH_HEADER, assertion=json_check(f"""
verify(body.limit == 5 && body.offset == {offset} && body.total > {offset} &&
       body.images instanceof List && body.images.size() == Math.min(5, body.total - {offset}) &&
       body.images.every {{ it.id == it.vector_id && it.filename instanceof String }},
       'Pagina de catalogo incorrecta')
"""))
        provider = "google_drive" if self.env == "render" else "s3"
        self.http(inside, "ADM-04", "/api/admin/storage", request_headers=AUTH_HEADER,
                  assertion=json_check(f"""
verify(body.status == 'connected' && body.provider == '{provider}' &&
       body.images_bucket_count > 0 && body.images_bucket_count == body.thumbnails_bucket_count,
       'Almacenamiento sin conexion o conteos inconsistentes')
"""))

    def flow_escritura(self, tree):
        self.login(tree)
        authenticated = self.if_present(tree, "adminToken")
        self.http(authenticated, "ESC-01", "/api/upload", method="POST", request_headers=AUTH_HEADER,
                  values={"description": "a photo of an African elephant"},
                  upload=(property_ref("DATASET", "../../../../VisionText-backend/dataset_final") + "/african_elephant_african_elephant-0005.jpg", "image/jpeg"),
                  before="vars.remove('ownedId')",
                  assertion=json_check("""
if (validId(body.image_id) && body.filename == 'african_elephant_african_elephant-0005.jpg') {
    vars.put('ownedId', body.image_id)
}
verify(vars.get('ownedId') && body.success == true && body.status == 'completed' &&
       body.similarity_score instanceof Number && body.similarity_score >= 0.2, 'No se completo la subida de prueba')
"""))
        inside = self.if_present(authenticated, "ownedId")
        self.http(inside, "ESC-02", "/api/images/" + variable("ownedId"), assertion=JPEG)
        self.http(inside, "ESC-03", "/api/thumbnails/" + variable("ownedId"), assertion=JPEG)
        self.http(inside, "ESC-04", "/api/admin/images/" + variable("ownedId"), method="DELETE",
                  request_headers=AUTH_HEADER, assertion=json_check("""
verify(body.success == true && body.deleted_from?.containsAll(['postgresql','faiss','minio']),
       'El borrado no confirmo todos los servicios')
"""))
        self.http(inside, "ESC-05", "/api/images/" + variable("ownedId"), expected=404, assertion=NOT_FOUND)

    def flow_web(self, tree):
        self.http(tree, "WEB-01", "/", web=True, before="vars.remove('jsPath'); vars.remove('cssPath')", assertion="""
def html = prev.getResponseDataAsString()
def modules = (html =~ /(?i)<script\\b[^>]*\\bsrc=["'](\\/assets\\/[^"']+\\.js)["']/)
def styles = (html =~ /(?i)<link\\b[^>]*\\bhref=["'](\\/assets\\/[^"']+\\.css)["']/)
if (verify(prev.getContentType().contains('text/html') && html.contains('VisionText') &&
           modules.find() && styles.find(), 'HTML o rutas de recursos de VisionText incorrectos')) {
    vars.put('jsPath', modules.group(1))
    vars.put('cssPath', styles.group(1))
}
""")
        inside = self.if_present(tree, "jsPath")
        self.http(inside, "WEB-02", variable("jsPath"), web=True, assertion="""
verify(prev.getContentType().contains('javascript') && prev.getResponseData().length > 0,
       'JavaScript ausente o de tipo incorrecto')
""")
        self.http(inside, "WEB-03", variable("cssPath"), web=True, assertion="""
verify(prev.getContentType().contains('text/css') && prev.getResponseData().length > 0,
       'CSS ausente o de tipo incorrecto')
""")


def verified_admin_request(path, values, method):
    """The authenticated cloud sampler checks both the TLS chain and the hostname."""
    from urllib.parse import urlencode

    login = method == "POST"
    target = "https://visiontext-backend.onrender.com" + path
    if values and not login:
        target += "?" + urlencode(values)
    prepare = """
def encode = { value -> java.net.URLEncoder.encode(value, java.nio.charset.StandardCharsets.UTF_8) }
def body = 'username=' + encode(vars.get('adminUser')) + '&password=' + encode(vars.get('adminPassword'))
request.header('Content-Type', 'application/x-www-form-urlencoded')
request.POST(java.net.http.HttpRequest.BodyPublishers.ofString(body))
SampleResult.setSentBytes(body.getBytes(java.nio.charset.StandardCharsets.UTF_8).length)
vars.remove('adminPassword')
""" if login else """
request.header('Authorization', 'Bearer ' + vars.get('adminToken'))
request.GET()
"""
    return f"""
try {{
    def client = vars.getObject('verifiedRenderClient')
    if (client == null) {{
        def tls = javax.net.ssl.SSLContext.getInstance('TLS')
        tls.init(null, null, null)
        def settings = new javax.net.ssl.SSLParameters()
        settings.setEndpointIdentificationAlgorithm('HTTPS')
        client = java.net.http.HttpClient.newBuilder().sslContext(tls).sslParameters(settings)
            .connectTimeout(java.time.Duration.ofSeconds(12))
            .followRedirects(java.net.http.HttpClient.Redirect.NEVER).build()
        vars.putObject('verifiedRenderClient', client)
    }}
    def request = java.net.http.HttpRequest.newBuilder(java.net.URI.create('{target}'))
        .timeout(java.time.Duration.ofSeconds(65))
    {prepare.strip()}
    def handler = {{ info ->
        SampleResult.latencyEnd()
        java.net.http.HttpResponse.BodySubscribers.ofByteArray()
    }} as java.net.http.HttpResponse.BodyHandler
    def response = client.send(request.build(), handler)
    def status = response.statusCode()
    SampleResult.setResponseCode(Integer.toString(status))
    SampleResult.setResponseMessage('HTTP ' + status)
    SampleResult.setContentType(response.headers().firstValue('Content-Type').orElse(''))
    SampleResult.setDataType('text')
    SampleResult.setResponseData(response.body())
    SampleResult.setSuccessful(status == 200)
}} catch (Exception exception) {{
    SampleResult.setResponseCode('TRANSPORTE')
    SampleResult.setResponseMessage(exception.getClass().getSimpleName())
    SampleResult.setSuccessful(false)
}}
return null
"""


def json_check(body):
    return "def body = new groovy.json.JsonSlurper().parseText(prev.getResponseDataAsString())\n" + VALID_ID + body


def search_check(target, predicate):
    return json_check(f"""
def rows = body.results
if (verify(rows instanceof List && rows.size() > 0 && rows.size() <= vars.get('limite').toInteger() &&
    rows.size() == body.total_count && body.query_time instanceof Number && body.query_time >= 0 &&
    rows.every {{ validId(it.id) && it.filename instanceof String && it.similarity_score instanceof Number }} &&
    rows.collect {{ it.id }}.unique().size() == rows.size(), 'Esquema de busqueda, conteos o IDs incorrectos')) {{
    def item = rows.find {{ item -> {predicate} }}
    if (verify(item != null, 'La consulta no recupero una coincidencia esperada del CSV')) {{
        vars.put('{target}', item.id)
    }}
}}
""")


JSON_HEADER = {"Content-Type": "application/json"}
AUTH_HEADER = {"Authorization": "Bearer " + variable("adminToken")}
VALID_ID = "def validId = { value -> value instanceof String && value ==~ /[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}/ }\n"
ROOT_CHECK = json_check("verify(body.status == 'running' && body.message == 'VisionText Backend API', 'Raiz de VisionText incorrecta')")
NOT_FOUND = json_check("verify(body.detail == 'Imagen no encontrada', 'Detalle HTTP 404 incorrecto')")
UNAUTHORIZED = json_check("verify(body.detail == 'No autorizado', 'Detalle HTTP 401 incorrecto')")
JPEG = """
def data = prev.getResponseData()
verify(prev.getContentType().startsWith('image/jpeg') && data.length > 4 &&
       (data[0] & 255) == 255 && (data[1] & 255) == 216, 'JPEG ausente o invalido')
"""


def main():
    for env, profiles in PROFILES.items():
        folder = ROOT / "plans" / env
        folder.mkdir(parents=True, exist_ok=True)
        for profile, groups in profiles.items():
            plan = Plan(env, profile)
            for group in groups:
                plan.group(group)
            indent(plan.root)
            ElementTree(plan.root).write(folder / f"{profile}.jmx", encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
