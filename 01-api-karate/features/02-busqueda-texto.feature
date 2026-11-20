@comun
Feature: Búsqueda por texto y validación del contrato JSON

  Background:
    * url baseUrl
    * path 'api', 'search', 'text'

  Scenario: TXT-01 Consulta válida con límite de un resultado
    * def limit = 1
    * def threshold = 0
    Given request { query: 'African elephant', limit: '#(limit)', threshold: '#(threshold)' }
    When method post
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.inference
    * def checked = call read('file:helpers/check-search.feature') { payload: '#(response)', requestedLimit: '#(limit)', minimumScore: '#(threshold)' }

  Scenario Outline: <code> FastAPI rechaza <case>
    * def requestBody = body
    Given request requestBody
    When method post
    Then status 422
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def checked = call read('file:helpers/check-validation.feature') { payload: '#(response)', location: ['body', '#(field)'], errorType: '#(error)' }

    Examples:
      | read('file:data/text-invalid.json') |

  Scenario: TXT-10 Un JSON mal formado retorna un error de parseo
    Given header Content-Type = 'application/json'
    And request '{"query":'
    When method post
    Then status 422
    And match header Content-Type contains 'application/json'
    * def validationIssue = read('file:schemas/validation-issue.json')
    And match response == { detail: '#[] validationIssue' }
    And match response.detail[0].type == 'json_invalid'
    And match response.detail[0].loc == ['body', '#number']
    And assert responseTime <= limits.fast
