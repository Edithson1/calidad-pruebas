@ignore
Feature: Leer la salud y los conteos de PostgreSQL y FAISS

  Scenario:
    Given url baseUrl
    And path 'api', 'health'
    When method get
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def healthSchema = read('file:schemas/service-health.json')
    And match response == healthSchema
    And match response.images_in_db == response.vectors_in_index
    * def health = response
