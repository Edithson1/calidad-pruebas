@comun
Feature: Búsqueda multipart por imagen y validación de archivos

  Background:
    * url baseUrl
    * path 'api', 'search', 'image'
    * def sample = read('file:data/elefante.jpg')

  Scenario: IMG-01 Procesa un JPEG válido y aplica el límite y el umbral
    * def limit = 2
    * def threshold = 0.65
    Given multipart file image = { value: '#(sample)', filename: 'consulta-elefante.jpg', contentType: 'image/jpeg' }
    And multipart field limit = limit
    And multipart field threshold = threshold
    When method post
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.inference
    * def checked = call read('file:helpers/check-search.feature') { payload: '#(response)', requestedLimit: '#(limit)', minimumScore: '#(threshold)' }

  Scenario: IMG-02 Rechaza un archivo de texto
    Given multipart file image = { value: 'un archivo de texto', filename: 'invalid.txt', contentType: 'text/plain' }
    When method post
    Then status 400
    And match header Content-Type contains 'application/json'
    And match response == { detail: 'El archivo debe ser una imagen' }
    And assert responseTime <= limits.fast

  Scenario: IMG-03 Rechaza bytes inválidos aun si la parte declara image/jpeg
    Given multipart file image = { value: 'no contiene un JPEG', filename: 'invalid.jpg', contentType: 'image/jpeg' }
    When method post
    Then status 400
    And match header Content-Type contains 'application/json'
    And match response == { detail: 'Formato de imagen no soportado' }
    And assert responseTime <= limits.fast

  Scenario: IMG-04 Rechaza una imagen de 2048 por 2048 que supera los cuatro millones de píxeles
    Given multipart file image = { read: 'file:data/sobre-limite.png', filename: 'sobre-limite.png', contentType: 'image/png' }
    When method post
    Then status 413
    And match header Content-Type contains 'application/json'
    And match response == { detail: '#regex La imagen supera el límite de [0-9]+ píxeles' }
    And assert responseTime <= limits.fast

  Scenario: IMG-05 Devuelve 422 si falta la parte image
    Given multipart field limit = '2'
    When method post
    Then status 422
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def checked = call read('file:helpers/check-validation.feature') { payload: '#(response)', location: ['body', 'image'], errorType: 'missing' }

  Scenario Outline: <code> Rechaza <field>=<value> en el formulario
    * def invalidForm = {}
    * eval invalidForm[field] = value
    Given multipart file image = { value: '#(sample)', filename: 'consulta-elefante.jpg', contentType: 'image/jpeg' }
    And multipart fields invalidForm
    When method post
    Then status 422
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def checked = call read('file:helpers/check-validation.feature') { payload: '#(response)', location: ['body', '#(field)'], errorType: '#(error)' }

    Examples:
      | code   | field     | value | error              |
      | IMG-06 | limit     | 0     | greater_than_equal |
      | IMG-07 | limit     | 101   | less_than_equal    |
      | IMG-08 | threshold | -0.1  | greater_than_equal |
      | IMG-09 | threshold | 1.1   | less_than_equal    |
