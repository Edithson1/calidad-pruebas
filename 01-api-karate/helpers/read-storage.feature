@ignore
Feature: Leer el estado y los conteos de objetos del S3 de pruebas

  Scenario:
    Given url baseUrl
    And path 'api', 'admin', 'storage'
    And header Authorization = auth
    When method get
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def storageSchema = read('file:schemas/storage-s3.json')
    And match response == storageSchema
    And match response.buckets contains ['visiontext-images', 'visiontext-thumbnails']
    * def storage = response
