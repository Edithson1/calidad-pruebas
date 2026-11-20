@comun
Feature: Contrato público y estado de VisionText

  Background:
    * url baseUrl

  Scenario: SRV-01 La raíz identifica la API y sus capacidades
    Given path '/'
    When method get
    Then status 200
    And match header Content-Type contains 'application/json'
    And match response == { message: 'VisionText Backend API', status: 'running', features: '#[3] #string' }
    And match response.features contains only ['Text-to-Image search', 'Image-to-Image search', 'Image-Text similarity validation']
    And assert responseTime <= limits.start

  Scenario: SRV-02 Salud comprueba dependencias y consistencia del índice
    Given path 'api', 'health'
    When method get
    Then status 200
    And match header Content-Type contains 'application/json'
    * def healthSchema = read('file:schemas/service-health.json')
    And match response == healthSchema
    And match response.images_in_db == response.vectors_in_index
    And assert expectedProvider !== 's3' || response.services.minio === 'connected'
    And assert responseTime <= limits.start

  Scenario: SRV-03 El OpenAPI documenta los endpoints y métodos de la suite
    Given path 'openapi.json'
    When method get
    Then status 200
    And match header Content-Type contains 'application/json'
    And match response.openapi == '#regex 3\\.[0-9]+\\.[0-9]+'
    And match response.info contains { title: 'VisionText Backend', version: '#string' }
    * table expectedRoutes
      | route                        | verb     |
      | '/'                          | 'get'    |
      | '/api/health'                | 'get'    |
      | '/api/search/text'           | 'post'   |
      | '/api/search/image'          | 'post'   |
      | '/api/images/{image_id}'     | 'get'    |
      | '/api/thumbnails/{image_id}' | 'get'    |
      | '/api/app/download'          | 'get'    |
      | '/api/admin/login'           | 'post'   |
      | '/api/admin/images'          | 'get'    |
      | '/api/admin/storage'         | 'get'    |
      | '/api/upload'                | 'post'   |
      | '/api/admin/images/{image_id}' | 'delete' |
    * def allPaths = response.paths
    And assert expectedRoutes.every(r => allPaths[r.route] && allPaths[r.route][r.verb] && typeof allPaths[r.route][r.verb].responses === 'object')
    And match response.components.schemas.TextSearchRequest.required contains 'query'
    And match response.paths['/api/upload'].post.responses contains { '200': '#object', '422': '#object' }
    And match response.paths['/api/app/download'].get.responses contains { '200': '#object', '404': '#object', '503': '#object' }
    And assert responseTime <= limits.fast

  Scenario: SRV-04 CORS permite el origen configurado para VisionText
    Given path 'api', 'search', 'text'
    And header Origin = corsOrigin
    And header Access-Control-Request-Method = 'POST'
    And header Access-Control-Request-Headers = 'content-type,authorization'
    When method options
    Then status 200
    And match header Access-Control-Allow-Origin == corsOrigin
    And match header Access-Control-Allow-Methods contains 'POST'
    And match header Access-Control-Allow-Headers contains 'content-type,authorization'
    And assert responseTime <= limits.fast

  Scenario: SRV-05 CORS rechaza un origen ajeno
    Given path 'api', 'search', 'text'
    And header Origin = 'https://visiontext-qa.invalid'
    And header Access-Control-Request-Method = 'POST'
    When method options
    Then status 400
    And match karate.lowerCase(responseHeaders) !contains { 'access-control-allow-origin': '#present' }
    And match response contains 'Disallowed CORS origin'
    And assert responseTime <= limits.fast
