function fn() {
  var env = function(name) {
    var value = java.lang.System.getenv(name);
    return value == null ? '' : String(value);
  };
  function origin(value, name, loopbackOnly) {
    var local = /^http:\/\/(?:127\.0\.0\.1|localhost)(?::\d+)?$/;
    var secure = /^https:\/\/[a-z0-9.-]+(?::\d+)?$/i;
    var trimmed = value.replace(/\/$/, '');
    if (!local.test(trimmed) && (loopbackOnly || !secure.test(trimmed))) {
      throw new Error(name + ' debe ser un origen válido' + (loopbackOnly ? ' en localhost' : ' HTTPS o local'));
    }
    return trimmed;
  }

  var profile = karate.env || 'publico';
  var isLocal = profile === 'local' || profile === 'limite-login';
  var defaultUrl = isLocal ? 'http://127.0.0.1:8000' : 'https://visiontext-backend.onrender.com';
  var baseUrl = origin(env('VT_KARATE_URL') || defaultUrl, 'VT_KARATE_URL', isLocal);
  var assetOrigin = origin(env('VT_KARATE_ASSET_ORIGIN') || baseUrl, 'VT_KARATE_ASSET_ORIGIN', isLocal);

  if (isLocal && (!env('VT_KARATE_ADMIN_USER') || !env('VT_KARATE_ADMIN_PASSWORD'))) {
    throw new Error('Define VT_KARATE_ADMIN_USER y VT_KARATE_ADMIN_PASSWORD para el backend local de pruebas');
  }
  if (isLocal && env('VT_KARATE_LOCAL_ISOLATED') !== '1') {
    throw new Error('Usa una instancia local aislada y confirma con VT_KARATE_LOCAL_ISOLATED=1');
  }
  var loginAttempts = Number(env('VT_KARATE_LOGIN_ATTEMPTS') || 3);
  var loginWindowSeconds = Number(env('VT_KARATE_LOGIN_WINDOW_SECONDS') || 8);
  if (profile === 'limite-login' && (
      !Number.isInteger(loginAttempts) || loginAttempts < 2 || loginAttempts > 5 ||
      !Number.isInteger(loginWindowSeconds) || loginWindowSeconds < 4 || loginWindowSeconds > 15)) {
    throw new Error('Usa de 2 a 5 intentos y una ventana de 4 a 15 segundos en la instancia aislada');
  }

  var limits = isLocal ?
      { start: 10000, fast: 5000, inference: 15000, transfer: 15000, upload: 25000 } :
      { start: 155000, fast: 15000, inference: 40000, transfer: 40000, upload: 0 };

  karate.configure('connectTimeout', 12000);
  karate.configure('readTimeout', isLocal ? 30000 : 170000);
  karate.configure('followRedirects', false);
  karate.configure('httpRetryEnabled', false);
  karate.configure('logModifier', new (Java.type('pe.visiontext.qa.RedactHttp'))());
  karate.configure('report', { showLog: true, showAllSteps: true });

  return {
    profile: profile,
    baseUrl: baseUrl,
    assetOrigin: assetOrigin,
    corsOrigin: env('VT_KARATE_CORS_ORIGIN') || 'http://127.0.0.1:5173',
    expectedProvider: isLocal ? 's3' : 'google_drive',
    limits: limits,
    adminUser: isLocal ? env('VT_KARATE_ADMIN_USER') : '',
    adminPassword: isLocal ? env('VT_KARATE_ADMIN_PASSWORD') : '',
    loginAttempts: loginAttempts,
    loginWindowSeconds: loginWindowSeconds,
    positiveInt: function(value) { return Number.isInteger(value) && value > 0; },
    nonnegativeInt: function(value) { return Number.isInteger(value) && value >= 0; },
    nullableText: function(value) { return value === null || typeof value === 'string'; },
    boundedScore: function(value) { return Number.isFinite(value) && value >= -1.000001 && value <= 1.000001; },
    newId: function() { return Java.type('java.util.UUID').randomUUID().toString(); },
    newFixtureName: function() {
      var UUID = Java.type('java.util.UUID');
      var BigInteger = Java.type('java.math.BigInteger');
      var hex = UUID.randomUUID().toString().replace(/-/g, '');
      // Los dígitos conservan el UUID sin formar palabras del filtro de contenido.
      return 'karate-' + new BigInteger(hex, 16).toString() + '.jpg';
    }
  };
}
