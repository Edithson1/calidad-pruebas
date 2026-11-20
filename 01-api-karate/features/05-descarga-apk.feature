Feature: Contrato de descarga pública de la aplicación Android

  Background:
    * url baseUrl
    * path 'api', 'app', 'download'

  @publico
  Scenario: APK-01 El despliegue entrega una APK de VisionText con los encabezados esperados
    When method get
    Then status 200
    And match header Content-Type == 'application/vnd.android.package-archive'
    And match header Content-Disposition == 'attachment; filename="VisionText.apk"'
    And match header Cache-Control == 'no-store'
    And match header X-Content-Type-Options == 'nosniff'
    And assert responseTime <= limits.transfer
    * def BinaryChecks = Java.type('pe.visiontext.qa.BinaryChecks')
    And assert BinaryChecks.containsApkEntries(responseBytes)

  @local
  Scenario: APK-02 El ambiente con almacenamiento S3 responde que la descarga requiere Drive
    When method get
    Then status 404
    And match header Content-Type contains 'application/json'
    And match response == { detail: 'La descarga de Android requiere el almacenamiento de Drive.' }
    And assert responseTime <= limits.fast
