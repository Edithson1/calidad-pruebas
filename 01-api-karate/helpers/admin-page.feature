@ignore
Feature: Consultar una página de administración y validar todos sus registros

  Scenario:
    * configure matchEachEmptyAllowed = true
    Given url baseUrl
    And path 'api', 'admin', 'images'
    And header Authorization = auth
    And param limit = pageSize
    And param offset = pageOffset
    When method get
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def adminItem = read('file:schemas/admin-item.json')
    * def pageSchema = read('file:schemas/admin-page.json')
    And match response == pageSchema
    And match response.limit == pageSize
    And match response.offset == pageOffset
    And assert response.images.length === Math.min(pageSize, Math.max(0, response.total - pageOffset))
    * def ids = karate.map(response.images, function(img){ return img.id })
    And assert new Set(ids).size === ids.length
    And assert response.images.every(img => img.vector_id === img.id && img.thumbnail_url === assetOrigin + '/api/thumbnails/' + img.id)
    * def page = response
