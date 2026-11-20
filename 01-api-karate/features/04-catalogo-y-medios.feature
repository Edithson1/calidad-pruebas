Feature: Catálogo público, originales y miniaturas

  Background:
    * url baseUrl

  @publico
  Scenario: CAT-01 El catálogo desplegado devuelve elefantes para African elephant y permite descargar original y miniatura
    * def limit = 5
    * def threshold = 0.18
    Given path 'api', 'search', 'text'
    And request { query: 'African elephant', limit: '#(limit)', threshold: '#(threshold)' }
    When method post
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.inference
    * def checked = call read('file:helpers/check-search.feature') { payload: '#(response)', requestedLimit: '#(limit)', minimumScore: '#(threshold)' }
    * def elephants = karate.filter(response.results, function(row){ return row.filename.startsWith('african_elephant_') })
    * assert elephants.length > 0
    * def selected = elephants[0]
    * def original = call read('file:helpers/download-jpeg.feature') { resource: 'images', imageId: '#(selected.id)' }
    * match original.dimensions == { width: '#(selected.metadata.width)', height: '#(selected.metadata.height)' }
    * def thumbnail = call read('file:helpers/download-jpeg.feature') { resource: 'thumbnails', imageId: '#(selected.id)' }
    * assert Math.max(thumbnail.dimensions.width, thumbnail.dimensions.height) <= 256
    * assert thumbnail.dimensions.width <= original.dimensions.width && thumbnail.dimensions.height <= original.dimensions.height

  @publico
  Scenario: CAT-02 Una consulta por JPEG recupera el mismo archivo del dataset con alta similitud
    * def limit = 5
    * def threshold = 0.65
    Given path 'api', 'search', 'image'
    And multipart file image = { read: 'file:data/elefante.jpg', filename: 'consulta-elefante.jpg', contentType: 'image/jpeg' }
    And multipart field limit = limit
    And multipart field threshold = threshold
    When method post
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.inference
    * def checked = call read('file:helpers/check-search.feature') { payload: '#(response)', requestedLimit: '#(limit)', minimumScore: '#(threshold)' }
    * def sameImage = karate.filter(response.results, function(row){ return row.filename === 'african_elephant_african_elephant-0005.jpg' })
    * assert sameImage.length === 1
    * assert sameImage[0].similarity_score >= 0.95

  @publico
  Scenario: CAT-05 El umbral máximo devuelve una colección vacía con un esquema válido
    Given path 'api', 'search', 'text'
    And request { query: 'African elephant', limit: 100, threshold: 1 }
    When method post
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.inference
    * def checked = call read('file:helpers/check-search.feature') { payload: '#(response)', requestedLimit: 100, minimumScore: 1 }
    And match response.results == []
    And match response.total_count == 0

  @comun
  Scenario Outline: <code> Devuelve 404 para un ID inexistente en <resource>
    * def missingId = newId()
    Given path 'api', resource, missingId
    When method get
    Then status 404
    And match header Content-Type contains 'application/json'
    And match response == { detail: 'Imagen no encontrada' }
    And assert responseTime <= limits.fast

    Examples:
      | code   | resource   |
      | CAT-03 | images     |
      | CAT-04 | thumbnails |
