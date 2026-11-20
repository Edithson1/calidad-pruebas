@ignore
Feature: Descargar y comprobar un JPEG del catálogo

  Scenario:
    Given url baseUrl
    And path 'api', resource, imageId
    When method get
    Then status 200
    And match header Content-Type == 'image/jpeg'
    And match header Cache-Control contains 'max-age=86400'
    And assert responseTime <= limits.transfer
    * def BinaryChecks = Java.type('pe.visiontext.qa.BinaryChecks')
    * def dimensions = BinaryChecks.jpegDimensions(responseBytes)
    * match dimensions == { width: '#number? positiveInt(_)', height: '#number? positiveInt(_)' }
